from bleak.backends.bluezdbus.defs import DEVICE_INTERFACE
from dbus_next.aio import MessageBus, ProxyInterface, ProxyObject  # type: ignore
from dbus_next.constants import PropertyAccess  # type: ignore
from dbus_next.introspection import Interface, Node  # type: ignore
from dbus_next.service import ServiceInterface, method, dbus_property  # type: ignore


class Device1(ServiceInterface):

    interface_name: str = DEVICE_INTERFACE

    def __init__(self):
        super().__init__(self.interface_name)

    @method()
    def Connect(self) -> "":  # type: ignore # type: ignore # noqa: F722
        raise NotImplementedError

    @method()
    def Disconnect(self) -> "":  # type: ignore # noqa: F722
        raise NotImplementedError

    @method()
    def ConnectProfile(self, uuid: "s") -> "":  # type: ignore # noqa: F722 F821
        raise NotImplementedError

    @method()
    def DisconnectProfile(self, uuid: "s") -> "":  # type: ignore # noqa: F722 F821
        raise NotImplementedError

    @method()
    def Pair(self) -> "":  # type: ignore # noqa: F722
        raise NotImplementedError

    @method()
    def CancelPairing(self) -> "":  # type: ignore # noqa: F722
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Address(self) -> "s":  # type: ignore # noqa: F722 F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def AddressType(self) -> "s":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Name(self) -> "s":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Icon(self) -> "s":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Class(self) -> "u":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Appearance(self) -> "q":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def UUIDs(self) -> "as":  # type: ignore # noqa: F722
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Paired(self) -> "b":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Bonded(self) -> "b":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Connected(self) -> "b":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property()
    def Trusted(self) -> "b":  # type: ignore # noqa: F821
        raise NotImplementedError

    @Trusted.setter  # type: ignore
    def Trusted(self, value: "b"):  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property()
    def Blocked(self) -> "b":  # type: ignore # noqa: F821
        raise NotImplementedError

    @Blocked.setter  # type: ignore
    def Blocked(self, value: "b"):  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property()
    def WakeAllowed(self) -> "b":  # type: ignore # noqa: F821
        raise NotImplementedError

    @WakeAllowed.setter  # type: ignore
    def WakeAllowed(self, value: "b"):  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property()
    def Alias(self) -> "s":  # type: ignore # noqa: F821
        raise NotImplementedError

    @Alias.setter  # type: ignore
    def Alias(self, value: "s"):  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Adapter(self) -> "o":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def LegacyPairing(self) -> "b":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def CablePairing(self) -> "b":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Modalias(self) -> "s":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def RSSI(self) -> "h":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def TxPower(self) -> "h":  # type: ignore # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def ManufacturerData(self) -> "a{hay}":  # type: ignore # noqa: F722
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def ServiceData(self) -> "a{say}":  # type: ignore # noqa: F722
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def ServicesResolved(self) -> "a{say}":  # type: ignore # noqa: F722
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def AdvertisingFlags(self) -> "ay":  # type: ignore # noqa: F722 F821
        raise NotImplementedError

    @classmethod
    def get_device(cls, bus: MessageBus, path: str) -> ProxyInterface:
        # Query the device object
        node: Node = Node.default(name=path)
        device_iface: Interface = Device1().introspect()
        node.interfaces.append(device_iface)

        object: ProxyObject = bus.get_proxy_object("org.bluez", path, node)
        return object.get_interface(DEVICE_INTERFACE)

    # For typing
    async def get_address(self) -> str:
        raise NotImplementedError
