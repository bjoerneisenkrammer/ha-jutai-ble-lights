from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class JutaiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the JuTai BLE config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            mac = user_input["mac"].upper()

            # Check duplicate devices
            for entry in self._async_current_entries():
                if entry.data["mac"] == mac:
                    errors["base"] = "already_configured"
                    break

            if not errors:
                return self.async_create_entry(
                    title=user_input["name"],
                    data={
                        "name": user_input["name"],
                        "mac": mac,
                    },
                )

        schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("mac"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
