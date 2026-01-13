import sys
import uuid
import pytest
import asyncio
import os
import aioconsole  # type: ignore

import numpy as np  # type: ignore

from typing import Optional, List

from bless.backends.characteristic import BlessGATTCharacteristic  # type: ignore

# Eventually should be removed when MacOS, Windows, and Linux are added
if sys.platform not in ["darwin", "linux", "win32"]:
    pytest.skip(
        "Currently, testing only works on macOS, linux, and windows",
        allow_module_level=True,
    )

from bless import BlessServer  # type: ignore  # noqa: E402
from bless.backends.attribute import (  # noqa: E402
    GATTAttributePermissions,
)
from bless.backends.characteristic import (  # noqa: E402
    GATTCharacteristicProperties,
)

hardware_double = pytest.mark.skipif("os.environ.get('TEST_HARDWARE') != '2'")
use_encrypted = os.environ.get("TEST_ENCRYPTED") is not None


@hardware_double
class TestBlessServerMultiClient:
    """
    Hardware test for two simultaneous connected clients.

    Runs when TEST_HARDWARE=2.
    """

    def gen_hex_pairs(self) -> str:
        hex_words: List[str] = [
            "DEAD",
            "FACE",
            "BABE",
            "CAFE",
            "FADE",
            "BAD",
            "DAD",
            "ACE",
            "BED",
        ]
        rng: np.random._generator.Generator = np.random.default_rng()  # type: ignore
        return "".join(rng.choice(hex_words, 2, replace=False))

    def hex_to_byte(self, hexstr: str) -> bytearray:
        return bytearray(
            int(f"0x{hexstr}", 16).to_bytes(
                length=int(np.ceil(len(hexstr) / 2)), byteorder="big"
            )
        )

    def byte_to_hex(self, b: bytearray) -> str:
        return "".join([hex(x)[2:] for x in b]).upper()

    def subscribed_client_count(self, server: BlessServer) -> Optional[int]:
        if hasattr(server, "_subscribed_clients"):
            return len(getattr(server, "_subscribed_clients"))
        if hasattr(server, "peripheral_manager_delegate"):
            delegate = getattr(server, "peripheral_manager_delegate")
            subscriptions = getattr(delegate, "_central_subscriptions", None)
            if isinstance(subscriptions, dict):
                return len(subscriptions)
        app = getattr(server, "app", None)
        if app is not None:
            subscribed = getattr(app, "subscribed_characteristics", None)
            if isinstance(subscribed, list):
                return len(subscribed)
        return None

    @pytest.mark.asyncio
    async def test_server_two_clients(self):
        # Initialize
        server: BlessServer = BlessServer("Test Server")

        # setup a service
        service_uuid: str = str(uuid.uuid4())
        await server.add_new_service(service_uuid)

        assert len(server.services) > 0

        # setup a characteristic for the service
        char_uuid: str = str(uuid.uuid4())
        char_flags: GATTCharacteristicProperties = (
            GATTCharacteristicProperties.read
            | GATTCharacteristicProperties.write
            | GATTCharacteristicProperties.notify
        )
        value: Optional[bytearray] = None
        permissions: GATTAttributePermissions = (
            GATTAttributePermissions.readable | GATTAttributePermissions.writable
        )

        if use_encrypted:
            print("\nEncryption has been enabled, ensure that you are bonded")
            permissions = (
                GATTAttributePermissions.read_encryption_required
                | GATTAttributePermissions.write_encryption_required
            )

        await server.add_new_characteristic(
            service_uuid, char_uuid, char_flags, value, permissions
        )

        assert server.services[service_uuid].get_characteristic(char_uuid)

        # Set up read, write, and subscribe callbacks
        def read(characteristic: BlessGATTCharacteristic) -> bytearray:
            return characteristic.value

        def write(characteristic: BlessGATTCharacteristic, value: bytearray):
            characteristic.value = value  # type: ignore

        def subscribe(characteristic: BlessGATTCharacteristic) -> None:
            print("Subscribed")

        def unsubscribe(characteristic: BlessGATTCharacteristic) -> None:
            print("Unsubscribed")

        server.on_read = read
        server.on_write = write
        server.on_subscribe = subscribe
        server.on_unsubscribe = unsubscribe

        # Start advertising
        assert await server.is_advertising() is False

        await server.start()

        assert await server.is_advertising() is True

        # Subscribe clients sequentially
        assert await server.is_connected() is False

        print(
            "\nPlease connect the first client and "
            + f"subscribe to characteristic {char_uuid}"
        )
        await aioconsole.ainput("Press enter when the first client is ready...")

        count = self.subscribed_client_count(server)
        if count is None:
            pytest.skip("Backend does not expose per-client subscription counts")
        assert count == 1

        print(
            "\nPlease connect the second client and "
            + f"subscribe to characteristic {char_uuid}"
        )
        await aioconsole.ainput("Press enter when the second client is ready...")

        assert self.subscribed_client_count(server) == 2

        # Read Test
        hex_val: str = self.gen_hex_pairs()
        server.get_characteristic(char_uuid).value = self.hex_to_byte(hex_val)
        print(
            "Trigger a read command from either client and "
            + "enter the capital letters you retrieve below"
        )
        entered_value = await aioconsole.ainput("Value: ")
        assert entered_value == hex_val

        # Write Test
        hex_val = self.gen_hex_pairs()
        print(f"Set the characteristic to this value from either client: {hex_val}")
        await aioconsole.ainput("Press enter when ready...")
        entered_value = self.byte_to_hex(server.get_characteristic(char_uuid).value)
        assert entered_value == hex_val

        # Notify Test
        hex_val = self.gen_hex_pairs()
        server.get_characteristic(char_uuid).value = self.hex_to_byte(hex_val)

        print("A new value will be notified on both clients")
        await aioconsole.ainput("Press enter to send the new value...")

        server.update_value(service_uuid, char_uuid)

        new_value = await aioconsole.ainput("Enter the new value from either client: ")
        assert new_value == hex_val

        # unsubscribe
        print("Unsubscribe both clients from the characteristic")
        await aioconsole.ainput("Press enter when ready...")
        assert self.subscribed_client_count(server) == 0

        # Stop Advertising
        await server.stop()
        await asyncio.sleep(2)
        assert await server.is_advertising() is False
