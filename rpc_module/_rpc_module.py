import rpyc

class RPCModuleService(rpyc.Service):

    def _init_(self, *args, **kwargs):
        super(RPCModuleService, self).__init__(*args, **kwargs)
        callback = kwargs.get("callback")
        if callback is None:
            raise Exception("No callback set")
        self.data_received_callback = callback

    def register_function(self, callback):
        self.data_received_callback = callback

    @rpyc.exposed
    def new_data(self, data):
        if self.data_received_callback is not None:
            return self.data_received_callback(data)
        else:
            return {
                "success": False,
                "message": "No callback set"
            }
