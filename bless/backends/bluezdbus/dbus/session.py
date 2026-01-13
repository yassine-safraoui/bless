import asyncio
import inspect
import logging
import os

import bleak.backends.bluezdbus.defs as defs  # type: ignore

from asyncio import AbstractEventLoop, Event
from dbus_next.aio import ProxyInterface, ProxyObject, MessageBus
from dbus_next.introspection import Interface, Node
from select import poll, POLLHUP, POLLERR, POLLNVAL
from socket import socket, socketpair, AF_UNIX, SOCK_SEQPACKET
from typing import Callable, Optional

from .device import Device1

logger = logging.getLogger(name=__name__)


class NotifySession:
    def __init__(self, device_path: str, mtu: int, bus: MessageBus, on_disconnect: Callable[["NotifySession"], None], loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()):
        self.device_path: str = device_path
        self.mtu: int = mtu
        self.bus: MessageBus = bus
        self.disconnect_callback: Callable[["NotifySession"], None] = on_disconnect
        self.loop: AbstractEventLoop = loop
        self.closed = asyncio.Event()

        self._tx: Optional[socket] = None
        self._device: Optional[ProxyInterface] = None

    def get_device(self) -> ProxyInterface:
        return self._device

    async def get_device_address(self) -> str:
        return await self._device.get_address()  # type: ignore

    async def watch_fd(self) -> None:
        fd: int = self._tx.fileno()
        p: poll = poll()
        p.register(fd, POLLHUP | POLLERR | POLLNVAL)

        while not self.closed.is_set():
            events = await asyncio.to_thread(p.poll, 500)
            for (ev_fd, ev) in events:
                if ev & (POLLHUP | POLLERR | POLLNVAL):
                    self.close()


    def _on_fd_readable(self):
        """
        For BlueZ AcquireNotify, readability usually means the peer closed
        (EOF / HUP). Consume/confirm and then close session.
        """
        logger.debug("Obtained reading on notifying session")
        if self._tx is None:
            return
        try:
            data: bytes = self._tx.recv(1024)
            # Most common: b"" => EOF => unsubscribed/disconnected
            if len(data) == 0:
                self.close()
        except BlockingIOError:
            return
        except OSError:
            # Treat any error as session ended
            self.close()

    async def start(self) -> int:

        # Query the device object
        node: Node = Node.default(name=self.device_path)
        device_iface: Interface = Device1().introspect()
        node.interfaces.append(device_iface)

        object: ProxyObject = self.bus.get_proxy_object("org.bluez", self.device_path, node)
        self._device = object.get_interface(defs.DEVICE_INTERFACE)

        # create a bluetooth socket pair
        self._tx, rx = socketpair(AF_UNIX, SOCK_SEQPACKET)

        # Unblock the transmission socket
        fd_tx: int = self._tx.fileno()
        os.set_blocking(fd_tx, False)

        # Fire when fd becomes readable (EOF/hup)
        # self.loop.add_reader(fd_tx, self._on_fd_readable)
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
