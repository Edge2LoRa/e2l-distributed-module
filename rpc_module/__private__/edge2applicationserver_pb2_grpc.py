# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import rpc_module.__private__.edge2applicationserver_pb2 as edge2applicationserver__pb2


class Edge2ApplicationServerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.new_data = channel.unary_unary(
                '/edge2applicationserver.Edge2ApplicationServer/new_data',
                request_serializer=edge2applicationserver__pb2.EdgeData.SerializeToString,
                response_deserializer=edge2applicationserver__pb2.ResponseMessage.FromString,
                )
        self.store_e2gw_pub_info = channel.unary_unary(
                '/edge2applicationserver.Edge2ApplicationServer/store_e2gw_pub_info',
                request_serializer=edge2applicationserver__pb2.E2GWPubInfo.SerializeToString,
                response_deserializer=edge2applicationserver__pb2.ResponseMessage.FromString,
                )


class Edge2ApplicationServerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def new_data(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def store_e2gw_pub_info(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_Edge2ApplicationServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'new_data': grpc.unary_unary_rpc_method_handler(
                    servicer.new_data,
                    request_deserializer=edge2applicationserver__pb2.EdgeData.FromString,
                    response_serializer=edge2applicationserver__pb2.ResponseMessage.SerializeToString,
            ),
            'store_e2gw_pub_info': grpc.unary_unary_rpc_method_handler(
                    servicer.store_e2gw_pub_info,
                    request_deserializer=edge2applicationserver__pb2.E2GWPubInfo.FromString,
                    response_serializer=edge2applicationserver__pb2.ResponseMessage.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'edge2applicationserver.Edge2ApplicationServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Edge2ApplicationServer(object):
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
        return grpc.experimental.unary_unary(request, target, '/edge2applicationserver.Edge2ApplicationServer/new_data',
            edge2applicationserver__pb2.EdgeData.SerializeToString,
            edge2applicationserver__pb2.ResponseMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def store_e2gw_pub_info(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/edge2applicationserver.Edge2ApplicationServer/store_e2gw_pub_info',
            edge2applicationserver__pb2.E2GWPubInfo.SerializeToString,
            edge2applicationserver__pb2.ResponseMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
