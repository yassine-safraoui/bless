import abc

from uuid import UUID
from typing import Optional, List, Union, cast, TYPE_CHECKING
from bleak.backends.service import BleakGATTService  # type: ignore

if TYPE_CHECKING:
    from bless.backends.server import BaseBlessServer
    from bless.backends.characteristic import BlessGATTCharacteristic


class BlessGATTService(BleakGATTService):
    """
    GATT Service object for Bless
    """

    def __init__(self, uuid: Union[str, UUID], primary: Optional[bool] = None):
        """
        Instantiates a new GATT Service but is not yet assigned to any
        application

        Parameters
        ----------
        uuid : Union[str, UUID]
            The uuid of the service
        primary : Optional[bool]
            True if this is a primary service, False otherwise. If None, default
            behavior of the backend is used.
        """
        if type(uuid) is str:
            uuid_str: str = cast(str, uuid)
            uuid = UUID(uuid_str)
        self._uuid: str = str(uuid)
        self._primary = primary
        self._characteristics: dict[int, BlessGATTCharacteristic] = {}  # type: ignore

    @abc.abstractmethod
    async def init(self, server: "BaseBlessServer"):
        """
        Initialize the backend specific service object

        Parameteres
        -----------
        server: BlessServer
            The server to assign the service to
        """
        raise NotImplementedError()

    def get_characteristic(self, uuid: Union[str, UUID]) -> "BlessGATTCharacteristic":
        return cast("BlessGATTCharacteristic", super().get_characteristic(uuid))

    def add_characteristic(
        self, characteristic: "BlessGATTCharacteristic"  # type: ignore[override]
    ):
        """Add a characteristic to this service"""
        handle = len(self._characteristics)
        self._characteristics[handle] = characteristic

    @property
    def characteristics(  # type: ignore[override]
        self,
    ) -> List["BlessGATTCharacteristic"]:
        return cast(list["BlessGATTCharacteristic"], super().characteristics)
