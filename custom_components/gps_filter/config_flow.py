"""Config flow for GPS Filter."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
)

from .const import (
    CONF_MAX_ACCURACY,
    CONF_MAX_SPEED,
    CONF_SOURCE,
    DEFAULT_MAX_ACCURACY,
    DEFAULT_MAX_SPEED,
    DOMAIN,
)


class GPSFilterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """GPS Filter config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle user step."""

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_SOURCE])
            self._abort_if_unique_id_configured()

            state = self.hass.states.get(user_input[CONF_SOURCE])

            friendly_name = (
                state.attributes.get("friendly_name")
                if state
                else user_input[CONF_SOURCE]
            )

            return self.async_create_entry(
                title=f"GPS Filter - {friendly_name}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SOURCE): EntitySelector(
                        EntitySelectorConfig(
                            domain="device_tracker",
                        )
                    ),
                    vol.Required(
                        CONF_MAX_SPEED,
                        default=DEFAULT_MAX_SPEED,
                    ): vol.Coerce(float),
                    vol.Required(
                        CONF_MAX_ACCURACY,
                        default=DEFAULT_MAX_ACCURACY,
                    ): vol.Coerce(float),
                }
            ),
        )
