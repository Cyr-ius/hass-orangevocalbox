"""Config flow to configure Orange VocalBox."""

import logging
from .vocalbox import VocalBox, VocalboxError
import voluptuous as vol
from homeassistant import config_entries, core
from homeassistant.const import CONF_PASSWORD, CONF_EMAIL
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

_LOGGER = logging.getLogger(__name__)


class OrangeVocalBoxFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Orange VocalBox config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            try:
                vocalbox = VocalBox(self.hass)
                await vocalbox.async_connect(
                    user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except VocalboxError as error:
                errors["base"] = error.args[1]

            if "base" not in errors:
                return self.async_create_entry(title="Orange VocalBox", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
