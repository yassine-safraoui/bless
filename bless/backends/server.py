import abc
import asyncio
import logging
import coloredlogs  # type: ignore

from uuid import UUID
from asyncio import AbstractEventLoop
from typing import Any, Dict, List, Optional, Set

from bless.backends.service import BlessGATTService
from bless.backends.advertisement import BlessAdvertisementData
from bless.backends.attribute import GATTAttributePermissions  # type: ignore
from bless.backends.characteristic import (  # type: ignore
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTReadCallback,
    GATTWriteCallback,
    GATTSubscribeCallback,
)
from bless.backends.descriptor import GATTDescriptorProperties  # type: ignore
from bless.backends.session import BlessGATTSession
from bless.backends.request import BlessGATTRequest

from bless.exceptions import BlessError

coloredlogs.install(
    level="DEBUG",
    logger=logging.getLogger('bless')
)
LOGGER = logging.getLogger(__name__)


class BaseBlessServer(abc.ABC):
    """
    The Server Interface for Bleak Backend

    Attributes
    ----------
    services : Optional[BleakGATTServiceCollection]
        Used to manage services and characteristics that this server advertises
    """

    def __init__(
        self,
        loop: Optional[AbstractEventLoop] = None,
        on_read: Optional[GATTReadCallback] = None,
        on_write: Optional[GATTWriteCallback] = None,
        on_subscribe: Optional[GATTSubscribeCallback] = None,
        on_unsubscribe: Optional[GATTSubscribeCallback] = None,
        **kwargs,
    ):
        self.loop: AbstractEventLoop = loop if loop else asyncio.get_event_loop()
        self.on_read: Optional[GATTReadCallback] = on_read
        self.on_write: Optional[GATTWriteCallback] = on_write
        self.on_subscribe: Optional[GATTSubscribeCallback] = on_subscribe
        self.on_unsubscribe: Optional[GATTSubscribeCallback] = on_unsubscribe

        self.services: Dict[str, BlessGATTService] = {}
        self._mtu: Optional[int] = None

    # Async Context managers

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    # Abstract Methods

    @abc.abstractmethod
    async def start(
        self, advertisement_data: Optional[BlessAdvertisementData] = None, **kwargs
    ) -> bool:
        """
        Start the server

        Parameters
        ----------
        advertisement_data : Optional[BlessAdvertisementData]
            Optional advertisement payload to customize backend advertising

        Returns
        -------
        bool
            Whether the server started successfully
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def stop(self) -> bool:
        """
        Stop the server

        Returns
        -------
        bool
            Whether the server stopped successfully
        """
        raise NotImplementedError()

    async def is_connected(self) -> bool:
        """
        Determine whether there are any connected central devices

        Returns
        -------
        bool
            Whether any peripheral devices are connected
        """
        return (
            len(
                set(
                    [
                        cid
                        for service in self.services.values()
                        for characteristic in service.characteristics
                        for cid in characteristic.subscribed_centrals
                    ]
                )
            )
            > 0
        )

    @abc.abstractmethod
    async def is_advertising(self) -> bool:
        """
        Determine whether the server is advertising

        Returns
        -------
        bool
            True if the server is advertising
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def add_new_service(self, uuid: str, primary: Optional[bool] = None):
        """
        Add a new GATT service to be hosted by the server

        Parameters
        ----------
        uuid : str
            The UUID for the service to add
        primary : Optional[bool]
            True if this is a primary service, False otherwise. If None,
            default behavior of the backend is used.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def add_new_characteristic(
        self,
        service_uuid: str,
        char_uuid: str,
        properties: GATTCharacteristicProperties,
        value: Optional[bytearray],
        permissions: GATTAttributePermissions,
        on_read: Optional[GATTReadCallback] = None,
        on_write: Optional[GATTWriteCallback] = None,
        on_subscribe: Optional[GATTSubscribeCallback] = None,
        on_unsubscribe: Optional[GATTSubscribeCallback] = None,
    ):
        """
        Add a new characteristic to be associated with the server

        Parameters
        ----------
        service_uuid : str
            The string representation of the UUID of the GATT service to which
            this new characteristic should belong
        char_uuid : str
            The string representation of the UUID of the characteristic
        properties : GATTCharacteristicProperties
            GATT Characteristic Flags that define the characteristic
        value : Optional[bytearray]
            A byterray representation of the value to be associated with the
            characteristic. Can be None if the characteristic is writable
        permissions : GATTAttributePermissions
            GATT flags that define the permissions for the characteristic
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
        raise NotImplementedError()

    @abc.abstractmethod
    async def add_new_descriptor(
        self,
        service_uuid: str,
        char_uuid: str,
        desc_uuid: str,
        properties: GATTDescriptorProperties,
        value: Optional[bytearray],
        permissions: GATTAttributePermissions,
    ):
        """
        Add a new characteristic to be associated with the server

        Parameters
        ----------
        service_uuid : str
            The string representation of the UUID of the GATT service to which
            this existing characteristic belongs
        char_uuid : str
            The string representation of the UUID of the GATT characteristic
            to which this new descriptor should belong
        desc_uuid : str
            The string representation of the UUID of the descriptor
        properties : GATTDescriptorProperties
            GATT Characteristic Flags that define the descriptor
        value : Optional[bytearray]
            A byterray representation of the value to be associated with the
            descriptor. Can be None if the descriptor is writable
        permissions : GATTAttributePermissions
            GATT flags that define the permissions for the descriptor
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def update_value(self, service_uuid: str, char_uuid: str) -> bool:
        """
        Update the characteristic value. This is different than using
        characteristic.set_value. This method ensures that subscribed devices
        receive notifications, assuming the characteristic in question is
        notifyable

        Parameters
        ----------
        service_uuid : str
            The string representation of the UUID for the service associated
            with the characteristic whose value is to be updated
        char_uuid : str
            The string representation of the UUID for the characteristic whose
            value is to be updated

        Returns
        -------
        bool
            Whether the characteristic value was successfully updated
        """
        raise NotImplementedError()

    def get_service(self, uuid: str) -> Optional[BlessGATTService]:
        """
        Retrieves the service whose UUID matches the string given

        Parameters
        ----------
        uuid : str
            The String representation of the uuid for the service

        Returns
        -------
        Optional[BlessGATTService]
            The service that matches the UUID. None if not found
        """
        uuid = str(UUID(uuid))
        potential_services: List[BlessGATTService] = [
            service
            for uuid_str, service in self.services.items()
            if service.uuid == uuid
        ]

        return potential_services[0] if len(potential_services) > 0 else None

    def get_characteristic(self, uuid: str) -> Optional[BlessGATTCharacteristic]:
        """
        Retrieves the characteristic whose UUID matches the string given.

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the characteristic to
            retrieve

        Returns
        -------
        BlessGATTCharacteristic
            The characteristic object
        """
        uuid = str(UUID(uuid))
        potentials: List[BlessGATTCharacteristic] = [
            self.services[service_uuid].get_characteristic(uuid)
            for service_uuid in self.services
            if self.services[service_uuid].get_characteristic(uuid) is not None
        ]
        try:
            return potentials[0]
        except KeyError:
            return None

    async def add_gatt(self, gatt_tree: Dict):
        """
        Uses the provided dictionary add all the services and characteristics

        Parameters
        ----------
        gatt_tree : Dict
            A dictionary of services and characteristics where the keys are the
            uuids and the attributes are the properties
        """
        for service_uuid, service_info in gatt_tree.items():
            await self.add_new_service(service_uuid, primary=True)
            for char_uuid, char_info in service_info.items():
                await self.add_new_characteristic(
                    service_uuid,
                    char_uuid,
                    char_info.get("Properties"),
                    char_info.get("Value"),
                    char_info.get("Permissions"),
                    char_info.get("OnRead"),
                    char_info.get("OnWrite"),
                    char_info.get("OnSubscribe"),
                    char_info.get("OnUnsubscribe"),
                )
                descriptors = char_info.get("Descriptors")
                if isinstance(descriptors, dict):
                    for desc_uuid, desc_info in descriptors.items():
                        await self.add_new_descriptor(
                            service_uuid,
                            char_uuid,
                            desc_uuid,
                            desc_info.get("Properties"),
                            desc_info.get("Value"),
                            desc_info.get("Permissions"),
                        )

    def _on_read(self, uuid: str, request: BlessGATTRequest) -> bytearray:
        """
        This function should be handed off to the subsequent backend bluetooth
        servers as a callback for incoming read requests on values for
        characteristics owned by our server. This function then hands off
        execution to the user-defiend callback functions

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the characteristic whose
            value is to be read
        request : BlessGATTRequest
            The read request

        Returns
        -------
        bytearray
            A bytearray value that represents the value for the characteristic
            requested
        """
        LOGGER.debug(f"Read request\n\tuuid: {uuid}\n\trequest: {request}")
        characteristic: Optional[BlessGATTCharacteristic] = self.get_characteristic(
            uuid
        )
        if not characteristic:
            raise BlessError("Invalid characteristic: {}".format(uuid))

        # handle MTU capture
        self.mtu = request.mtu

        # Route to characteristic read
        LOGGER.debug(f"on_read: {characteristic.on_read}")
        if characteristic.on_read is not None:
            LOGGER.debug("Characteristic Read!")
            return characteristic.on_read(characteristic, request)

        # Route to server defined read
        if self.on_read is not None:
            return self.on_read(characteristic, request)

        # Generic handling
        return characteristic.value

    def _on_write(self, uuid: str, value: Any, request: BlessGATTRequest) -> None:
        """
        Obtain the characteristic to write and pass on to the user-defined
        on_write

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the characteristic whose
            value is to be written
        value : Any
            The value to write to the characteristic
        request : BlessGATTRequest
            The write request data

        """
        LOGGER.debug(f"Write request\n\tuuid: {uuid}\n\trequest: {request}")
        characteristic: Optional[BlessGATTCharacteristic] = self.get_characteristic(
            uuid
        )
        if not characteristic:
            raise BlessError("Invalid characteristic: {}".format(uuid))

        # handle MTU capture
        self.mtu = request.mtu

        # Route to characteristic write
        if characteristic.on_write is not None:
            return characteristic.on_write(characteristic, value, request)

        # Route to server defined write
        if self.on_write is not None:
            return self.on_write(characteristic, value, request)

    def _on_subscribe(self, uuid: str, session: BlessGATTSession) -> None:
        """
        Obtain the characteristic to subscribe to and pass on to the
        user-defined on_subscribe

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the characteristic whose
            value is to be subscribed to
        session : BlessGATTSession
            The session object
        """
        LOGGER.debug(f"Subscribe request\n\tuuid: {uuid}\n\tsession: {session}")
        characteristic: Optional[BlessGATTCharacteristic] = self.get_characteristic(
            uuid
        )

        if characteristic is None:
            raise BlessError(f"Invalid characteristic: {uuid}")

        # handle MTU capture
        self.mtu = session.mtu

        # Route to characteristic subscription
        if characteristic.on_subscribe is not None:
            return characteristic.on_subscribe(characteristic, session)

        # Route to server defined subscription
        if self.on_subscribe is not None:
            return self.on_subscribe(characteristic, session)

    def _on_unsubscribe(self, uuid: str, session: BlessGATTSession) -> None:
        """
        Obtain the characteristic to unsubscribe from and pass on to the
        user-defined on_unsubscribe

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the characteristic whose
            value is to be unsubscribed from
        session : BlessGATTSession
            The session object
        """
        LOGGER.debug(f"Unsubscribe request\n\tuuid: {uuid}\n\tsession: {session}")
        characteristic: Optional[BlessGATTCharacteristic] = self.get_characteristic(
            uuid
        )

        if characteristic is None:
            raise BlessError(f"Invalid characteristic: {uuid}")

        # handle MTU capture
        self.mtu = session.mtu

        # Route to characteristic unsubscription
        if characteristic.on_unsubscribe is not None:
            return characteristic.on_unsubscribe(characteristic, session)

        # Route to server defined unsubscription
        if self.on_unsubscribe is not None:
            return self.on_unsubscribe(characteristic, session)

    # Aliases for backwards compatibility
    def read_request(self, uuid: str, request: BlessGATTRequest) -> bytearray:
        """
        Alias for `_on_read` for backwards compatibility
        """
        return self._on_read(uuid, request)

    def write_request(self, uuid: str, value: Any, request: BlessGATTRequest) -> None:
        """
        Alias for `_on_write` for backwards compatibility
        """
        return self._on_write(uuid, value, request)

    def subscribe_request(self, uuid: str, session: BlessGATTSession) -> None:
        """
        Alias for `_on_subscribe` for backwards compatibility
        """
        return self._on_subscribe(uuid, session)

    def unsubscribe_request(self, uuid: str, session: BlessGATTSession) -> None:
        """
        Alias for `_on_unsubscribe` for backwards compatibility
        """
        return self._on_unsubscribe(uuid, session)

    @property
    def read_request_func(self) -> Optional[GATTReadCallback]:
        """
        Return an instance of the function to handle incoming read requests

        Note
        ----
        This will be deprecated in version 0.4. Prefer using `on_read`.
        """
        return self.on_read

    @read_request_func.setter
    def read_request_func(self, func: GATTReadCallback):
        """
        Set the function to handle incoming read requests

        Note
        ----
        This will be deprecated in version 0.4. Prefer using `on_read`.
        """
        self.on_read = func

    @property
    def write_request_func(self) -> Optional[GATTWriteCallback]:
        """
        Return an instance of the function to handle incoming write requests

        Note
        ----
        This will be deprecated in version 0.4. Prefer using `on_write`.
        """
        return self.on_write

    @write_request_func.setter
    def write_request_func(self, func: GATTWriteCallback):
        """
        Set the function to handle incoming write requests

        Note
        ----
        This will be deprecated in version 0.4. Prefer using `on_write`.
        """
        self.on_write = func

    @property
    def mtu(self) -> Optional[int]:
        """
        The most recently observed MTU value for this server.
        """
        return self._mtu

    @mtu.setter
    def mtu(self, value: Optional[int]):
        """
        Set the MTU value for this server.
        """
        self._mtu = value

    @property
    def subscribed_centrals(self) -> Set[str]:
        """
        Unique list of subscribed central IDs across all characteristics.
        """
        return set(
            [
                central_id
                for service in self.services.values()
                for characteristic in service.characteristics
                for central_id in characteristic.subscribed_centrals
            ]
        )

    @property
    def subscribed_clients(self) -> Set[str]:
        """
        Alias for `subscribed_centrals`.
        """
        return self.subscribed_centrals

    @staticmethod
    def is_uuid(uuid: str) -> bool:
        """
        Check whether uuid is a valid uuid

        Parameters
        ----------
        uuid : str
            The string representation of the uuid to check

        Returns
        -------
        bool
            True if uuid is a valid UUID
        """
        try:
            UUID(uuid)
            return True
        except ValueError:
            return False
