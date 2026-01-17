import abc
import logging

from enum import Flag
from uuid import UUID
from typing import Callable, List, Optional, Set, Union, TYPE_CHECKING, cast

from bleak.backends.characteristic import (  # type: ignore
    BleakGATTCharacteristic,
    CharacteristicPropertyName,
)

from .attribute import GATTAttributePermissions
from .request import BlessGATTRequest
from .session import BlessGATTSession

if TYPE_CHECKING:
    from bless.backends.service import BlessGATTService
    from bless.backends.descriptor import BlessGATTDescriptor

logger = logging.getLogger(__name__)

GATTReadCallback = Callable[["BlessGATTCharacteristic", BlessGATTRequest], bytearray]
GATTWriteCallback = Callable[["BlessGATTCharacteristic", bytes, BlessGATTRequest], None]
GATTSubscribeCallback = Callable[["BlessGATTCharacteristic", BlessGATTSession], None]


class GATTCharacteristicProperties(Flag):
    broadcast = 0x0001
    read = 0x0002
    write_without_response = 0x0004
    write = 0x0008
    notify = 0x0010
    indicate = 0x0020
    authenticated_signed_writes = 0x0040
    extended_properties = 0x0080
    reliable_write = 0x0100
    writable_auxiliaries = 0x0200


_PROPERTY_FLAG_TO_NAME = [
    (GATTCharacteristicProperties.broadcast, "broadcast"),
    (GATTCharacteristicProperties.read, "read"),
    (GATTCharacteristicProperties.write_without_response, "write-without-response"),
    (GATTCharacteristicProperties.write, "write"),
    (GATTCharacteristicProperties.notify, "notify"),
    (GATTCharacteristicProperties.indicate, "indicate"),
    (
        GATTCharacteristicProperties.authenticated_signed_writes,
        "authenticated-signed-writes",
    ),
    (GATTCharacteristicProperties.extended_properties, "extended-properties"),
    (GATTCharacteristicProperties.reliable_write, "reliable-write"),
    (GATTCharacteristicProperties.writable_auxiliaries, "writable-auxiliaries"),
]


def _properties_to_bleak(
    properties: GATTCharacteristicProperties,
) -> List[CharacteristicPropertyName]:
    result: List[CharacteristicPropertyName] = []
    for flag, name in _PROPERTY_FLAG_TO_NAME:
        if properties & flag:
            result.append(cast(CharacteristicPropertyName, name))
    return result


class BlessGATTCharacteristic(BleakGATTCharacteristic):
    """
    Extension of the BleakGATTCharacteristic to allow for writable values
    """

    def __init__(
        self,
        uuid: Union[str, UUID],
        properties: GATTCharacteristicProperties,
        permissions: GATTAttributePermissions,
        value: Optional[bytearray],
        on_read: Optional[GATTReadCallback] = None,
        on_write: Optional[GATTWriteCallback] = None,
        on_subscribe: Optional[GATTSubscribeCallback] = None,
        on_unsubscribe: Optional[GATTSubscribeCallback] = None,
    ):
        """
        Instantiates a new GATT Characteristic but is not yet assigned to any
        service or application

        Parameters
        ----------
        uuid : Union[str, UUID]
            The string representation of the universal unique identifier for
            the characteristic or the actual UUID object
        properties : GATTCharacteristicProperties
            The properties that define the characteristics behavior
        permissions : GATTAttributePermissions
            Permissions that define the protection levels of the properties
        value : Optional[bytearray]
            The binary value of the characteristic
        on_read : Optional[GATTReadCallback]
            If defined, reads destined for this characteristic will be passed
            to this function
        on_write : Optional[GATTWriteCallback]
            If defined, writes destined for this characteristic will be passed
            to this function
        on_subscribe : Optional[GATTSubscribeCallback]
            If defined, subscriptions destined for this characteristic will be
            passed to this function
        on_unsubscribe : Optional[GATTSubscribeCallback]
            If defined, unsubscriptions destined for this characteristic will
            be passed to this function
        """
        self.on_read: Optional[GATTReadCallback] = on_read
        self.on_write: Optional[GATTWriteCallback] = on_write
        self.on_subscribe: Optional[GATTSubscribeCallback] = on_subscribe
        self.on_unsubscribe: Optional[GATTSubscribeCallback] = on_unsubscribe

        logger.debug(f"With on_read: {on_read}")
        if type(uuid) is str:
            uuid_str: str = cast(str, uuid)
            uuid = UUID(uuid_str)
        self._uuid: str = str(uuid)
        self._properties_flags: GATTCharacteristicProperties = properties
        self._properties: List[CharacteristicPropertyName] = _properties_to_bleak(
            properties
        )
        self._permissions: GATTAttributePermissions = permissions
        self._initial_value: Optional[bytearray] = value

    def __str__(self):
        """
        String output of this characteristic
        """
        return f"{self.uuid}: {self.description}"

    @abc.abstractmethod
    async def init(self, service: "BlessGATTService"):
        """
        Initializes the backend-specific characteristic object and stores it in
        self.obj
        """
        raise NotImplementedError()

    @property  # type: ignore
    @abc.abstractmethod
    def value(self) -> bytearray:
        """Value of this characteristic"""
        raise NotImplementedError()

    @value.setter  # type: ignore
    @abc.abstractmethod
    def value(self, val: bytearray):
        """Set the value of this characteristic"""
        raise NotImplementedError()

    def get_descriptor(
        self, specifier: Union[int, str, UUID]
    ) -> Optional["BlessGATTDescriptor"]:
        """Get a descriptor by handle or UUID."""
        return cast("BlessGATTDescriptor", super().get_descriptor(specifier))

    @property
    def subscribed_centrals(self) -> Set[str]:
        """
        Unique list of subscribed central IDs
        """
        raise NotImplementedError
