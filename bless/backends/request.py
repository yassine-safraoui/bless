from abc import abstractmethod
from typing import Any, Dict, Optional


class BlessGATTRequest:

    def __init__(self, obj: Any):
        """
        Parameters
        ----------
        obj : Any
            The backend-specific request object
        """
        self.obj: Any = obj

    def __str__(self) -> str:
        return f"BlessGATTRequest({self.to_dict()})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "central_id": self.central_id,
            "mtu": self.mtu,
            "offset": self.offset,
            "response_requested": self.response_requested,
        }

    @property
    @abstractmethod
    def central_id(self) -> str:
        """
        The id of the central that made the request
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def mtu(self) -> int:
        """
        The maximum transfer unit
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def offset(self) -> int:
        """
        The offset of the characteristic value to begin reading or writing from
        in bytes
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def response_requested(self) -> Optional[bool]:
        """
        Whether a response is requested for write requests
        """
        raise NotImplementedError
