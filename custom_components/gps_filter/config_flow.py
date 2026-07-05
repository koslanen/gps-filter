"""Config flow for GPS Filter."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
)

from .const import (
    CONF_MAX_ACCURACY,
    CONF_MAX_SPEED,
    CONF_MAX_SPEED_DIFFERENCE,
    CONF_SOURCE,
    DEFAULT_MAX_ACCURACY,
    DEFAULT_MAX_SPEED,
    DEFAULT_MAX_SPEED_DIFFERENCE,
    DOMAIN,
)

POSITIVE_FLOAT = vol.All(
    vol.Coerce(float),
    vol.Range(min=0, min_included=False),
)


def _options_defaults(entry: ConfigEntry) -> dict[str, float]:
    """Return option defaults, falling back to config entry data."""
    return {
        CONF_MAX_SPEED: entry.options.get(
            CONF_MAX_SPEED,
            entry.data.get(CONF_MAX_SPEED, DEFAULT_MAX_SPEED),
        ),
        CONF_MAX_ACCURACY: entry.options.get(
            CONF_MAX_ACCURACY,
            entry.data.get(CONF_MAX_ACCURACY, DEFAULT_MAX_ACCURACY),
        ),
        CONF_MAX_SPEED_DIFFERENCE: entry.options.get(
            CONF_MAX_SPEED_DIFFERENCE,
            entry.data.get(
                CONF_MAX_SPEED_DIFFERENCE,
                DEFAULT_MAX_SPEED_DIFFERENCE,
            ),
        ),
    }


def _get_user_data_schema() -> vol.Schema:
    """Return the config flow user step schema."""
    return vol.Schema(
        {
            vol.Required(CONF_SOURCE): EntitySelector(
                EntitySelectorConfig(
                    domain="device_tracker",
                )
            ),
            vol.Required(
                CONF_MAX_SPEED,
                default=DEFAULT_MAX_SPEED,
            ): POSITIVE_FLOAT,
            vol.Required(
                CONF_MAX_ACCURACY,
                default=DEFAULT_MAX_ACCURACY,
            ): POSITIVE_FLOAT,
            vol.Required(
                CONF_MAX_SPEED_DIFFERENCE,
                default=DEFAULT_MAX_SPEED_DIFFERENCE,
            ): POSITIVE_FLOAT,
        }
    )


def _get_options_schema(defaults: dict[str, float]) -> vol.Schema:
    """Return the options flow schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_MAX_SPEED,
                default=defaults[CONF_MAX_SPEED],
            ): POSITIVE_FLOAT,
            vol.Required(
                CONF_MAX_ACCURACY,
                default=defaults[CONF_MAX_ACCURACY],
            ): POSITIVE_FLOAT,
            vol.Required(
                CONF_MAX_SPEED_DIFFERENCE,
                default=defaults[CONF_MAX_SPEED_DIFFERENCE],
            ): POSITIVE_FLOAT,
        }
    )


class GPSFilterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """GPS Filter config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return GPSFilterOptionsFlow(config_entry)

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
            data_schema=_get_user_data_schema(),
        )


class GPSFilterOptionsFlow(config_entries.OptionsFlow):
    """GPS Filter options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage GPS Filter options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=_get_options_schema(_options_defaults(self._entry)),
        )
