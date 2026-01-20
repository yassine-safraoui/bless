from typing import Dict, Optional, cast
from .dbus.application import BlueZOptions
from ..request import BlessGATTRequest


class BlessGATTRequestBlueZ(BlessGATTRequest):

    @property
    def options(self) -> BlueZOptions:
        return cast(Dict, self.obj)

    @property
    def central_id(self) -> str:
        """
        Note, that the device returned within the options on
        BlueZ is a DBus path to the device object. It is the
        receving calls responsibility to use the DBus to resolve
        the device address and populate this field
        """
        return self.obj["central_id"].value

    @property
    def mtu(self) -> int:
        return self.obj["mtu"].value

    @property
    def offset(self) -> int:
        return 0 if "offset" not in self.obj else self.obj["offset"].value

    @property
    def response_requested(self) -> Optional[bool]:
        return None if "type" not in self.obj else (self.obj["type"].value == "request")
