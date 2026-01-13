from uuid import UUID
from typing import Mapping, Optional, Union, cast, TYPE_CHECKING

from bleak.backends.service import BleakGATTService  # type: ignore
from bless.backends.bluezdbus.dbus.service import BlueZGattService
from bless.backends.service import BlessGATTService as BaseBlessGATTService
from bless.backends.server import BaseBlessServer

if TYPE_CHECKING:
    from bless.backends.bluezdbus.server import BlessServerBlueZDBus

    from ..characteristic import BlessGATTCharacteristic


class BlessGATTServiceBlueZDBus(BaseBlessGATTService, BleakGATTService):
    """ "
    GATT service implementation for the BlueZ backend
    """

    def __init__(self, uuid: Union[str, UUID], primary: Optional[bool] = None):
        """
        Initialize the Bless GATT Service

        Parameters
        ----------
        uuid : Union[str, UUID]
            The UUID to assign to the service
        primary : Optional[bool]
            True if this is a primary service, False otherwise. If None,
            default behavior of the backend is used which is only the first
            service added is primary.
        """
        BaseBlessGATTService.__init__(self, uuid, primary)
        self._characteristics: Mapping[int, BlessGATTCharacteristic] = (
            {}  # type: ignore[assignment]
        )
        self.__handle = 0
        self.__path = ""

    async def init(self, server: "BaseBlessServer"):
        """
        Initialize the underlying bluez gatt service

        Parameters
        ----------
        server: BaseBlessServer
            The server to assign the service to
        """
        bluez_server: "BlessServerBlueZDBus" = cast("BlessServerBlueZDBus", server)
        gatt_service: BlueZGattService = await bluez_server.app.add_service(
            self._uuid, primary=self._primary
        )

        # Store the BlueZ GATT service
        self.gatt = gatt_service
        self.__path = gatt_service.path

        # Set attributes expected by BleakGATTService
        self.obj = gatt_service  # The backend-specific object
        self._handle = 0  # Handle will be assigned by BlueZ

    @property
    def handle(self) -> int:
        """The integer handle of the service"""
        return self.__handle

    @property
    def uuid(self) -> str:
        """UUID for this service"""
        return self._uuid

    @property
    def description(self) -> str:
        """Description of this service"""
        return f"Service {self._uuid}"

    @property
    def path(self):
        return self.__path
