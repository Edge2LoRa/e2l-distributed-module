#!/bin/bash
python3 -m grpc_tools.protoc -Iprotos --python_out=rpc_module/__private__ --pyi_out=rpc_module/__private__ --grpc_python_out=rpc_module/__private__ ./protos/edge2applicationserver.proto
