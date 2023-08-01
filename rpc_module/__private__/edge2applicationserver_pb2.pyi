from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ResponseMessage(_message.Message):
    __slots__ = ["status_code", "message"]
    STATUS_CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status_code: int
    message: bytes
    def __init__(self, status_code: _Optional[int] = ..., message: _Optional[bytes] = ...) -> None: ...

class e2gw_pub_info(_message.Message):
    __slots__ = ["gw_ip_addr", "gw_port", "e2gw_pub_key"]
    GW_IP_ADDR_FIELD_NUMBER: _ClassVar[int]
    GW_PORT_FIELD_NUMBER: _ClassVar[int]
    E2GW_PUB_KEY_FIELD_NUMBER: _ClassVar[int]
    gw_ip_addr: str
    gw_port: str
    e2gw_pub_key: bytes
    def __init__(self, gw_ip_addr: _Optional[str] = ..., gw_port: _Optional[str] = ..., e2gw_pub_key: _Optional[bytes] = ...) -> None: ...

class NewDataRequest(_message.Message):
    __slots__ = ["name", "timetag"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TIMETAG_FIELD_NUMBER: _ClassVar[int]
    name: str
    timetag: int
    def __init__(self, name: _Optional[str] = ..., timetag: _Optional[int] = ...) -> None: ...

class NewDataResponse(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...
