from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol
from .const import DOMAIN

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="EcoFlow PowerStream", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("email"): str,
                    vol.Required("password"): str,
                    vol.Required("serial_number"): str,  // Sans default
                }
            ),
        )
