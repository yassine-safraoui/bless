import abc
import asyncio
import logging

from uuid import UUID
from asyncio import AbstractEventLoop
from typing import Any, Callable, Dict, List, Optional, Set

from bless.backends.service import BlessGATTService
from bless.backends.advertisement import BlessAdvertisementData
from bless.backends.attribute import GATTAttributePermissions  # type: ignore
from bless.backends.characteristic import (  # type: ignore
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
)
from bless.backends.descriptor import GATTDescriptorProperties  # type: ignore

from bless.exceptions import BlessError

LOGGER = logging.getLogger(__name__)


class BaseBlessServer(abc.ABC):
    """
    The Server Interface for Bleak Backend

    Attributes
    ----------
    services : Optional[BleakGATTServiceCollection]
        Used to manage services and characteristics that this server advertises
    """

    def __init__(self, loop: Optional[AbstractEventLoop] = None, **kwargs):
        self.loop: AbstractEventLoop = loop if loop else asyncio.get_event_loop()

        self._callbacks: Dict[str, Callable[[Any], Any]] = {}

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

    @abc.abstractmethod
    async def is_connected(self) -> bool:
        """
        Determine whether there are any connected central devices

        Returns
        -------
        bool
            Whether any peripheral devices are connected
        """
        raise NotImplementedError()

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
    async def add_new_service(self, uuid: str):
        """
        Add a new GATT service to be hosted by the server

        Parameters
        ----------
        uuid : str
            The UUID for the service to add
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
            await self.add_new_service(service_uuid)
            for char_uuid, char_info in service_info.items():
                await self.add_new_characteristic(
                    service_uuid,
                    char_uuid,
                    char_info.get("Properties"),
                    char_info.get("Value"),
                    char_info.get("Permissions"),
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

    def read_request(self, uuid: str, options: Optional[Dict] = None) -> bytearray:
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

        Returns
        -------
        bytearray
            A bytearray value that represents the value for the characteristic
            requested
        """
        if options is not None:
            self._update_mtu_from_options(options)
        characteristic: Optional[BlessGATTCharacteristic] = self.get_characteristic(
            uuid
        )

        if not characteristic:
            raise BlessError("Invalid characteristic: {}".format(uuid))

        return self.on_read(characteristic)

    def write_request(
        self, uuid: str, value: Any, options: Optional[Dict] = None
    ) -> None:
        """
        Obtain the characteristic to write and pass on to the user-defined
        on_write

        """
        if options is not None:
            self._update_mtu_from_options(options)
        characteristic: Optional[BlessGATTCharacteristic] = self.get_characteristic(
            uuid
        )

        self.on_write(characteristic, value)

    def subscribe_request(self, uuid: str, options: Optional[Dict] = None) -> None:
        """
        Obtain the characteristic to subscribe to and pass on to the
        user-defined on_subscribe
        """
        LOGGER.debug(f"Subscribe_request\n\tuuid: {uuid}\n\toptions: {options}")
        characteristic: Optional[BlessGATTCharacteristic] = self.get_characteristic(
            uuid
        )

        if characteristic is None:
            raise BlessError(f"Invalid characteristic: {uuid}")

        if options is not None:
            self._update_mtu_from_options(options)

            if options.get("central_id") is not None:
                characteristic.add_subscription(options["central_id"])

        self.on_subscribe(characteristic)

    def unsubscribe_request(self, uuid: str, options: Optional[Dict] = None) -> None:
        """
        Obtain the characteristic to unsubscribe from and pass on to the
        user-defined on_unsubscribe
        """
        characteristic: Optional[BlessGATTCharacteristic] = self.get_characteristic(
            uuid
        )

        if characteristic is None:
            raise BlessError(f"Invalid characteristic: {uuid}")

        if options is not None:
            self._update_mtu_from_options(options)

            if options.get("central_id") is not None:
                characteristic.remove_subscription(options["central_id"])

        self.on_unsubscribe(characteristic)

    @property
    def on_read(self) -> Callable[[Any], Any]:
        """
        Alias for `read_request_func`.
        """
        func: Optional[Callable[[Any], Any]] = self._callbacks.get("read")
        if func is not None:
            return func
        else:
            raise BlessError("Server: Read Callback is undefined")

    @on_read.setter
    def on_read(self, func: Callable):
        """
        Alias for `read_request_func`.
        """
        self._callbacks["read"] = func

    @property
    def on_write(self) -> Callable:
        """
        Alias for `write_request_func`.
        """
        func: Optional[Callable[[Any], Any]] = self._callbacks.get("write")
        if func is not None:
            return func
        else:
            raise BlessError("Server: Write Callback is undefined")

    @on_write.setter
    def on_write(self, func: Callable):
        """
        Alias for `write_request_func`.
        """
        self._callbacks["write"] = func

    @property
    def on_subscribe(self) -> Callable:
        """
        Alias for `subscribe_request_func`.
        """
        func: Optional[Callable[[Any], Any]] = self._callbacks.get("subscribe")
        if func is not None:
            return func
        else:
            raise BlessError("Server: Subscribe Callback is undefined")

    @on_subscribe.setter
    def on_subscribe(self, func: Callable):
        """ """
        self._callbacks["subscribe"] = func

    @property
    def on_unsubscribe(self) -> Callable:
        """
        Alias for `unsubscribe_request_func`.
        """
        func: Optional[Callable[[Any], Any]] = self._callbacks.get("unsubscribe")
        if func is not None:
            return func
        else:
            raise BlessError("Server: Unsubscribe Callback is undefined")

    @on_unsubscribe.setter
    def on_unsubscribe(self, func: Callable):
        """ """
        self._callbacks["unsubscribe"] = func

    @property
    def read_request_func(self) -> Callable[[Any], Any]:
        """
        Return an instance of the function to handle incoming read requests

        Note
        ----
        This will be deprecated in version 0.4. Prefer using `on_read`.
        """
        return self.on_read

    @read_request_func.setter
    def read_request_func(self, func: Callable):
        """
        Set the function to handle incoming read requests

        Note
        ----
        This will be deprecated in version 0.4. Prefer using `on_read`.
        """
        self.on_read = func

    @property
    def write_request_func(self) -> Callable:
        """
        Return an instance of the function to handle incoming write requests

        Note
        ----
        This will be deprecated in version 0.4. Prefer using `on_write`.
        """
        return self.on_write

    @write_request_func.setter
    def write_request_func(self, func: Callable):
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

    @staticmethod
    def _coerce_mtu_value(value: Any) -> Optional[int]:
        if value is None:
            return None
        if hasattr(value, "value"):
            return BaseBlessServer._coerce_mtu_value(value.value)
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _update_mtu_from_options(self, options: Dict[str, Any]) -> None:
        mtu_value = self._coerce_mtu_value(options.get("mtu"))
        if mtu_value is not None:
            self._mtu = mtu_value

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

    def _normalize_uuid(self, uuid: str) -> str:
        try:
            return str(UUID(uuid))
        except ValueError:
            return uuid

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
