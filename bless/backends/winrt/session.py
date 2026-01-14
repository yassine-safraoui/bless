from typing import cast
from winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
    GattSubscribedClient,
)

from ..session import BlessGATTSession


class BlessGATTSessionWinRT(BlessGATTSession):

    @property
    def subscribed_client(self) -> GattSubscribedClient:
        return cast(GattSubscribedClient, self.obj)

    @property
    def device_id(self) -> str:
        return self.subscribed_client.session.device_id.id

    @property
    def mtu(self) -> int:
        return self.subscribed_client.session.max_pdu_size
