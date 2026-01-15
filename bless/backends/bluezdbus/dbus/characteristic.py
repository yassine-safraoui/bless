import asyncio
import logging
import os

import bleak.backends.bluezdbus.defs as defs  # type: ignore

from dbus_next import DBusError  # type: ignore
from dbus_next.aio import ProxyInterface  # type: ignore
from dbus_next.constants import PropertyAccess  # type: ignore
from dbus_next.service import ServiceInterface, method, dbus_property  # type: ignore
from dbus_next.signature import Variant  # type: ignore
from enum import Enum
from typing import List, TYPE_CHECKING, Any, Dict

from .descriptor import BlueZGattDescriptor, DescriptorFlags  # type: ignore
from .device import Device1
from .session import NotifySession  # type: ignore

if TYPE_CHECKING:
    from bless.backends.bluezdbus.dbus.service import (  # type: ignore # noqa: F401
        BlueZGattService,
    )

logger = logging.getLogger(name=__name__)


class Flags(Enum):
    BROADCAST = "broadcast"
    READ = "read"
    WRITE_WITHOUT_RESPONSE = "write-without-response"
    WRITE = "write"
    NOTIFY = "notify"
    INDICATE = "indicate"
    AUTHENTICATED_SIGNED_WRITES = "authenticated-signed-writes"
    RELIABLE_WRITE = "reliable-write"
    WRITABLE_AUXILIARIES = "writable-auxiliaries"
    ENCRYPT_READ = "encrypt-read"
    ENCRYPT_WRITE = "encrypt-write"
    ENCRYPT_AUTHENTICATED_READ = "encrypt-authenticated-read"
    ENCRYPT_AUTHENTICATED_WRITE = "encrypt-authenticated-write"


class BlueZGattCharacteristic(ServiceInterface):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """

    interface_name: str = defs.GATT_CHARACTERISTIC_INTERFACE

    def __init__(
        self,
        uuid: str,
        flags: List[Flags],
        index: int,
        service: "BlueZGattService",  # noqa: F821
    ):
        """
        Create a BlueZ Gatt Characteristic

        Parameters
        ----------
        uuid : str
            The unique identifier for the characteristic
        flags : List[Flags]
            A list of strings that represent the properties of the
            characteristic
        index : int
            The index number for this characteristic in the service
        service : BlueZService
            The Gatt Service that owns this characteristic
        """
        self.path: str = service.path + "/char" + f"{index:04d}"
        self._uuid: str = uuid
        self._flags: List[str] = [x.value for x in flags]
        self._service_path: str = service.path  # noqa: F821
        self._service: "BlueZGattService" = service  # noqa: F821

        self._value: bytes = b""
        self._notifying_calls: int = 0
        self._subscribed_centrals: Dict[str, NotifySession] = {}
        self.descriptors: List["BlueZGattDescriptor"] = []  # noqa: F821

        super(BlueZGattCharacteristic, self).__init__(self.interface_name)

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":  # type: ignore # noqa: F821 N802
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Service(self) -> "o":  # type: ignore # noqa: F821 N802
        return self._service_path

    @dbus_property()
    def Value(self) -> "ay":  # type: ignore # noqa: F821 N802
        return self._value

    @Value.setter  # type: ignore
    def Value(self, value: "ay"):  # type: ignore # noqa: F821 N802
        if isinstance(value, bytearray):
            value = bytes(value)
        self._value = value

    @dbus_property(access=PropertyAccess.READ)
    def Notifying(self) -> "b":  # type: ignore # noqa: F821 N802
        return self._notifying_calls > 0 or self.NotifyAcquired

    @dbus_property(access=PropertyAccess.READ)  # noqa: F722
    def Flags(self) -> "as":  # type: ignore # noqa: F821 F722 N802
        return self._flags

    @dbus_property(access=PropertyAccess.READ)  # noqa: F722
    def NotifyAcquired(self) -> "b":  # type: ignore # noqa: F821
        return len(self._subscribed_centrals) > 0

    @method()  # noqa: F722
    async def ReadValue(self, options: "a{sv}") -> "ay":  # type: ignore # noqa: F722 F821 N802 E501
        """
        Read the value of the characteristic.
        This is to be fully implemented at the application level

        Parameters
        ----------
        options : Dict
            A list of options

        Returns
        -------
        bytes
            The bytes that is the value of the characteristic
        """
        device_path: str = options["device"]
        device: ProxyInterface = Device1.get_device(self._service.bus, device_path)
        options["central_id"] = await device.get_address()
        f = self._service.app.Read
        if f is None:
            raise NotImplementedError()
        return f(self, options)

    @method()  # noqa: F722
    def WriteValue(self, value: "ay", options: "a{sv}"):  # type: ignore # noqa
        """
        Write a value to the characteristic
        This is to be fully implemented at the application level

        Parameters
        ----------
        value : bytes
            The value to set
        options : Dict
            Some options for you to select from
        """
        device_path: str = options["device"]
        device: ProxyInterface = Device1.get_device(self._service.bus, device_path)
        options["central_id"] = device.get_address()
        f = self._service.app.Write
        if f is None:
            raise NotImplementedError()
        f(self, value, options)

    @method()
    async def AcquireNotify(self, options: "a{sv}") -> "hq":  # type: ignore # noqa
        """
        Called when a central device subscribes to the
        characteristic
        """
        mtu: int = options["mtu"].value
        potential_device: Variant = options["device"]
        device_path: str = potential_device.value

        # Can only process this if we are not already subscribed
        if self.Notifying and not self.NotifyAcquired:
            logger.error("AcquireNotify attempted after StartNotify called")
            raise DBusError(
                "org.bluez.Error.NotPermitted", "AcquireNotify not permitted"
            )

        session: NotifySession = NotifySession(
            device_path, mtu, self._service.app.bus, self.ReleaseNotify
        )
        rx: int = await session.start()
        address: str = await session.get_device_address()
        logger.debug(f"AcquireNotify on {self.UUID} from {address} on FD {rx}")

        f = self._service.app.StartNotify
        if f is None:
            raise NotImplementedError()

        f(self, session)
        self._subscribed_centrals[address] = session

        async def close_rx():
            logger.debug("Closing RX")
            await asyncio.sleep(2)
            os.close(rx)

        asyncio.create_task(close_rx())
        return [rx, mtu]

    async def ReleaseNotify(self, session: NotifySession):
        address: str = await session.get_device_address()
        logger.debug(f"ReleaseNotify on {self.UUID} from {address}")
        f = self._service.app.StopNotify
        if f is None:
            raise NotImplementedError()
        f(self, session)
        del self._subscribed_centrals[address]

    @method()
    def StartNotify(self):  # noqa: N802
        """
        Begin a subscription to the characteristic
        """
        if self.NotifyAcquired:
            logger.info(
                "StartNotify called. "
                + "AcquireNotify already called. "
                + "Ignoring call to Start Notify"
            )
            return

        logger.debug(f"StartNotify on {self.UUID}")
        f = self._service.app.StartNotify
        if f is None:
            raise NotImplementedError()
        f(self, {})
        self._notifying_calls += 1

    @method()
    async def StopNotify(self):  # noqa: N802
        """
        Stop a subscription to the characteristic
        """
        if self.NotifyAcquired:
            logger.error("StopNotify called but notifications are aquried!")
            return

        f = self._service.app.StopNotify
        if f is None:
            raise NotImplementedError()
        f(self, {})
        self._notifying_calls -= 1

    def update_value(self) -> None:
        """
        This method does not actually alter that value of the characteristic,
        but rather sends updates to subscribed centrals.
        """
        if self.NotifyAcquired is True:
            for central_id, session in self._subscribed_centrals.items():
                logger.debug(f"Sending update to {central_id}")
                if not session.send_update(self._value):
                    logger.warn(f"Failed to send update to {central_id}")

        else:
            self.emit_properties_changed(changed_properties={"Value": self._value})

    async def add_descriptor(
        self, uuid: str, flags: List[DescriptorFlags], value: Any
    ) -> BlueZGattDescriptor:
        """
        Adds a BlueZGattDescriptor to the characteristic.

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the descriptor
        flags : List[DescriptorFlags],
            A list of flags to apply to the descriptor
        value : Any
            The descriptor's value
        """
        index: int = len(self.descriptors) + 1
        descriptor: BlueZGattDescriptor = BlueZGattDescriptor(uuid, flags, index, self)
        descriptor._value = value  # type: ignore
        self.descriptors.append(descriptor)
        await self._service.app._register_object(descriptor)
        return descriptor

    async def get_obj(self) -> Dict:
        """
        Obtain the underlying dictionary within the BlueZ API that describes
        the characteristic

        Returns
        -------
        Dict
            The dictionary that describes the characteristic
        """
        return {"UUID": Variant("s", self._uuid)}
