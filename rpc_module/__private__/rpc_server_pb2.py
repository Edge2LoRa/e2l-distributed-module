# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: rpc_server.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10rpc_server.proto\x12\x13\x65\x64ge2lorarpcservice\"\x1e\n\x0eNewDataRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\"\"\n\x0fNewDataResponse\x12\x0f\n\x07message\x18\x01 \x01(\t2l\n\x13\x45\x64ge2LoraRPCService\x12U\n\x08new_data\x12#.edge2lorarpcservice.NewDataRequest\x1a$.edge2lorarpcservice.NewDataResponseB:\n\x1dio.grpc.examples.edge2lorarpcB\x11\x45\x64ge2LoRaRPCProtoP\x01\xa2\x02\x03\x45\x32Lb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'rpc_server_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\035io.grpc.examples.edge2lorarpcB\021Edge2LoRaRPCProtoP\001\242\002\003E2L'
  _globals['_NEWDATAREQUEST']._serialized_start=41
  _globals['_NEWDATAREQUEST']._serialized_end=71
  _globals['_NEWDATARESPONSE']._serialized_start=73
  _globals['_NEWDATARESPONSE']._serialized_end=107
  _globals['_EDGE2LORARPCSERVICE']._serialized_start=109
  _globals['_EDGE2LORARPCSERVICE']._serialized_end=217
# @@protoc_insertion_point(module_scope)
