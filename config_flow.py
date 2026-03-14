"""Config flow for Tuya Generic Thermostat."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import voluptuous as vol

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN, SensorDeviceClass
from homeassistant.const import CONF_NAME, DEGREE
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)

from .const import (
    CONF_AC_ID,
    CONF_AC_MODE,
    CONF_ACCESS_ID,
    CONF_ACCESS_SECRET,
    CONF_COLD_TOLERANCE,
    CONF_HOT_TOLERANCE,
    CONF_MAX_TEMP,
    CONF_MIN_DUR,
    CONF_MIN_TEMP,
    CONF_PRESETS,
    CONF_REMOTE_ID,
    CONF_SENSOR,
    CONF_REGION,
    DEFAULT_TOLERANCE,
    DOMAIN,
)

# 步骤1：涂鸦连接凭据
TUYA_AUTH_SCHEMA = {
    vol.Required(CONF_REGION, default="CN"): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=["CN", "US", "EU", "IN"],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    ),
    vol.Required(CONF_ACCESS_ID): selector.TextSelector(),
    vol.Required(CONF_ACCESS_SECRET): selector.TextSelector(
        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
    ),
    vol.Required(CONF_REMOTE_ID): selector.TextSelector(),
    vol.Required(CONF_AC_ID): selector.TextSelector(),
}

# 步骤2：实体运行参数
THERMOSTAT_SETTINGS_SCHEMA = {
    vol.Required(CONF_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.TEMPERATURE
        )
    ),
    vol.Required(CONF_AC_MODE, default=False): selector.BooleanSelector(
        selector.BooleanSelectorConfig()
    ),
    vol.Required(
        CONF_COLD_TOLERANCE, default=DEFAULT_TOLERANCE
    ): selector.NumberSelector(
        selector.NumberSelectorConfig(
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement=DEGREE,
            step=0.1,
        )
    ),
    vol.Required(
        CONF_HOT_TOLERANCE, default=DEFAULT_TOLERANCE
    ): selector.NumberSelector(
        selector.NumberSelectorConfig(
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement=DEGREE,
            step=0.1,
        )
    ),
    vol.Optional(CONF_MIN_DUR): selector.DurationSelector(
        selector.DurationSelectorConfig(allow_negative=False)
    ),
    vol.Optional(CONF_MIN_TEMP): selector.NumberSelector(
        selector.NumberSelectorConfig(
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement=DEGREE,
            step=0.1,
        )
    ),
    vol.Optional(CONF_MAX_TEMP): selector.NumberSelector(
        selector.NumberSelectorConfig(
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement=DEGREE,
            step=0.1,
        )
    ),
}

PRESETS_SCHEMA = {
    vol.Optional(v): selector.NumberSelector(
        selector.NumberSelectorConfig(
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement=DEGREE,
            step=0.1,
        )
    )
    for v in CONF_PRESETS.values()
}

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(
        vol.Schema({vol.Required(CONF_NAME): selector.TextSelector(), **TUYA_AUTH_SCHEMA}), 
        next_step="settings"
    ),
    "settings": SchemaFlowFormStep(vol.Schema(THERMOSTAT_SETTINGS_SCHEMA), next_step="presets"),
    "presets": SchemaFlowFormStep(vol.Schema(PRESETS_SCHEMA)),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(vol.Schema(TUYA_AUTH_SCHEMA), next_step="settings"),
    "settings": SchemaFlowFormStep(vol.Schema(THERMOSTAT_SETTINGS_SCHEMA), next_step="presets"),
    "presets": SchemaFlowFormStep(vol.Schema(PRESETS_SCHEMA)),
}


class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle config or options flow for Tuya Generic Thermostat."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW
    options_flow_reloads = True

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        return cast(str, options.get(CONF_NAME, "Tuya Generic Thermostat"))
