from abc import abstractmethod
from typing import Any


class BlessGATTSession:
    """
    Represents a session established between a central and a peripheral
    during a subscription
    """

    def __init__(self, obj: Any):
        """
        Parameters
        ----------
        obj : Any
            The backend-specific session object
        """
        self.obj: Any = obj

    @property
    @abstractmethod
    def device_id(self) -> str:
        """
        The device ID of this session
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def mtu(self) -> int:
        """
        The maximum transfer unit
        """
        raise NotImplementedError
