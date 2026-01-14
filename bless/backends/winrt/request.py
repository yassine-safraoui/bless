from winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
    GattSession,
    GattReadRequest,
    GattWriteRequest,
)
from typing import Optional, Tuple, Union, cast
from ..request import BlessGATTRequest

GattRequest = Union[GattReadRequest, GattWriteRequest]
WinRTGattRequest = Tuple[GattSession, GattRequest]


class BlessGATTRequestWinRT(BlessGATTRequest):

    @property
    def object_data(self) -> WinRTGattRequest:
        return cast(WinRTGattRequest, self.obj)

    @property
    def session(self) -> GattSession:
        return cast(GattSession, self.object_data[0])

    @property
    def request(self) -> GattRequest:
        return cast(GattRequest, self.object_data[1])

    @property
    def central_id(self) -> str:
        return self.session.device_id.id

    @property
    def mtu(self) -> int:
        return self.session.max_pdu_size

    @property
    def offset(self) -> int:
        return self.request.offset

    @property
    def response_requested(self) -> Optional[bool]:
        return (
            None
            if isinstance(self.request, GattReadRequest)
            else (self.request.options != 0x1)
        )
