"""Config flow for ViCare integration."""
from __future__ import annotations

from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_CIRCUIT,
    CONF_HEATING_TYPE,
    DEFAULT_HEATING_TYPE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    HeatingType,
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ViCare."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):  # type: ignore
        """Invoke when a user initiates a flow via the user interface."""

        data_schema = {
            vol.Required(CONF_USERNAME): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
            vol.Required(CONF_CLIENT_ID): cv.string,
            vol.Optional(CONF_CIRCUIT, default=0): int,
            vol.Optional(CONF_NAME, default="ViCare"): cv.string,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=30)
            ),
            vol.Optional(CONF_HEATING_TYPE, default=DEFAULT_HEATING_TYPE): vol.In(
                [DEFAULT_HEATING_TYPE, "gas", "heatpump", "fuelcell"]
            ),
        }

        if user_input is not None:
            unique_id = f"{user_input[CONF_USERNAME]}"
            if user_input.get(CONF_CIRCUIT) is not None:
                unique_id += f"-{user_input[CONF_CIRCUIT]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema))
