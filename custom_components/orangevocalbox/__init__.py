"""Orange VocalBox."""
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import ATTR_ID, ATTR_TYPE, DOMAIN, VALUES_TYPE, SERVICE_CLEAN
from .vocalbox import VocalBox, VocalboxError

SCAN_INTERVAL = timedelta(minutes=119)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Load configuration for Orange VocalBox component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, config_entry):
    """Set up VocalBox as config entry."""
    vocalbox = VocalBox(
        hass, config_entry.data[CONF_EMAIL], config_entry.data[CONF_PASSWORD]
    )

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=vocalbox.async_fetch_datas,
        update_interval=SCAN_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()

    if coordinator.data is None:
        return False

    hass.data[DOMAIN] = coordinator
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "binary_sensor")
    )

    service_clean_schema = vol.Schema(
        {
            vol.Required(ATTR_ID): vol.Any(cv.positive_int, vol.Equal("all")),
            vol.Required(ATTR_TYPE): vol.All(cv.string, vol.In(VALUES_TYPE)),
        }
    )

    async def async_vocalbox_clean(call) -> None:  # pylint: disable=unused-argument
        """Handle restart service call."""
        try:
            await vocalbox.async_delete_datas(call.data[ATTR_ID], call.data[ATTR_TYPE])
            await coordinator.async_refresh()
        except VocalboxError as error:
            _LOGGER.error(error)

    hass.services.async_register(
        DOMAIN, SERVICE_CLEAN, async_vocalbox_clean, service_clean_schema
    )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(config_entry, "binary_sensor")
    return True
