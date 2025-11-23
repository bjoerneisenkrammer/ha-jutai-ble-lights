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
