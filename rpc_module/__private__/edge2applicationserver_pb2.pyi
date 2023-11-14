from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ResponseMessage(_message.Message):
    __slots__ = ["status_code", "message"]
    STATUS_CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status_code: int
    message: str
    def __init__(self, status_code: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class E2GWPubInfo(_message.Message):
    __slots__ = ["gw_ip_addr", "gw_port", "e2gw_pub_key"]
    GW_IP_ADDR_FIELD_NUMBER: _ClassVar[int]
    GW_PORT_FIELD_NUMBER: _ClassVar[int]
    E2GW_PUB_KEY_FIELD_NUMBER: _ClassVar[int]
    gw_ip_addr: str
    gw_port: str
    e2gw_pub_key: bytes
    def __init__(self, gw_ip_addr: _Optional[str] = ..., gw_port: _Optional[str] = ..., e2gw_pub_key: _Optional[bytes] = ...) -> None: ...

class EdgeData(_message.Message):
    __slots__ = ["gw_id", "dev_eui", "dev_addr", "aggregated_data", "fcnts", "timetag"]
    GW_ID_FIELD_NUMBER: _ClassVar[int]
    DEV_EUI_FIELD_NUMBER: _ClassVar[int]
    DEV_ADDR_FIELD_NUMBER: _ClassVar[int]
    AGGREGATED_DATA_FIELD_NUMBER: _ClassVar[int]
    FCNTS_FIELD_NUMBER: _ClassVar[int]
    TIMETAG_FIELD_NUMBER: _ClassVar[int]
    gw_id: str
    dev_eui: str
    dev_addr: str
    aggregated_data: int
    fcnts: _containers.RepeatedScalarFieldContainer[int]
    timetag: int
    def __init__(self, gw_id: _Optional[str] = ..., dev_eui: _Optional[str] = ..., dev_addr: _Optional[str] = ..., aggregated_data: _Optional[int] = ..., fcnts: _Optional[_Iterable[int]] = ..., timetag: _Optional[int] = ...) -> None: ...

class GwLog(_message.Message):
    __slots__ = ["gw_id", "dev_addr", "log", "frame_type", "fcnt", "timetag"]
    GW_ID_FIELD_NUMBER: _ClassVar[int]
    DEV_ADDR_FIELD_NUMBER: _ClassVar[int]
    LOG_FIELD_NUMBER: _ClassVar[int]
    FRAME_TYPE_FIELD_NUMBER: _ClassVar[int]
    FCNT_FIELD_NUMBER: _ClassVar[int]
    TIMETAG_FIELD_NUMBER: _ClassVar[int]
    gw_id: str
    dev_addr: str
    log: str
    frame_type: int
    fcnt: int
    timetag: int
    def __init__(self, gw_id: _Optional[str] = ..., dev_addr: _Optional[str] = ..., log: _Optional[str] = ..., frame_type: _Optional[int] = ..., fcnt: _Optional[int] = ..., timetag: _Optional[int] = ...) -> None: ...

class SysLog(_message.Message):
    __slots__ = ["gw_id", "memory_usage", "memory_available", "cpu_usage", "data_received", "data_transmitted"]
    GW_ID_FIELD_NUMBER: _ClassVar[int]
    MEMORY_USAGE_FIELD_NUMBER: _ClassVar[int]
    MEMORY_AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    CPU_USAGE_FIELD_NUMBER: _ClassVar[int]
    DATA_RECEIVED_FIELD_NUMBER: _ClassVar[int]
    DATA_TRANSMITTED_FIELD_NUMBER: _ClassVar[int]
    gw_id: str
    memory_usage: int
    memory_available: int
    cpu_usage: float
    data_received: int
    data_transmitted: int
    def __init__(self, gw_id: _Optional[str] = ..., memory_usage: _Optional[int] = ..., memory_available: _Optional[int] = ..., cpu_usage: _Optional[float] = ..., data_received: _Optional[int] = ..., data_transmitted: _Optional[int] = ...) -> None: ...
