import asyncio
import inspect
import logging
import os

from asyncio import AbstractEventLoop, Event
from dbus_next.aio import ProxyInterface, MessageBus  # type: ignore
from select import poll, POLLHUP, POLLERR, POLLNVAL
from socket import socket, socketpair, AF_UNIX, SOCK_SEQPACKET
from typing import Callable, Coroutine, Optional, Union

from .device import Device1

logger = logging.getLogger(name=__name__)

DisconnectCallback = Union[
    Callable[["NotifySession"], None], Callable[["NotifySession"], Coroutine]
]


class NotifySession:
    def __init__(
        self,
        device_path: str,
        mtu: int,
        bus: MessageBus,
        on_disconnect: DisconnectCallback,
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop(),
    ):
        self.device_path: str = device_path
        self.mtu: int = mtu
        self.bus: MessageBus = bus
        self.disconnect_callback: DisconnectCallback = on_disconnect
        self.loop: AbstractEventLoop = loop
        self.closed: Event = Event()

        self._tx: Optional[socket] = None
        self._device: Optional[ProxyInterface] = None
        self._address: Optional[str] = None

    @property
    def address(self) -> str:
        if self._address is None:
            raise Exception("NotifySession not started. Address property not obtained")

        return self._address

    def get_device(self) -> ProxyInterface:
        if self._device is None:
            raise Exception("NotifySession not started. Device properties not obtained")

        return self._device

    async def get_device_address(self) -> str:
        return await self._device.get_address()  # type: ignore

    async def watch_fd(self) -> None:
        if self._tx is None:
            raise Exception("NotifySession not started. Transmission socket not open")
        fd: int = self._tx.fileno()
        p: poll = poll()
        p.register(fd, POLLHUP | POLLERR | POLLNVAL)

        while not self.closed.is_set():
            events = await asyncio.to_thread(p.poll, 500)
            for ev_fd, ev in events:
                if ev & (POLLHUP | POLLERR | POLLNVAL):
                    self.close()

    async def start(self) -> int:
        self._device = Device1.get_device(self.bus, self.device_path)
        self._address = await self.get_device_address()

        # create a bluetooth socket pair
        self._tx, rx = socketpair(AF_UNIX, SOCK_SEQPACKET)

        # Unblock the transmission socket
        fd_tx: int = self._tx.fileno()
        os.set_blocking(fd_tx, False)

        # watch when fd becomes readable (EOF/hup)
        asyncio.create_task(self.watch_fd())

        # return the receiving socket
        return rx.detach()

    def send_update(self, data: bytes) -> bool:
        if self._tx is None:
            return False

        try:
            max_len: int = max(0, self.mtu - 3)
            self._tx.send(data[:max_len])
            return True
        except BlockingIOError:
            # buffer full: drop or retry later
            return True
        except (BrokenPipeError, ConnectionResetError, OSError):
            self.close()
            return False

    def close(self):
        if self.closed.is_set():
            return

        self.closed.set()

        if self._tx is not None:
            try:
                self.loop.remove_reader(self._tx.fileno())
            except Exception:
                pass
            try:
                self._tx.close()
            except Exception:
                pass

        cb = self.disconnect_callback(self)
        if inspect.isawaitable(cb):
            asyncio.create_task(cb)
