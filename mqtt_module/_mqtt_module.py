import paho.mqtt.client as mqtt
import logging 



class MQTTModule():

    def __init__(self, **kwargs) -> None:
        username = kwargs.get('username', None)
        password = kwargs.get('password', None)
        host = kwargs.get('host', None)
        port = kwargs.get('port', None)
        client_id = kwargs.get('client_id', __name__)
        clean_session = kwargs.get('clean_session', True)
        if username is None or password is None or host is None or port is None:
            raise Exception('Missing parameters')
        self.client = mqtt.Client(
            client_id =client_id,
            clean_session=clean_session,
            protocol = mqtt.MQTTv311
        )
        self.client.username_pw_set(username, password)
        self.client.connect(host, port, 60)

    def enable_logger(self, enable = True):
        if enable:
            self.client.enable_logger(logging.getLogger(__name__))
        else:
            self.client.disable_logger()

    def subscribe_to_topic(self, topic: str, callback):
        self.client.subscribe(topic)
        self.client.on_message = callback

    def wait_for_message(self):
        self.client.loop_forever()