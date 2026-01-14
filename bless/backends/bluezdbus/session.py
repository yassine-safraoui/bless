from typing import cast

from .dbus.session import NotifySession

from ..session import BlessGATTSession



class BlessGATTSessionBlueZ(BlessGATTSession):

    @property
    def session(self) -> NotifySession:
        return cast(NotifySession, self.obj)

    @property
    def device_id(self) -> str:
        return self.session.address

    @property
    def mtu(self) -> int:
        return self.session.mtu
