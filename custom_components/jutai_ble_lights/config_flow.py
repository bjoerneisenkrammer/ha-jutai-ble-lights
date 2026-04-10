"""Config flow and options flow for JuTai BLE Lights.

Initial setup (ConfigFlow):
  The user provides a friendly name and the device's MAC address.
  The MAC is stored in entry.data and never changes.

Reconfiguration (OptionsFlow):
  Accessible via the "Configure" button on the device card in HA.
  Currently allows renaming the device. Saving triggers a reload of the
  integration so the light entity picks up the new name immediately.
"""

from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN


class JutaiBleLightsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup of a JuTai BLE light."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Show the setup form and create the config entry on submit."""
        errors = {}

        if user_input is not None:
            mac = user_input["mac"].upper()

            # Prevent adding the same device twice.
            for entry in self._async_current_entries():
                if entry.data["mac"] == mac:
                    errors["base"] = "already_configured"
                    break

            if not errors:
                return self.async_create_entry(
                    title=user_input["name"],
                    data={"name": user_input["name"], "mac": mac},
                )

        schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("mac"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler for this config entry."""
        return JutaiBleOptionsFlow(config_entry)


class JutaiBleOptionsFlow(config_entries.OptionsFlow):
    """Handle reconfiguration of an existing JuTai BLE light entry."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Show the options form pre-filled with the current name."""
        if user_input is not None:
            # Keep the config entry title in sync so the device card shows the new name.
            self.hass.config_entries.async_update_entry(
                self._config_entry, title=user_input["name"]
            )
            return self.async_create_entry(data={"name": user_input["name"]})

        current_name = self._config_entry.options.get(
            "name", self._config_entry.data["name"]
        )
        schema = vol.Schema({
            vol.Required("name", default=current_name): str,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
