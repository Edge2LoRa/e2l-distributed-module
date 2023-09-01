from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class EdPubInfo(_message.Message):
    __slots__ = ["dev_eui", "dev_addr", "g_as_ed", "dev_public_key"]
    DEV_EUI_FIELD_NUMBER: _ClassVar[int]
    DEV_ADDR_FIELD_NUMBER: _ClassVar[int]
    G_AS_ED_FIELD_NUMBER: _ClassVar[int]
    DEV_PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    dev_eui: str
    dev_addr: str
    g_as_ed: bytes
    dev_public_key: bytes
    def __init__(self, dev_eui: _Optional[str] = ..., dev_addr: _Optional[str] = ..., g_as_ed: _Optional[bytes] = ..., dev_public_key: _Optional[bytes] = ...) -> None: ...

class GwInfo(_message.Message):
    __slots__ = ["status_code", "g_gw_ed"]
    STATUS_CODE_FIELD_NUMBER: _ClassVar[int]
    G_GW_ED_FIELD_NUMBER: _ClassVar[int]
    status_code: int
    g_gw_ed: bytes
    def __init__(self, status_code: _Optional[int] = ..., g_gw_ed: _Optional[bytes] = ...) -> None: ...
