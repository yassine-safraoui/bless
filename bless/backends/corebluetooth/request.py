from CoreBluetooth import CBATTRequest  # type: ignore
from typing import Optional, cast
from ..characteristic import GATTCharacteristicProperties
from ..request import BlessGATTRequest


class BlessGATTRequestCoreBluetooth(BlessGATTRequest):

    @property
    def request(self) -> CBATTRequest:
        return cast(CBATTRequest, self.obj)

    @property
    def central_id(self) -> str:
        return self.request.central().identifier().UUIDString()

    @property
    def mtu(self) -> int:
        return self.request.maximumUpdateValueLength()

    @property
    def offset(self) -> int:
        return self.request.offset()

    @property
    def response_requested(self) -> Optional[bool]:
        return not (
            self.request.characteristic().properties()
            & GATTCharacteristicProperties.write_without_response
        )
