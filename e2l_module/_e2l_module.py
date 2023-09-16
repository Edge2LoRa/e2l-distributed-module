import os
import base64
import time
from Crypto.PublicKey import ECC
import logging
import grpc
from e2gw_rpc_client import edge2gateway_pb2_grpc, EdPubInfo
from .__private__ import demo_pb2_grpc, SendStatistics, SendLogMessage
import json
import hashlib
from threading import Thread

DEBUG = os.getenv('DEBUG', False)
DEBUG = True if DEBUG == '1' else False
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)

LOG_ED=1
LOG_GW=2
LOG_DM=3


class E2LoRaModule():
    """
    This class is handle the Edge2LoRa Protocol.
    """
    def __init__(self, dashboard_rpc_endpoint):
        # Generate ephimeral ecc private/public key pair
        self.ephimeral_private_key = ECC.generate(curve='P-256')
        self.ephimeral_public_key = self.ephimeral_private_key.public_key()
        self.ephimeral_public_key_bytes_compressed = self.ephimeral_public_key.export_key(format='SEC1')
        # Init active directory
        self.active_directory = {
            "e2gws": {},
            "e2eds": {}
        }
        # Statistics collection utils
        self.statistics = {
            "rx_legacy_frames": 0,
            "rx_e2l_frames": 0,
            "gateways": {},
            "rx_ns": 0,
            "tx_ns": 0
        }
        self.e2gw_ids = []
        self.e2ed_ids = []
        # Init RPC Client
        channel = grpc.insecure_channel(dashboard_rpc_endpoint)
        try:
            self.dashboard_rpc_stub = demo_pb2_grpc.GRPCDemoStub(channel)
            # self.dashboard_rpc_stub = None
        except:
            self.dashboard_rpc_stub = None
        
        # LOG UTILS
        self.gw_log = None
        # LOG
        self._send_log(LOG_ED, "E2LoRa Module started")

    '''
        @brief: this function send log to the dashboard
        @param type: log type <LOG_ED|LOG_GW|LOG_DM>
        @param message: log message
    '''
    def _send_log(self, type, message):
        if self.dashboard_rpc_stub is None:
            return
        request = SendLogMessage(
            client_id = 1,
            message_data = "",
            key_agreement_log_message_node_id = type,
            key_agreement_message_log = message,
            key_agreement_process_time = 0,
        )
        self.dashboard_rpc_stub.SimpleMethodsLogMessage(request)

    def _get_stats(self):
        for i in range(10):
            gw_1_info = {}
            gw_2_info = {}
            if(len(self.e2gw_ids) > 0):
                gw_1_info = self.statistics["gateways"][self.e2gw_ids[0]]
            if(len(self.e2gw_ids) > 1):
                gw_2_info = self.statistics["gateways"][self.e2ed_ids[1]]
            request = SendStatistics(
                client_id = 1,
                message_data = "",
                gw_1_received_frame_num = gw_1_info.get("rx", 0),
                gw_1_transmitted_frame_num = gw_1_info.get("tx", 0),
                gw_2_received_frame_num = gw_2_info.get("rx", 0),
                gw_2_transmitted_frame_num = gw_2_info.get("tx", 0),
                ns_received_frame_frame_num = self.statistics.get("rx_ns", 0),
                ns_transmitted_frame_frame_num = self.statistics.get("tx_ns", 0),
                module_received_frame_frame_num = self.statistics.get("rx_legacy_frames", 0) + self.statistics.get("rx_e2l_frames", 0),
                aggregation_function_result = self.statistics.get("rx_e2l_frames", 0)
            )
            yield request
            time.sleep(5)

    def _update_dashboard(self):
        while(True):
            time.sleep(5)
            log.info("Sending statistics to dashboard")
            self.dashboard_rpc_stub.ClientStreamingMethodStatistics(self._get_stats())


    """
        @brief: This function is used to send a downlink frame to a ED.
        @para
    """
    def _send_downlink_frame(self, mqtt_client, base64_message, dev_id, priority = "HIGHEST"):
        downlink_frame = {
            "downlinks": [
                {
                    "f_port": 3,
                    "frm_payload": base64_message,
                    "priority": priority
                }
            ]
        }
        downlink_frame_str = json.dumps(downlink_frame)

        base_topic = os.getenv('MQTT_BASE_TOPIC')
        topic = f'{base_topic}{dev_id}/down/replace'
        
        res = mqtt_client.publish_to_topic(
            topic = topic,
            message = downlink_frame_str
        )

        return downlink_frame
    """
        @brief  This funciont handle new public key info received by a GW.
                It initialize a RPC client for each GW.
        @param gw_rpc_endpoint_address: The IP address of the Gateway.
        @param gw_rpc_endpoint_port: The port of the Gateway.
        @param gw_pub_key_bytes: The E2GW Public Key.
        @return: 0 is success, < 0 if failure.
        @error code:
            -1: Error 
    """
    def handle_gw_pub_info(self, gw_rpc_endpoint_address, gw_rpc_endpoint_port, gw_pub_key_compressed):
        # Retireve Info
        gw_pub_key = ECC.import_key(gw_pub_key_compressed, curve_name='P-256')
        g_as_gw_point = gw_pub_key.pointQ * self.ephimeral_private_key.d
        g_as_gw = ECC.construct(curve='P-256', point_x=g_as_gw_point.x, point_y=g_as_gw_point.y)

        # Init RPC Client
        channel = grpc.insecure_channel(f'{gw_rpc_endpoint_address}:{gw_rpc_endpoint_port}')
        stub = edge2gateway_pb2_grpc.Edge2GatewayStub(channel)

        self.active_directory["e2gws"][gw_rpc_endpoint_address] = {
            "gw_rpc_endpoint_address": gw_rpc_endpoint_address,
            "gw_rpc_endpoint_port": gw_rpc_endpoint_port,
            "gw_pub_key": gw_pub_key,
            "g_as_gw": g_as_gw,
            "e2gw_stub": stub
        }
        if self.statistics.get("gateways").get(gw_rpc_endpoint_address) is None:
            self.statistics["gateways"][gw_rpc_endpoint_address] = {
                "rx": 0,
                "tx": 0
            }
        if gw_rpc_endpoint_address not in self.e2gw_ids:
            self.e2gw_ids.append(gw_rpc_endpoint_address)
        if self.gw_log is None:
            self.gw_log = gw_rpc_endpoint_address
        log.info(f'E2GW {gw_rpc_endpoint_address} is added to active directory')
        if self.gw_log == gw_rpc_endpoint_address:
            self._send_log(LOG_GW, f'Ephimeral E2GW ECC key pair received')
        return 0

    """
        @brief  This function handle new public key info received by a ED.
                It complete the process of key agreement for the server.
        @param dev_eui: The Dev EUI.
        @param dev_addr: The Dev Addr.
        @param dev_pub_key_compressed: The Compressed Dev Public Key.
        @return: 0 is success, < 0 if failure.
        @error code:
            -1: Error 
    """
    def handle_edge_join_request(self, dev_id, dev_eui, dev_addr, dev_pub_key_compressed_base_64, mqtt_client):

        # Assign E2GW to E2ED and store informations
        e2gw = self.active_directory["e2gws"].get(list(self.active_directory["e2gws"].keys())[0])
        if e2gw is None:
            log.error("No E2GW found")
            return -1

        dev_obj = {
            "dev_id": dev_id,
            "dev_eui": dev_eui,
            "dev_addr": dev_addr,
            "e2gw": e2gw.get("gw_rpc_endpoint_address"),
        }
        # Get g_as_gw
        g_as_gw = e2gw.get("g_as_gw")
        # Schedule downlink to ed with g_as_gw
        # encode g_as_gw in base64
        g_as_gw_exported = g_as_gw.export_key(format="SEC1")
        g_as_gw_base_64 = base64.b64encode(g_as_gw_exported).decode('utf-8')
        _downlink_frame = self._send_downlink_frame(
            mqtt_client=mqtt_client,
            base64_message = g_as_gw_base_64, 
            dev_id = dev_id
            )

        # Generate g_as_ed
        # Decode base64
        dev_pub_key_compressed = base64.b64decode(dev_pub_key_compressed_base_64)
        dev_pub_key = ECC.import_key(dev_pub_key_compressed, curve_name='P-256')
        g_as_ed = dev_pub_key.pointQ * self.ephimeral_private_key.d
        g_as_ed_bytes = ECC.construct(curve='P-256', point_x=g_as_ed.x, point_y=g_as_ed.y).export_key(format="SEC1")
        
        ### Send g_as_ed to e2gw
        e2gw_rpc_stub = e2gw.get("e2gw_stub")
        ed_pub_info = EdPubInfo(dev_eui=dev_eui, dev_addr=dev_addr, g_as_ed=g_as_ed_bytes, dev_public_key = dev_pub_key_compressed)
        response = e2gw_rpc_stub.handle_ed_pub_info(ed_pub_info)
        g_gw_ed_bytes = response.g_gw_ed
        g_gw_ed = ECC.import_key(g_gw_ed_bytes, curve_name='P-256')
        edgeSKey_int = self.ephimeral_private_key.d * g_gw_ed.pointQ
        edgeSKey = edgeSKey_int.x.to_bytes()

        # Hash edgeSKey
        edgeSIntKey = b'\x00' + edgeSKey
        edgeSEncKey = b'\x01' + edgeSKey
        edgeSIntKey = hashlib.sha256(edgeSIntKey).digest()[:16]
        edgeSEncKey = hashlib.sha256(edgeSEncKey).digest()[:16]
        log.info(f'edgeSIntKey: {[x for x in edgeSIntKey]}')
        log.info(f'edgeSEncKey: {[x for x in edgeSEncKey]}')

        # Store device info
        dev_obj["edgeSIntKey"] = edgeSIntKey
        dev_obj["edgeSEncKey"] = edgeSEncKey
        self.active_directory["e2eds"][dev_eui] = dev_obj
        if dev_eui not in self.e2ed_ids:
            self.e2ed_ids.append(dev_eui)

        return 0
     
    def handle_edge_data_from_legacy(self, dev_id, dev_eui, dev_addr, frame_payload):
        log.info(f'Received Edge Frame from legacy route. Dev Addr: {dev_addr}');
        self.statistics["rx_ns"] = self.statistics["rx_ns"] + 1
        self.statistics["tx_ns"] = self.statistics["tx_ns"] + 1
        self.statistics["rx_e2l_frames"] = self.statistics["rx_e2l_frames"] + 1
        return 0
        
    def handle_legacy_data(self, dev_id, dev_eui, dev_addr, frame_payload):
        log.info(f'Received Legacy Frame from Legacy Route.');
        self.statistics["rx_ns"] = self.statistics["rx_ns"] + 1
        self.statistics["tx_ns"] = self.statistics["tx_ns"] + 1
        self.statistics["rx_legacy_frames"] = self.statistics["rx_legacy_frames"] + 1
        for i in range(len(self.e2gw_ids)):
            if self.statistics["gateways"].get(self.e2gw_ids[i]) is None:
                continue
            self.statistics["gateways"][self.e2gw_ids[i]]["rx"] = self.statistics["gateways"][self.e2gw_ids[i]].get("rx", 0) + 1
            self.statistics["gateways"][self.e2gw_ids[i]]["tx"] = self.statistics["gateways"][self.e2gw_ids[i]].get("tx", 0) + 1
        return 0

    
        self.e2l_module.handle_edge_data(
            gw_id = gw_id,
            dev_eui = dev_eui,
            dev_addr = dev_addr,
            aggregated_data = aggregated_data,
            delta_time = delta_time
        )
    def handle_edge_data(self, gw_id, dev_eui, dev_addr, aggregated_data, delta_time):
        log.info(f'Received Edge Frame from E2ED. Data: {aggregated_data} Dev Addr: {dev_addr}. Passyng from GW: {gw_id}');
        self.statistics["rx_e2l_frames"] = self.statistics["rx_e2l_frames"] + 1
        for i in range(len(self.e2gw_ids)):
            if self.statistics["gateways"].get(self.e2gw_ids[i]) is None:
                continue
            self.statistics["gateways"][self.e2gw_ids[i]]["rx"] = self.statistics["gateways"][self.e2gw_ids[i]].get("rx", 0) + 1
            if self.gw_ids[i] == gw_id:
                self.statistics["gateways"][self.e2gw_ids[i]]["tx"] = self.statistics["gateways"][self.e2gw_ids[i]].get("tx", 0) + 1


    def start_dashboard_update_loop(self):
        if self.dashboard_rpc_stub is None:
            return
        self.dashboard_update_loop = Thread(target=self._update_dashboard)
        self.dashboard_update_loop.start()