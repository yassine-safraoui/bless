from bleak.backends.bluezdbus.defs import DEVICE_INTERFACE
from dbus_next.constants import PropertyAccess
from dbus_next.service import ServiceInterface, method, dbus_property


class Device1(ServiceInterface):

    interface_name: str = DEVICE_INTERFACE

    def __init__(self):
        super().__init__(self.interface_name)

    @method()
    def Connect(self) -> "":  # noqa: F722
        raise NotImplementedError

    @method()
    def Disconnect(self) -> "":  # noqa: F722
        raise NotImplementedError

    @method()
    def ConnectProfile(self, uuid: "s") -> "":  # noqa: F722 F821
        raise NotImplementedError

    @method()
    def DisconnectProfile(self, uuid: "s") -> "":  # noqa: F722 F821
        raise NotImplementedError

    @method()
    def Pair(self) -> "":  # noqa: F722
        raise NotImplementedError

    @method()
    def CancelPairing(self) -> "":  # noqa: F722
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Address(self) -> "s":  # noqa: F722 F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def AddressType(self) -> "s":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Name(self) -> "s":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Icon(self) -> "s":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Class(self) -> "u":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Appearance(self) -> "q":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def UUIDs(self) -> "as":  # noqa: F722
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Paired(self) -> "b":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Bonded(self) -> "b":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Connected(self) -> "b":  # noqa: F821
        raise NotImplementedError

    @dbus_property()
    def Trusted(self) -> "b":  # noqa: F821
        raise NotImplementedError

    @Trusted.setter
    def Trusted(self, value: "b"):  # noqa: F821
        raise NotImplementedError

    @dbus_property()
    def Blocked(self) -> "b":  # noqa: F821
        raise NotImplementedError

    @Blocked.setter
    def Blocked(self, value: "b"):  # noqa: F821
        raise NotImplementedError

    @dbus_property()
    def WakeAllowed(self) -> "b":  # noqa: F821
        raise NotImplementedError

    @WakeAllowed.setter
    def WakeAllowed(self, value: "b"):  # noqa: F821
        raise NotImplementedError

    @dbus_property()
    def Alias(self) -> "s":  # noqa: F821
        raise NotImplementedError

    @Alias.setter
    def Alias(self, value: "s"):  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Adapter(self) -> "o":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def LegacyPairing(self) -> "b":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def CablePairing(self) -> "b":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def Modalias(self) -> "s":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def RSSI(self) -> "h":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def TxPower(self) -> "h":  # noqa: F821
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def ManufacturerData(self) -> "a{hay}":  # noqa: F722
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def ServiceData(self) -> "a{say}":  # noqa: F722
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def ServicesResolved(self) -> "a{say}":  # noqa: F722
        raise NotImplementedError

    @dbus_property(access=PropertyAccess.READ)
    def AdvertisingFlags(self) -> "ay":  # noqa: F722 F821
        raise NotImplementedError
