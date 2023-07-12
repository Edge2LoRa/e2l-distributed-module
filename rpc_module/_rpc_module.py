# import rpyc
import time
import math
from rpc_module.__private__ import rpc_server_pb2_grpc
from rpc_module.__private__.rpc_server_pb2 import NewDataResponse


class Edge2LoraRpcService(rpc_server_pb2_grpc.Edge2LoraRPCServiceServicer):


    def register_function(self, callback):
        self.data_received_callback = callback

    def new_data(self, request, context):
        now = math.floor(time.time() * 1000)
        data = request.name
        timetag = request.timetag

        delta = now - timetag


        self.delta_time_array.append(delta)
        with open("output_files/e2lora_delta_data.txt", "a") as f:
            f.write(str(delta) + ", ")

        if (len(self.delta_time_array) >= self.delta_array_len_limit):
            print("WRITING TO FILE")
            with open("output_files/e2lora_delta_avg.txt", "a") as f:
                f.write("- [ ")
                sum = 0
                for elem in self.delta_time_array:
                    f.write(str(elem) + ", ")
                    sum += elem
                f.write("]\n")
                avg = sum / len(self.delta_time_array)
                f.write(f'AVG: {str(avg)} \n')

            self.delta_time_array = []
        print(data)
        print(timetag)
        print(now)
        print(delta)

        return NewDataResponse(message = "OK")
