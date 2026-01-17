from abc import abstractmethod
from typing import Any, Dict


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

    def __str__(self) -> str:
        return f"BlessGATTSession({self.to_dict()})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "central_id": self.central_id,
            "mtu": self.mtu,
        }

    @property
    @abstractmethod
    def central_id(self) -> str:
        """
        The central ID of this session
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def mtu(self) -> int:
        """
        The maximum transfer unit
        """
        raise NotImplementedError
