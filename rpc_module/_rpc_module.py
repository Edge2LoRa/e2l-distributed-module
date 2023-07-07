# import rpyc

from rpc_module.__private__ import rpc_server_pb2_grpc
from rpc_module.__private__.rpc_server_pb2 import NewDataResponse


class Edge2LoraRpcService(rpc_server_pb2_grpc.Edge2LoraRPCServiceServicer):

    def _init_(self, *args, **kwargs):
        super(rpc_server_pb2_grpc.Edge2LoraRPCServiceServicer, self).__init__(*args, **kwargs)
        callback = kwargs.get("callback")
        if callback is None:
            raise Exception("No callback set")
        self.data_received_callback = callback

    def register_function(self, callback):
        self.data_received_callback = callback

    def new_data(self, request, context):
        data = request.name
        print(data)
        return NewDataResponse(message = "OK")
        return self.data_received_callback(request.data)
