import asyncio
import logging

import sys
from uuid import UUID
from threading import Event
from asyncio.events import AbstractEventLoop
from typing import Optional, List, Any, cast, Set

from bless.backends.server import BaseBlessServer  # type: ignore
from bless.backends.advertisement import BlessAdvertisementData
from bless.backends.attribute import (  # type: ignore
    GATTAttributePermissions,
)
from bless.backends.characteristic import (  # type: ignore
    GATTCharacteristicProperties,
)
from bless.backends.descriptor import GATTDescriptorProperties
from bless.backends.winrt.service import BlessGATTServiceWinRT
from bless.backends.winrt.characteristic import (  # type: ignore
    BlessGATTCharacteristicWinRT,
)
from bless.backends.winrt.descriptor import BlessGATTDescriptorWinRT  # type: ignore

from bless.backends.winrt.ble import BLEAdapter

from .request import BlessGATTRequestWinRT
from .session import BlessGATTSessionWinRT

# CLR imports
# Import of Bleak CLR->UWP Bridge.
# from BleakBridge import Bridge

# Import of other CLR components needed.
if sys.version_info >= (3, 12):
    from winrt.windows.foundation import Deferral  # type: ignore

    from winrt.windows.storage.streams import DataReader, DataWriter  # type: ignore

    from winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattWriteOption,
        GattServiceProvider,
        GattLocalCharacteristic,
        GattServiceProviderAdvertisingParameters,
        GattServiceProviderAdvertisementStatusChangedEventArgs as StatusChangeEvent,  # noqa: E501
        GattReadRequestedEventArgs,
        GattReadRequest,
        GattWriteRequestedEventArgs,
        GattWriteRequest,
        GattSession,
        GattSubscribedClient,
    )
else:
    from bleak_winrt.windows.foundation import Deferral  # type: ignore

    from bleak_winrt.windows.storage.streams import (  # type: ignore
        DataReader,
        DataWriter,
    )

    from bleak_winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattWriteOption,
        GattServiceProvider,
        GattLocalCharacteristic,
        GattServiceProviderAdvertisingParameters,
        GattServiceProviderAdvertisementStatusChangedEventArgs as StatusChangeEvent,  # noqa: E501
        GattReadRequestedEventArgs,
        GattReadRequest,
        GattWriteRequestedEventArgs,
        GattWriteRequest,
        GattSession,
        GattSubscribedClient,
    )

logger = logging.getLogger(__name__)


class Request:
    def __init__(self):
        self._obj = None


class BlessServerWinRT(BaseBlessServer):
    """
    WinRT Implementation of BlessServer

    Attributes
    ----------
    name : str
        The name of the server to advertise
    services : Dict[str, BlessGATTServiceWinRT]
        A dictionary of services to be advertised by this server
    """

    def __init__(
        self,
        name: str,
        loop: Optional[AbstractEventLoop] = None,
        name_overwrite: bool = False,
        **kwargs,
    ):
        """
        Initialize a new instance of a Bless BLE peripheral (server) for WinRT

        Parameters
        ----------
        name : str
            The display name that central device uses when your service is
            identified. The `local_name`. By default, windows machines use the
            name of the computer. This can can be used instead if name_overwrite
            is set to True.
        loop : AbstractEventLoop
            An asyncio loop to run the server on
        name_overwrite : bool
            Defaults to false. If true, will cause the bluetooth system module
            to be renamed to self.name
        """
        super(BlessServerWinRT, self).__init__(loop=loop, **kwargs)

        self.name: str = name

        self._service_provider: Optional[GattServiceProvider] = None
        self._subscribed_clients: Dict[str, Set[GAttSubscribedClient]] = {}

        self._advertising: bool = False
        self._advertising_started: Event = Event()
        self._adapter: BLEAdapter = BLEAdapter()
        self._name_overwrite: bool = name_overwrite

    async def start(
        self: "BlessServerWinRT",
        advertisement_data: Optional[BlessAdvertisementData] = None,
        **kwargs,
    ):
        """
        Start the server

        Parameters
        ----------
        timeout : float
            Floating point decimal in seconds for how long to wait for the
            on-board bluetooth module to power on
        advertisement_data : Optional[BlessAdvertisementData]
            Optional advertisement payload to customize local name and
            connectable/discoverable settings
        """

        if advertisement_data and advertisement_data.local_name is not None:
            self._adapter.set_local_name(advertisement_data.local_name)
        elif self._name_overwrite:
            self._adapter.set_local_name(self.name)

        adv_parameters: GattServiceProviderAdvertisingParameters = (
            GattServiceProviderAdvertisingParameters()
        )
        if advertisement_data and advertisement_data.is_discoverable is not None:
            adv_parameters.is_discoverable = advertisement_data.is_discoverable
        else:
            adv_parameters.is_discoverable = True
        if advertisement_data and advertisement_data.is_connectable is not None:
            adv_parameters.is_connectable = advertisement_data.is_connectable
        else:
            adv_parameters.is_connectable = True

        for uuid, service in self.services.items():
            winrt_service: BlessGATTServiceWinRT = cast(BlessGATTServiceWinRT, service)
            service_provider = winrt_service.service_provider
            assert service_provider is not None
            service_provider.start_advertising(adv_parameters)
        self._advertising = True
        self._advertising_started.wait()

    async def stop(self: "BlessServerWinRT"):
        """
        Stop the server
        """
        for uuid, service in self.services.items():
            winrt_service: BlessGATTServiceWinRT = cast(BlessGATTServiceWinRT, service)
            service_provider = winrt_service.service_provider
            assert service_provider is not None
            service_provider.stop_advertising()
        self._advertising = False

    async def is_advertising(self) -> bool:
        """
        Determine whether the server is advertising

        Returns
        -------
        bool
            True if advertising
        """
        all_services_advertising: bool = False
        for uuid, service in self.services.items():
            winrt_service: BlessGATTServiceWinRT = cast(BlessGATTServiceWinRT, service)
            service_provider = winrt_service.service_provider
            assert service_provider is not None
            service_is_advertising: bool = service_provider.advertisement_status == 2
            all_services_advertising = (
                all_services_advertising or service_is_advertising
            )

        return self._advertising and all_services_advertising

    def _status_update(
        self,
        service_provider: Optional[GattServiceProvider],
        args: Optional[StatusChangeEvent],
    ) -> None:
        """
        Callback function for the service provider to trigger when the
        advertizing status changes

        Parameters
        ----------
        service_provider : GattServiceProvider
            The service provider whose advertising status changed

        args : GattServiceProviderAdvertisementStatusChangedEventArgs
            The arguments associated with the status change
            See
            [here](https://docs.microsoft.com/en-us/uwp/api/windows.devices.bluetooth.genericattributeprofile.gattserviceprovideradvertisementstatuschangedeventargs.status?view=winrt-19041)
        """
        if args is not None and args.status == 2:
            self._advertising_started.set()

    async def add_new_service(self, uuid: str, primary: Optional[bool] = None):
        """
        Generate a new service to be associated with the server

        Parameters
        ----------
        uuid : str
            The string representation of the UUID of the service to be added
        primary : Optional[bool]
            True if this is a primary service, False otherwise. If None,
            default behavior of the backend is used.
            For WinRT, it seems to only allow primary services to be added so
            this is currently unused.
        """
        logger.debug("Creating a new service with uuid: {}".format(uuid))
        logger.debug("Adding service to server with uuid {}".format(uuid))
        service: BlessGATTServiceWinRT = BlessGATTServiceWinRT(uuid, primary)
        await service.init(self)
        self.services[service.uuid] = service

    async def add_new_characteristic(
        self,
        service_uuid: str,
        char_uuid: str,
        properties: GATTCharacteristicProperties,
        value: Optional[bytearray],
        permissions: GATTAttributePermissions,
    ):
        """
        Generate a new characteristic to be associated with the server

        Parameters
        ----------
        service_uuid : str
            The string representation of the uuid of the service to associate
            the new characteristic with
        char_uuid : str
            The string representation of the uuid of the new characteristic
        properties : GATTCharacteristicProperties
            The flags for the characteristic
        value : Optional[bytearray]
            The initial value for the characteristic
        permissions : GATTAttributePermissions
            The permissions for the characteristic
        """

        service_uuid = str(UUID(service_uuid))
        char_uuid = str(UUID(char_uuid))
        service: BlessGATTServiceWinRT = cast(
            BlessGATTServiceWinRT, self.services[service_uuid]
        )
        characteristic: BlessGATTCharacteristicWinRT = BlessGATTCharacteristicWinRT(
            char_uuid, properties, permissions, value
        )
        await characteristic.init(service)

        # All characteristics route through to:
        #   1. Backend-specific `__on_<verb>`
        #   2. Bless server `_on_<verb>`
        #   3. User-defined `on_<verb>`
        characteristic.obj.add_read_requested(self.__on_read)
        characteristic.obj.add_write_requested(self.__on_write)
        characteristic.obj.add_subscribed_clients_changed(self.__on_subscribe)
        service.add_characteristic(characteristic)

    async def add_new_descriptor(
        self,
        service_uuid: str,
        char_uuid: str,
        descriptor_uuid: str,
        properties: GATTDescriptorProperties,
        value: Optional[bytearray],
        permissions: GATTAttributePermissions,
    ):
        logger.debug("Creating a new descriptor with uuid: {}".format(descriptor_uuid))
        service_uuid = str(UUID(service_uuid))
        char_uuid = str(UUID(char_uuid))
        service = cast(Optional[BlessGATTServiceWinRT], self.get_service(service_uuid))
        if service is None:
            return
        characteristic_obj = service.get_characteristic(char_uuid)
        if characteristic_obj is None:
            return
        characteristic: BlessGATTCharacteristicWinRT = cast(
            BlessGATTCharacteristicWinRT, characteristic_obj
        )
        descriptor: BlessGATTDescriptorWinRT = BlessGATTDescriptorWinRT(
            descriptor_uuid, properties, permissions, value
        )
        await descriptor.init(characteristic)

    def update_value(self, service_uuid: str, char_uuid: str) -> bool:
        """
        Update the characteristic value. This is different than using
        characteristic.set_value. This send notifications to subscribed
        central devices.

        Parameters
        ----------
        service_uuid : str
            The string representation of the UUID for the service associated
            with the characteristic to be added
        char_uuid : str
            The string representation of the UUID for the characteristic to be
            added

        Returns
        -------
        bool
            Whether the value was successfully updated
        """
        service_uuid = str(UUID(service_uuid))
        char_uuid = str(UUID(char_uuid))
        service: Optional[BlessGATTServiceWinRT] = cast(
            Optional[BlessGATTServiceWinRT], self.get_service(service_uuid)
        )
        if service is None:
            return False
        characteristic: BlessGATTCharacteristicWinRT = cast(
            BlessGATTCharacteristicWinRT, service.get_characteristic(char_uuid)
        )
        value: bytes = characteristic.value
        value = value if value is not None else b"\x00"
        writer: DataWriter = DataWriter()
        writer.write_bytes(value)
        characteristic.obj.notify_value_async(writer.detach_buffer())

        return True

    def __on_read(
        self, sender: GattLocalCharacteristic, args: GattReadRequestedEventArgs
    ):
        """
        The is triggered by pythonnet when windows receives a read request for
        a given characteristic

        Parameters
        ----------
        sender : GattLocalCharacteristic
            The characteristic Gatt object whose value was requested
        args : GattReadRequestedEventArgs
            Arguments for the read request
        """
        logger.debug("Reading Characteristic")
        deferral: Optional[Deferral] = args.get_deferral()
        if deferral is None:
            return

        # Get the session
        session: GattSession = args.session

        # Get the request object
        logger.debug("Getting request object {}".format(self))
        request: GattReadRequest

        async def f():
            nonlocal request
            request = await args.get_request_async()

        asyncio.new_event_loop().run_until_complete(f())
        logger.debug("Got request object {}".format(request))

        # pass up to server-side callback
        value: bytearray = self._on_read(
            str(sender.uuid), BlessGATTRequestWinRT((session, request))
        )

        logger.debug(f"Current Characteristic value {value}")
        value = value if value is not None else b"\x00"
        writer: DataWriter = DataWriter()
        writer.write_bytes(value)
        request.respond_with_value(writer.detach_buffer())
        deferral.complete()

    def __on_write(
        self, sender: GattLocalCharacteristic, args: GattWriteRequestedEventArgs
    ):
        """
        Called by pythonnet when a write request is submitted

        Parameters
        ----------
        sender : GattLocalCharacteristic
            The object representation of the gatt characteristic whose value we
            should write to
        args : GattWriteRequestedEventArgs
            The event arguments for the write request
        """

        deferral: Optional[Deferral] = args.get_deferral()
        if deferral is None:
            return

        # Get the session
        session: GattSession = args.session

        # Get the request
        request: GattWriteRequest

        async def f():
            nonlocal request
            request = await args.get_request_async()

        asyncio.new_event_loop().run_until_complete(f())
        logger.debug("Request value: {}".format(request.value))

        # extrac the bytarray value
        reader: Optional[DataReader] = DataReader.from_buffer(request.value)
        if reader is None:
            return
        n_bytes: int = reader.unconsumed_buffer_length
        value: bytearray = bytearray()
        for n in range(0, n_bytes):
            next_byte: int = reader.read_byte()
            value.append(next_byte)
        logger.debug("Written Value: {}".format(value))

        # Pass up to server
        self._on_write(
            str(sender.uuid), value, BlessGATTRequestWinRT((session, request))
        )

        if request.option == GattWriteOption.WRITE_WITH_RESPONSE:
            request.respond()

        logger.debug("Write Complete")
        deferral.complete()

    def __on_subscribe(self, sender: GattLocalCharacteristic, args: Any):
        """
        Called when a characteristic is subscribed to or unsubscribed from

        Because there is no "unsubscribe", we track when central devices come
        and go to determine whether to call upstream subscribe or unsubscribe
        callbacks

        Parameters
        ----------
        sender : GattLocalCharacteristic
            The characteristic object associated with the characteristic to
            which the device would like to subscribe
        args : Object
            Additional arguments to use for the subscription
        """
        new_clients: List[GattSubscribedClient] = (
            list([]) if sender.subscribed_clients is None else sender.subscribed_clients
        )

        prev_ids: Set[str] = set(
            [
                str(client.session.device_id.id)
                for client in self._subscribed_clients.get(str(sender.uuid), set())
            ]
        )

        new_ids: Set[str] = {str(client.session.device_id.id) for client in new_clients}

        # compute added and removed
        added_ids: Set[str] = new_ids - prev_ids
        removed_ids: Set[str] = prev_ids - new_ids
        logger.debug(f"Added: {added_ids}")
        logger.debug(f"removed: {removed_ids}")

        # convert to client objects
        added_clients: List[GattSubscribedClient] = [
            client
            for client in new_clients
            if str(client.session.device_id.id) in added_ids
        ]
        removed_clients: List[GattSubscribedClient] = [
            client
            for client in self._subscribed_clients[str(sender.uuid)]
            if str(client.session.device_id.id) in removed_ids
        ]

        # Handle Subscriptions
        for client in added_clients:
            self._on_subscribe(str(sender.uuid), BlessGATTSessionWinRT(client))

        for client in removed_clients:
            self._on_unsubscribe(str(sender.uuid), BlessGATTSessionWinRT(client))

        # Update Subscribed Clients
        self._subscribed_clients[str(sender.uuid)] = new_clients
