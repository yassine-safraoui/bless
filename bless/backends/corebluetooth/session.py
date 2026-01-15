from CoreBluetooth import CBCentral  # type: ignore[import-untyped]
from typing import cast

from ..session import BlessGATTSession


class BlessGATTSessionCoreBluetooth(BlessGATTSession):

    @property
    def central(self) -> CBCentral:
        return cast(CBCentral, self.obj)

    @property
    def central_id(self) -> str:
        return self.central.identifier().UUIDString()

    @property
    def mtu(self) -> int:
        return self.central.maximumUpdateValueLength()
