# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from rpc_module.__private__ import rpc_server_pb2 as rpc__server__pb2


class Edge2LoraRPCServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.new_data = channel.unary_unary(
                '/edge2lorarpcservice.Edge2LoraRPCService/new_data',
                request_serializer=rpc__server__pb2.NewDataRequest.SerializeToString,
                response_deserializer=rpc__server__pb2.NewDataResponse.FromString,
                )


class Edge2LoraRPCServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def new_data(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_Edge2LoraRPCServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'new_data': grpc.unary_unary_rpc_method_handler(
                    servicer.new_data,
                    request_deserializer=rpc__server__pb2.NewDataRequest.FromString,
                    response_serializer=rpc__server__pb2.NewDataResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'edge2lorarpcservice.Edge2LoraRPCService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Edge2LoraRPCService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def new_data(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/edge2lorarpcservice.Edge2LoraRPCService/new_data',
            rpc__server__pb2.NewDataRequest.SerializeToString,
            rpc__server__pb2.NewDataResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
