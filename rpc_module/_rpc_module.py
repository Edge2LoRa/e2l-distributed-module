import time
import math
import os
import base64
from rpc_module.__private__ import edge2applicationserver_pb2_grpc
from rpc_module.__private__.edge2applicationserver_pb2 import NewDataResponse
from rpc_module.__private__.edge2applicationserver_pb2 import ResponseMessage

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

ecc_curve = os.environ.get("ECC_CURVE")
if ecc_curve is None:
    ecc_curve = "p256"

class Edge2LoRaApplicationServer(edge2applicationserver_pb2_grpc.Edge2ApplicationServerServicer):

    def __init__(self) -> None:
        super().__init__()
        self.e2gw_active_directory = {}

    def register_function(self, callback):
        self.data_received_callback = callback

    def store_e2gw_pub_info(self, request, context):
        ip_address = request.gw_ip_addr
        gw_pub_key_bytes = request.e2gw_pub_key
        gw_pub_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), gw_pub_key_bytes)

        # Generate ecc private key
        ephimeral_private_key = ec.generate_private_key(ec.SECP256R1())
        # Generate ecc public key
        ephimeral_public_key = ephimeral_private_key.public_key()
        ephimeral_public_key_bytes = ephimeral_public_key.public_bytes(encoding = Encoding.X962, format = PublicFormat.UncompressedPoint )

        g_as_gw = ephimeral_private_key.exchange(ec.ECDH(), gw_pub_key)
        print("G_AS_GW: ", list(g_as_gw))


        self.e2gw_active_directory[ip_address] = {
            "ephimeral_gw_pub_key": gw_pub_key,
            "ephimaral_server_key" : {
                "private": ephimeral_private_key,
                "public": ephimeral_public_key
            },
            "g_as_gw": g_as_gw
        }
        return ResponseMessage(
            status_code=200,
            message= ephimeral_public_key_bytes
        )
        

    def new_data(self, request, context):
        now = math.floor(time.time() * 1000)
        data = request.name
        timetag = request.timetag

        delta = now - timetag

        # self.delta_time_array.append(delta)
        with open("output_files/e2lora_delta_data.txt", "a") as f:
            f.write(f'{delta}\n')

        return NewDataResponse(message="OK")
