import os
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import logging


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
        self.ephimeral_private_key = ec.generate_private_key(ec.SECP256R1())
        self.ephimeral_public_key = self.ephimeral_private_key.public_key()
        self.ephimeral_public_key_bytes_compressed = self.ephimeral_public_key.public_bytes(encoding = Encoding.X962, format = PublicFormat.UncompressedPoint )
        # Init active directory
        self.active_directory = {
            "e2gws": {},
            "e2eds": {}
        }

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
        gw_pub_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), gw_pub_key_compressed)
        g_as_gw = self.ephimeral_private_key.exchange(ec.ECDH(), gw_pub_key)
        self.active_directory["e2gws"][gw_rpc_endpoint_address] = {
            "gw_rpc_endpoint_address": gw_rpc_endpoint_address,
            "gw_rpc_endpoint_port": gw_rpc_endpoint_port,
            "gw_pub_key": gw_pub_key,
            "g_as_gw": g_as_gw
        }
        return 0


    def handle_edge_join_request(self, dev_eui, dev_addr, payload):
        log.info(f'Dev EUI: {dev_eui}')
        log.info(f'Dev Addr: {dev_addr}')
        log.info(f'Payload: {payload}')