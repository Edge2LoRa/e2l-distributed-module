import os
import base64
import time
from Crypto.PublicKey import ECC
import logging
import grpc
from e2gw_rpc_client import edge2gateway_pb2_grpc, EdPubInfo, AggregationParams, E2LDeviceInfo , GwResponse
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

### LORAWAN PORTS
DEFAULT_APP_PORT=2
DEFAULT_E2L_JOIN_PORT=3
DEFAULT_E2L_APP_PORT=4
DEFAULT_E2L_COMMAND_PORT=5

# EDGE2LORA COMMAND
REJOIN_COMMAND = "REJOIN"

# LOG TYPE
LOG_GW1=1
LOG_GW2=2
LOG_ED=3

# AGGREGATION FUNCTION TYPE
AVG_ID=1
SUM_ID=2
MIN_ID=3
MAX_ID=4

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
        # MQTT CLIENT
        self.mqtt_client = None
        # Aggregation Utils
        self.aggregation_function = None
        self.window_size = None

    """
        @brief: this function send log to the dashboard
        @param type: log type <LOG_GW1|LOG_GW2|LOG_ED>
        @param message: log message
    """
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
        log.info(f'Sending log to dashboard: {type}\t{message}')
        response = self.dashboard_rpc_stub.SimpleMethodsLogMessage(request)
        log.info(response)

    """
        @brief  This function collect the stats and return a SendStatistics object
        @return The updated SendStatistics object
    """
    def _get_stats(self):
        for i in range(1):
            gw_1_info = {}
            gw_2_info = {}
            if(len(self.e2gw_ids) > 0):
                gw_1_info = self.statistics["gateways"][self.e2gw_ids[0]]
            if(len(self.e2gw_ids) > 1):
                gw_2_info = self.statistics["gateways"][self.e2gw_ids[1]]
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
            # time.sleep(5)

    """
        @brief: This function updated the paramenters according to the settings of the dashboard.
                It can trigger a change in the aggregation function and window size of the gateways, or
                change the E2GW for the E2EDs.
        @param ed_1_gw_selection: the gateway index to be used for the first E2ED
        @param ed_2_gw_selection: the gateway index to be used for the second E2ED
        @param ed_3_gw_selection: the gateway index to be used for the third E2ED
        @param aggregation_function: the aggregation function to be used for the gateways
        @param window_size: the window size to be used for the gateways
        @return: None
    """
    def _update_params(self, ed_1_gw_selection, ed_2_gw_selection, ed_3_gw_selection, aggregation_function, window_size):
        # UPDATE AGGREGATION PARAMETERS
        if self.window_size is None or self.aggregation_function is None or self.window_size != window_size or self.aggregation_function != aggregation_function:
            self.window_size = window_size
            self.aggregation_function = aggregation_function
            for e2gw_id in self.e2gw_ids:
                gw_stub = self.active_directory["e2gws"].get(e2gw_id).get("e2gw_stub")
                new_aggregation_params = AggregationParams(
                    aggregation_function = aggregation_function,
                    window_size = window_size
                )
                gw_stub.update_aggregation_params(new_aggregation_params)
        
        rejoin_command_base64 = base64.b64encode(REJOIN_COMMAND.encode('utf-8')).decode('utf-8')
        # UPDATE ED 1 GW SELECTION
        if len(self.e2gw_ids) >= ed_1_gw_selection and len(self.e2ed_ids) > 0:
            dev_eui = self.e2ed_ids[0]
            new_e2gw_id = self.e2gw_ids[ed_1_gw_selection - 1]
            e2ed_info = self.active_directory["e2eds"].get(dev_eui)
            if e2ed_info is not None:
                old_e2gw_id = e2ed_info.get("e2gw")
                if new_e2gw_id != old_e2gw_id:
                    self.active_directory["e2eds"][dev_eui]["e2gw"] = new_e2gw_id
                    dev_id = e2ed_info.get("dev_id")
                    self._send_downlink_frame(
                        base64_message = rejoin_command_base64,
                        dev_id = dev_id,
                        lorawan_port = DEFAULT_E2L_COMMAND_PORT,
                        priority = "HIGHEST"
                    )
                    old_e2gw_stub = self.active_directory["e2gws"].get(old_e2gw_id).get("e2gw_stub")
                    e2ed_data = old_e2gw_stub.remove_e2device(E2LDeviceInfo(
                        dev_eui = dev_eui,
                        dev_addr = e2ed_info.get("dev_addr"),
                    ))


                    
        # UPDATE ED 2 GW SELECTION
        if len(self.e2gw_ids) >= ed_2_gw_selection and len(self.e2ed_ids) > 1:
            dev_eui = self.e2ed_ids[1]
            new_e2gw_id = self.e2gw_ids[ed_2_gw_selection - 1]
            e2ed_info = self.active_directory["e2eds"].get(dev_eui)
            if e2ed_info is not None:
                old_e2gw_id = e2ed_info.get("e2gw")
                if new_e2gw_id != old_e2gw_id:
                    self.active_directory["e2eds"][dev_eui]["e2gw"] = new_e2gw_id
                    dev_id = e2ed_info.get("dev_id")
                    self._send_downlink_frame(
                        base64_message = rejoin_command_base64,
                        dev_id = dev_id,
                        lorawan_port = DEFAULT_E2L_COMMAND_PORT,
                        priority = "HIGHEST"
                    )
                    old_e2gw_stub = self.active_directory["e2gws"].get(old_e2gw_id).get("e2gw_stub")
                    e2ed_data = old_e2gw_stub.remove_e2device(E2LDeviceInfo(
                        dev_eui = dev_eui,
                        dev_addr = e2ed_info.get("dev_addr"),
                    ))
                    
        # UPDATE ED 3 GW SELECTION
        if len(self.e2gw_ids) >= ed_3_gw_selection and len(self.e2ed_ids) > 2:
            dev_eui = self.e2ed_ids[2]
            new_e2gw_id = self.e2gw_ids[ed_3_gw_selection - 1]
            e2ed_info = self.active_directory["e2eds"].get(dev_eui)
            if e2ed_info is not None:
                old_e2gw_id = e2ed_info.get("e2gw")
                if new_e2gw_id != old_e2gw_id:
                    self.active_directory["e2eds"][dev_eui]["e2gw"] = new_e2gw_id
                    dev_id = e2ed_info.get("dev_id")
                    self._send_downlink_frame(
                        base64_message = rejoin_command_base64,
                        dev_id = dev_id,
                        lorawan_port = DEFAULT_E2L_COMMAND_PORT,
                        priority = "HIGHEST"
                    )
                    old_e2gw_stub = self.active_directory["e2gws"].get(old_e2gw_id).get("e2gw_stub")
                    e2ed_data = old_e2gw_stub.remove_e2device(E2LDeviceInfo(
                        dev_eui = dev_eui,
                        dev_addr = e2ed_info.get("dev_addr"),
                    ))
                    
    """
        @brief  This function is used to periodically send the stats to the dashboard, and get the new settings.
        @return None
    """
    def _update_dashboard(self):
        while(True):
            time.sleep(5)
            log.info("Sending statistics to dashboard")
            response = self.dashboard_rpc_stub.ClientStreamingMethodStatistics(self._get_stats())
            ed_1_gw_selection = response.ed_1_gw_selection
            ed_2_gw_selection = response.ed_2_gw_selection
            ed_3_gw_selection = response.ed_3_gw_selection
            aggregation_function_str = response.process_function
            aggregation_function = AVG_ID
            if aggregation_function_str == "mean":
                aggregation_function = AVG_ID
            elif aggregation_function_str == "sum":
                aggregation_function = SUM_ID
            elif aggregation_function_str == "min":
                aggregation_function = MIN_ID
            elif aggregation_function_str == "max":
                aggregation_function = MAX_ID
            else:
                log.error("Unknown aggregation function. Setting to AVG.")
            window_size = response.process_window
            self._update_params(ed_1_gw_selection, ed_2_gw_selection, ed_3_gw_selection, aggregation_function, window_size)

    """
        @brief  This function is used to send a downlink frame to a ED.
        @param   base64_message: The frame payload to be sent encoded in base64.
        @param   dev_id: The device ID of the ED as in TTS.
        @param   lorawan_port: The port of the ED. (default: 3)
        @param   priority: The priority of the frame. (default: HIGHEST)
        @return   0 is success, < 0 if failure.
    """
    def _send_downlink_frame(self, base64_message, dev_id, lorawan_port = 3, priority = "HIGHEST"):
        downlink_frame = {
            "downlinks": [
                {
                    "f_port": lorawan_port,
                    "frm_payload": base64_message,
                    "priority": priority
                }
            ]
        }
        downlink_frame_str = json.dumps(downlink_frame)

        base_topic = os.getenv('MQTT_BASE_TOPIC')
        topic = f'{base_topic}{dev_id}/down/replace'
        
        res = self.mqtt_client.publish_to_topic(
            topic = topic,
            message = downlink_frame_str
        )

        return 0

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
        new_aggregation_params = AggregationParams(
            aggregation_function = self.aggregation_function,
            window_size = self.window_size
        )
        stub.update_aggregation_params(new_aggregation_params)

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
        log_type = None
        log_message = ''
        if gw_rpc_endpoint_address not in self.e2gw_ids:
            self.e2gw_ids.append(gw_rpc_endpoint_address)
            log_message = f'Added GW info in DM active directory'
        else: 
            log_message = f'Updated GW info in DM active directory'
        # SEND LOG
        index = self.e2gw_ids.index(gw_rpc_endpoint_address)
        log_type = None
        if index == 0:
            log_type = LOG_GW1
        elif index == 1:
            log_type = LOG_GW2
        else: 
            log_type = None
        if log_type is not None:
            self._send_log(type=log_type, message=log_message)
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
    def handle_edge_join_request(self, dev_id, dev_eui, dev_addr, dev_pub_key_compressed_base_64):
        # SEND LOG
        if len(self.e2ed_ids) < 1 or (dev_eui in self.e2ed_ids and self.e2ed_ids.index(dev_eui) == 0):
            self._send_log(type=LOG_ED, message=f'Starting Edge Join')

        dev_obj = None
        e2gw = None
        # Check if ED is already registered
        if self.active_directory["e2eds"].get(dev_eui) is None:
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
        else:
            dev_obj = self.active_directory["e2eds"].get(dev_eui)
            e2gw = self.active_directory["e2gws"].get(dev_obj.get("e2gw"))
            if e2gw is None:
                log.error("No E2GW found")
                return -1
        # SEND LOG
        if len(self.e2ed_ids) < 1 or  (dev_eui in self.e2ed_ids and self.e2ed_ids.index(dev_eui) == 0):
            self._send_log(type=LOG_ED, message=f'Send EdgeJoinRequest')
        # Get g_as_gw
        g_as_gw = e2gw.get("g_as_gw")
        # Schedule downlink to ed with g_as_gw
        # encode g_as_gw in base64
        g_as_gw_exported = g_as_gw.export_key(format="SEC1")
        g_as_gw_base_64 = base64.b64encode(g_as_gw_exported).decode('utf-8')
        _downlink_frame = self._send_downlink_frame(
            base64_message = g_as_gw_base_64, 
            dev_id = dev_id
            )
        # SEND LOG
        if len(self.e2ed_ids) < 1 or  (dev_eui in self.e2ed_ids and self.e2ed_ids.index(dev_eui) == 0):
            self._send_log(type=LOG_ED, message=f'Received EdgeAcceptRequest')

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
        # SEND LOG
        index = self.e2gw_ids.index(e2gw.get("gw_rpc_endpoint_address"))
        log_type = None
        if index == 0:
            log_type = LOG_GW1
        elif index == 1:
            log_type = LOG_GW2
        else: 
            log_type = None
        if log_type is not None:
            self._send_log(type=log_type, message=f'Received Device {dev_addr} Public Info')

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
        
        # SEND LOG
        if self.e2ed_ids.index(dev_eui) == 0:
            self._send_log(type=LOG_ED, message=f'Edge Join Completed')
        if log_type is not None:
            self._send_log(type=log_type, message=f'Edge Join Completed')

        return 0

    """
        @brief  This function handle new edge frame received by an ED, passing by the legacy route.
        @param dev_id: The Dev ID as in TTS.
        @param dev_eui: The Dev EUI.
        @param dev_addr: The Dev Addr.
        @param frame_payload: The Frame Payload.
        @return: 0 is success, < 0 if failure.
    """ 
    def handle_edge_data_from_legacy(self, dev_id, dev_eui, dev_addr, frame_payload):
        # log.info(f'Received Edge Frame from legacy route. Dev Addr: {dev_addr}');
        # self.statistics["rx_ns"] = self.statistics["rx_ns"] + 1
        # self.statistics["tx_ns"] = self.statistics["tx_ns"] + 1
        # self.statistics["rx_e2l_frames"] = self.statistics["rx_e2l_frames"] + 1
        return 0
        
    """
        @brief  This function handle new legacy frame received by an ED, passing by the legacy route.
        @param dev_id: The Dev ID as in TTS.
        @param dev_eui: The Dev EUI.
        @param dev_addr: The Dev Addr.
        @param frame_payload: The Frame Payload.
        @return: 0 is success, < 0 if failure.
    """
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

    """
        @brief  This function handle new edge frame received by an ED, passing by the E2ED route.
        @param gw_id: The GW ID.
        @param dev_eui: The Dev EUI.
        @param dev_addr: The Dev Addr.
        @param aggregated_data: The Aggregated Data.
        @param delta_time: The Delta Time.
        @return: 0 is success, < 0 if failure.
    """
    def handle_edge_data(self, gw_id, dev_eui, dev_addr, aggregated_data, delta_time):
        log.info(f'Received Edge Frame from E2ED. Data: {aggregated_data} Dev Addr: {dev_addr}. Passyng from GW: {gw_id}');
        self.statistics["rx_e2l_frames"] = self.statistics["rx_e2l_frames"] + 1
        for i in range(len(self.e2gw_ids)):
            if self.statistics["gateways"].get(self.e2gw_ids[i]) is None:
                continue
            self.statistics["gateways"][self.e2gw_ids[i]]["rx"] = self.statistics["gateways"][self.e2gw_ids[i]].get("rx", 0) + self.window_size
            if self.e2gw_ids[i] == gw_id:
                self.statistics["gateways"][self.e2gw_ids[i]]["tx"] = self.statistics["gateways"][self.e2gw_ids[i]].get("tx", 0) + 1

        # SEND LOG
        if self.e2ed_ids.index(dev_eui) == 0:
            self._send_log(type=LOG_ED, message=f'E2L Frame Received by DM')

        return 0

    """
        @brief  Thid function start a thread to handle the dashboard update loop.
        @return: None.
    """
    def start_dashboard_update_loop(self):
        if self.dashboard_rpc_stub is None:
            return
        self.dashboard_update_loop = Thread(target=self._update_dashboard)
        self.dashboard_update_loop.start()

    """
        @brief  This function set the mqtt client object.
        @param mqtt_client: The mqtt client object.
        @return: None.
    """
    def set_mqtt_client(self, mqtt_client):
        self.mqtt_client = mqtt_client