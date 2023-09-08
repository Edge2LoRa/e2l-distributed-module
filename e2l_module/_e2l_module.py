import os
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from Crypto.PublicKey import ECC
import logging
import grpc
from e2gw_rpc_client import edge2gateway_pb2_grpc, EdPubInfo, GwInfo



DEBUG = os.getenv('DEBUG', False)
DEBUG = True if DEBUG == '1' else False
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)

class E2LoRaModule():
    """
    This class is handle the Edge2LoRa Protocol.
    """
    def __init__(self):
        # Generate ephimeral ecc private/public key pair
        self.ephimeral_private_key = ECC.generate(curve='P-256')
        self.ephimeral_public_key = self.ephimeral_private_key.public_key()
        self.ephimeral_public_key_bytes_compressed = self.ephimeral_public_key.export_key(format='SEC1')
        log.info(f'ephimeral public key: {self.ephimeral_public_key_bytes_compressed}')
        # self.ephimeral_private_key = ec.generate_private_key(ec.SECP256R1())
        # self.ephimeral_public_key = self.ephimeral_private_key.public_key()
        # self.ephimeral_public_key_bytes_compressed = self.ephimeral_public_key.public_bytes(encoding = Encoding.X962, format = PublicFormat.UncompressedPoint )
        # Init active directory
        self.active_directory = {
            "e2gws": {},
            "e2eds": {}
        }

    """
        @brief: This function is used to send a downlink frame to a ED.
        @para
    """
    def _send_downlink_frame(self, mqtt_client, base64_message, dev_eui, priority = "HIGHEST"):
        downlink_frame = {
            "downlinks": [
                {
                    "f_port": 3,
                    "frm_payload": base64_message,
                    "priority": priority
                }
            ]
        }

        base_topic = os.getenv('MQTT_BASE_TOPIC')
        topic = f'{base_topic}/{dev_eui}/down/push'
        log.info(f'Send downlink frame to {dev_eui}')
        mqtt_client.publish_to_topic(
            topic = topic,
            message = str(downlink_frame)
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
        # gw_pub_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), gw_pub_key_compressed)
        # g_as_gw = self.ephimeral_private_key.exchange(ec.ECDH(), gw_pub_key)
        gw_pub_key = ECC.import_key(gw_pub_key_compressed, curve_name='P-256')
        g_as_gw = gw_pub_key.pointQ * self.ephimeral_private_key.d
        log.info(f'g_as_gw: ({g_as_gw.x}, {g_as_gw.y})')

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
        # ed_pub_info = EdPubInfo(dev_eui="dev_eui", dev_addr="dev_addr", g_as_ed=b'g_as_ed', dev_public_key = b'dev_pub_key_compressed')
        # response = stub.handle_ed_pub_info(ed_pub_info)
        log.info(f'E2GW {gw_rpc_endpoint_address} is added to active directory')
        return 0

    """
        @brief  This funciont handle new public key info received by a ED.
                It complete the process of key agreement for the server.
        @param dev_eui: The Dev EUI.
        @param dev_addr: The Dev Addr.
        @param dev_pub_key_compressed: The Compressed Dev Public Key.
        @return: 0 is success, < 0 if failure.
        @error code:
            -1: Error 
    """
    def handle_edge_join_request(self, dev_eui, dev_addr, dev_pub_key_compressed_base_64, mqtt_client):

        # Assign E2GW to E2ED and store informations
        e2gw = self.active_directory["e2gws"].get(list(self.active_directory["e2gws"].keys())[0])
        if e2gw is None:
            log.error("No E2GW found")
            return -1

        dev_obj = {
            "dev_eui": dev_eui,
            "dev_addr": dev_addr,
            "e2gw": e2gw.get("gw_rpc_endpoint_address"),
        }
        self.active_directory["e2eds"][dev_eui] = dev_obj
        # Get g_as_gw
        g_as_gw = e2gw.get("g_as_gw")
        # Schedule downlink to ed with g_as_gw
        # encode g_as_gw in base64
        g_as_gw_base_64 = base64.b64encode(g_as_gw)
        downlink_frame = self._send_downlink_frame(
            mqtt_client=mqtt_client,
            base64_message = g_as_gw_base_64, 
            dev_eui = dev_eui
            )

        # Generate g_as_ed
        # Decode base64
        dev_pub_key_compressed = base64.b64decode(dev_pub_key_compressed_base_64)
        dev_pub_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), dev_pub_key_compressed)
        g_as_ed = self.ephimeral_private_key.exchange(ec.ECDH(), dev_pub_key)
        # g_as_ed_compressed = g_as_ed.public_bytes(encoding = Encoding.X962, format = PublicFormat.CompressedPoint)
        
        ### Send g_as_ed to e2gw
        e2gw_rpc_stub = e2gw.get("e2gw_stub")
        ed_pub_info = EdPubInfo(dev_eui=dev_eui, dev_addr=dev_addr, g_as_ed=g_as_ed, dev_public_key = dev_pub_key_compressed)
        response = e2gw_rpc_stub.handle_ed_pub_info(ed_pub_info)
        g_gw_ed_secret = response.g_gw_ed
        g_private_int = int.from_bytes(g_gw_ed_secret, byteorder='big')
        g_private_key = ec.derive_private_key(g_private_int, ec.SECP256R1())
        g_gw_ed = g_private_key.public_key()
        edgeSKey = self.ephimeral_private_key.exchange(ec.ECDH(), g_gw_ed)
        log.info(f'edgeSKey: {[x for x in edgeSKey]}')
        # Hash edgeSKey
        import hashlib
        edgeSIntKey = hashlib.sha256(b'\x00' + edgeSKey).digest()[:16]
        edgeSEncKey = hashlib.sha256(b'\x01' + edgeSKey).digest()[:16]
        log.info(f'edgeSIntKey: {[x for x in edgeSIntKey]}')
        log.info(f'edgeSEncKey: {[x for x in edgeSEncKey]}')

        return 0
     
    def handle_edge_data_from_legacy(self):
        return 0