from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

class JutaiBleLightsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            mac = user_input["mac"].upper()

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
        return JutaiBleOptionsFlow(config_entry)


class JutaiBleOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
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
