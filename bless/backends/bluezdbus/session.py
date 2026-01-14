import asyncio

from threading import Thread
from typing import cast

from .dbus.session import NotifySession

from ..session import BlessGATTSession


class BlessGATTSessionWinRT(BlessGATTSession):

    @property
    def session(self) -> NotifySession:
        return cast(NotifySession, self.obj)

    @property
    def device_id(self) -> str:
        result: str

        def wrapper():
            nonlocal result
            result = asyncio.run(self.session.get_device_address())

        thread: Thread = Thread(target=wrapper)
        thread.start()
        thread.join()

        return result

    @property
    def mtu(self) -> int:
        return self.session.mtu
