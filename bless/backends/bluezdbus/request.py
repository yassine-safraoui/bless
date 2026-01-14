from typing import Dict, Optional, cast
from ..request import BlessGATTRequest


class BlessGATTRequestBlueZ(BlessGATTRequest):

    @property
    def options(self) -> Dict:
        return cast(Dict, self.obj)

    @property
    def central_id(self) -> str:
        """
        Note, that the device returned within the options on
        BlueZ is a DBus path to the device object. It is the
        receving calls responsibility to use the DBus to resolve
        the device address and populate this field
        """
        return self.obj["central_id"]

    @property
    def mtu(self) -> int:
        return self.obj["mtu"]

    @property
    def offset(self) -> int:
        return self.obj["offset"]

    @property
    def response_requested(self) -> Optional[bool]:
        return None if "type" not in self.obj else (self.obj["type"] == "request")
