"""Test the MicroBot config flow."""
from unittest.mock import ANY, AsyncMock, patch

from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    SERVICE_INFO,
    USER_INPUT,
    MockMicroBotApiClientFail,
    patch_async_setup_entry,
)

from tests.common import MockConfigEntry

DOMAIN = "keymitt_ble"


def patch_microbot_api():
    """Patch MicroBot API."""
    return patch(
        "homeassistant.components.keymitt_ble.config_flow.MicroBotApiClient", AsyncMock
    )


async def test_bluetooth_discovery(hass: HomeAssistant) -> None:
    """Test discovery via bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=SERVICE_INFO,
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch_async_setup_entry() as mock_setup_entry, patch_microbot_api():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "link"
    assert result["errors"] is None

    with patch_microbot_api(), patch_async_setup_entry() as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["result"].data == {
        CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
        CONF_ACCESS_TOKEN: ANY,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_bluetooth_discovery_already_setup(hass: HomeAssistant) -> None:
    """Test discovery via bluetooth with a valid device when already setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
        },
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)
    with patch_microbot_api():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_BLUETOOTH},
            data=SERVICE_INFO,
        )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"


async def test_user_setup(hass: HomeAssistant) -> None:
    """Test the user initiated form with valid mac."""

    with patch(
        "homeassistant.components.keymitt_ble.config_flow.async_discovered_service_info",
        return_value=[SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch_microbot_api():
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "link"
    assert result2["errors"] is None

    with patch_microbot_api(), patch_async_setup_entry() as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["result"].data == {
        CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
        CONF_ACCESS_TOKEN: ANY,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_setup_already_configured(hass: HomeAssistant) -> None:
    """Test the user initiated form with valid mac."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
        },
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.keymitt_ble.config_flow.async_discovered_service_info",
        return_value=[SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_user_no_devices(hass: HomeAssistant) -> None:
    """Test the user initiated form with valid mac."""
    with patch_microbot_api(), patch(
        "homeassistant.components.keymitt_ble.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_no_link(hass: HomeAssistant) -> None:
    """Test the user initiated form with invalid response."""

    with patch_microbot_api(), patch(
        "homeassistant.components.keymitt_ble.config_flow.async_discovered_service_info",
        return_value=[SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch_microbot_api(), patch(
        "homeassistant.components.keymitt_ble.config_flow.MicroBotApiClient",
        MockMicroBotApiClientFail,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
    await hass.async_block_till_done()
    
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "link"
    assert result2["errors"] == {"base": "linking"}

    with patch_microbot_api():
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
    await hass.async_block_till_done()
    
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "link"
    assert result2["errors"] == {}
    
    with patch_microbot_api(), patch_async_setup_entry() as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result4["type"] == FlowResultType.CREATE_ENTRY
    assert result4["result"].data == {
        CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
        CONF_ACCESS_TOKEN: ANY,
    }
    assert len(mock_setup_entry.mock_calls) == 1
