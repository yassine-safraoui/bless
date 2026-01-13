from uuid import UUID
from typing import Optional, Union, Dict

from CoreBluetooth import CBMutableService, CBUUID  # type: ignore

from bleak.backends.service import BleakGATTService  # type: ignore

from bless.backends.service import BlessGATTService as BaseBlessGATTService
from bless.backends.server import BaseBlessServer

from ..characteristic import BlessGATTCharacteristic


class BlessGATTServiceCoreBluetooth(BaseBlessGATTService, BleakGATTService):
    """
    GATT Characteristic implementation for the CoreBluetooth backend
    """

    def __init__(self, uuid: Union[str, UUID], primary: Optional[bool] = None):
        """
        New Bless Service for macOS

        Parameters
        ----------
        uuid: Union[str, UUID]
            The uuid to assign to the service
        primary : Optional[bool]
            True if this is a primary service, False otherwise. If None, default
            behavior of the backend is used which is that all services are primary.
        """
        BaseBlessGATTService.__init__(self, uuid, primary)
        self.__handle = 0
        self._characteristics: Dict[int, BlessGATTCharacteristic] = {}  # type: ignore
        self._cb_service = None

    async def init(self, server: "BaseBlessServer"):
        """
        Initailize the CoreBluetooth Service object
        """
        service_uuid: CBUUID = CBUUID.alloc().initWithString_(self._uuid)
        cb_service: CBMutableService = CBMutableService.alloc().initWithType_primary_(
            service_uuid, True if self._primary is None else self._primary
        )

        # Store the CoreBluetooth service
        self._cb_service = cb_service
        self.obj = cb_service
        self._handle = 0

    @property
    def handle(self) -> int:
        """The integer handle of this service"""
        return self.__handle

    @property
    def uuid(self) -> str:
        """UUID for this service."""
        if self._cb_service is not None:
            return self._cb_service.UUID().UUIDString().lower()
        return self._uuid

    @property
    def description(self) -> str:
        """Description of this service"""
        return f"Service {self.uuid}"
