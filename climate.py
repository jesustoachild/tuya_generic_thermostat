"""Adds support for generic thermostat units."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime, time, timedelta
import logging
import math
from typing import Any
from .api_x import TuyaXAPI

import voluptuous as vol

# 设置日志记录器
_LOGGER = logging.getLogger(__name__)
#_LOGGER.setLevel(logging.INFO)
#_LOGGER.setLevel(logging.DEBUG)
_LOGGER.setLevel(logging.WARNING)

from homeassistant.components.climate import (
    ATTR_PRESET_MODE,
    PLATFORM_SCHEMA as CLIMATE_PLATFORM_SCHEMA,
    PRESET_ACTIVITY,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_HOME,
    PRESET_NONE,
    PRESET_SLEEP,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    FAN_LOW,     #2.0.1
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_AUTO,
    #SUPPORT_FAN_MODE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    CONF_NAME,
    CONF_UNIQUE_ID, 
    EVENT_HOMEASSISTANT_START,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import (
    DOMAIN as HA_DOMAIN,
    CoreState,
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.exceptions import ConditionError
from homeassistant.helpers import condition, config_validation as cv
from homeassistant.helpers.device import async_device_info_to_link_from_entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, VolDictType

#from . import CONF_HEATER, DOMAIN, PLATFORMS
from . import DOMAIN, PLATFORMS
from .const import (
    # HA 基础配置与实体属性
    DEFAULT_NAME, DEFAULT_TOLERANCE, CONF_AC_ID, CONF_AC_MODE, CONF_ACCESS_ID, 
    CONF_ACCESS_SECRET,     CONF_REMOTE_ID, CONF_SENSOR, CONF_PRESETS, CONF_REGION,
    CONF_COLD_TOLERANCE, CONF_HOT_TOLERANCE, CONF_INITIAL_HVAC_MODE, CONF_PRECISION, 
    CONF_MIN_DUR, CONF_MIN_TEMP, CONF_MAX_TEMP, CONF_TARGET_TEMP, CONF_TEMP_STEP,

    # 涂鸦极寒极热补偿与睡眠参数
    COOLING_MAX_OPERA_TEMP, HEATING_MIN_OPERA_TEMP, COOLING_TEMP_OFFSET, 
    HEATING_TEMP_OFFSET, EXTREME_COLD_MULTIPLIER, EXTREME_HOT_MULTIPLIER, 
    SLEEP_START_TIME, SLEEP_END_TIME,

    # 涂鸦红外底层 API 代码字典
    HVAC_MODE_COOL_API_CODE, HVAC_MODE_HEAT_API_CODE, HVAC_MODE_AUTO_API_CODE, 
    HVAC_MODE_FAN_ONLY_API_CODE, HVAC_MODE_DRY_API_CODE, HVAC_MODE_OFF_API_CODE,
    POWER_ON_API_CODE, POWER_OFF_API_CODE, AC_FAN_ONLY_API_CODE, AC_IDLE_API_CODE,
)

_LOGGER = logging.getLogger(__name__)


api_fan_modes_map = {
    FAN_LOW: ("1", FAN_LOW),
    FAN_MEDIUM: ("2", FAN_MEDIUM),
    FAN_HIGH: ("3", FAN_HIGH),
    FAN_AUTO: ("0", FAN_AUTO),
}

PRESETS_SCHEMA: VolDictType = {
    vol.Optional(v): vol.Coerce(float) for v in CONF_PRESETS.values()
}

PLATFORM_SCHEMA_COMMON = vol.Schema(
    {
        vol.Required(CONF_ACCESS_ID): cv.string,
        vol.Required(CONF_ACCESS_SECRET): cv.string,
        vol.Required(CONF_REMOTE_ID): cv.string,
        vol.Required(CONF_AC_ID): cv.string,
        vol.Optional(CONF_REGION, default="CN"): cv.string,
        #vol.Required(CONF_HEATER): cv.entity_id,
        vol.Required(CONF_SENSOR): cv.entity_id,
        vol.Optional(CONF_AC_MODE): cv.boolean,
        vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
        vol.Optional(CONF_MIN_DUR): cv.positive_time_period,
        vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_COLD_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
        vol.Optional(CONF_HOT_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
        vol.Optional(CONF_TARGET_TEMP): vol.Coerce(float),
        #vol.Optional(CONF_KEEP_ALIVE): cv.positive_time_period,
        vol.Optional(CONF_INITIAL_HVAC_MODE): vol.In(
            [HVACMode.COOL, HVACMode.HEAT, HVACMode.OFF]
        ),
        vol.Optional(CONF_PRECISION): vol.All(
            vol.Coerce(float),
            vol.In([PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE]),
        ),
        vol.Optional(CONF_TEMP_STEP): vol.All(
            vol.In([PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE])
        ),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        **PRESETS_SCHEMA,
    }
)


PLATFORM_SCHEMA = CLIMATE_PLATFORM_SCHEMA.extend(PLATFORM_SCHEMA_COMMON.schema)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize config entry."""
    config = dict(config_entry.data)
    config.update(config_entry.options)

    # Data merging for config and options flows handled by SchemaConfigFlow

    # 不通过 PLATFORM_SCHEMA 拦截强校验，避免默认值缺失引发整体崩溃
    # 只有当 UI 和 YAML 数据汇聚在类初始化时，使用兼容访问
    await _async_setup_config(
        hass,
        config,
        config_entry.entry_id,
        async_add_entities,
    )


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the generic thermostat platform."""

    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)
    await _async_setup_config(
        hass, config, config.get(CONF_UNIQUE_ID), async_add_entities
    )

async def _async_setup_config(
    hass: HomeAssistant,
    config: Mapping[str, Any],
    unique_id: str | None,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the generic thermostat platform."""

    name: str = config.get(CONF_NAME, DEFAULT_NAME)
    #heater_entity_id: str = config[CONF_HEATER]
    sensor_entity_id: str = config.get(CONF_SENSOR)
    min_temp: float | None = config.get(CONF_MIN_TEMP)
    max_temp: float | None = config.get(CONF_MAX_TEMP)
    target_temp: float | None = config.get(CONF_TARGET_TEMP)
    ac_mode: bool | None = config.get(CONF_AC_MODE)

    # 修复从 UI(Config Entry) 获取的时间结构为 字典 的问题，将字典转回 timedelta
    raw_min_dur = config.get(CONF_MIN_DUR)
    min_cycle_duration: timedelta | None = None
    if raw_min_dur:
        if isinstance(raw_min_dur, dict):
            min_cycle_duration = timedelta(**raw_min_dur)
        else:
            min_cycle_duration = raw_min_dur
            
    cold_tolerance: float = config.get(CONF_COLD_TOLERANCE, DEFAULT_TOLERANCE)
    hot_tolerance: float = config.get(CONF_HOT_TOLERANCE, DEFAULT_TOLERANCE)
    #keep_alive: timedelta | None = config.get(CONF_KEEP_ALIVE)
    initial_hvac_mode: HVACMode | None = config.get(CONF_INITIAL_HVAC_MODE)
    presets: dict[str, float] = {
        key: config[value] for key, value in CONF_PRESETS.items() if value in config
    }
    precision: float | None = config.get(CONF_PRECISION)
    target_temperature_step: float | None = config.get(CONF_TEMP_STEP)
    unit = hass.config.units.temperature_unit

    access_id: str = config.get(CONF_ACCESS_ID)
    access_secret: str = config.get(CONF_ACCESS_SECRET)
    remote_id: str = config.get(CONF_REMOTE_ID)
    ac_id: str = config.get(CONF_AC_ID)
    region: str = config.get(CONF_REGION, "CN")
    
    if not sensor_entity_id:
        _LOGGER.error("[设备ID-%s] 尝试创建实体，但提供的 Sensor Entity ID 为空！合并后的 config: %s", remote_id[-4:] if remote_id else "未知", config)
        return

    async_add_entities(
        [
            TuyaGenericThermostat(
                hass,
                name,
                #heater_entity_id,
                sensor_entity_id,
                min_temp,
                max_temp,
                target_temp,
                ac_mode,
                min_cycle_duration,
                cold_tolerance,
                hot_tolerance,
                #keep_alive,
                initial_hvac_mode,
                presets,
                precision,
                target_temperature_step,
                unit,
                unique_id,
                access_id,
                access_secret,
                remote_id,
                ac_id,
                region,
            )
        ]
    )


class TuyaGenericThermostat(ClimateEntity, RestoreEntity):
    """Representation of a Tuya Generic Thermostat device."""

    _attr_should_poll = False
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        #heater_entity_id: str,
        sensor_entity_id: str,
        min_temp: float | None,
        max_temp: float | None,
        target_temp: float | None,
        ac_mode: bool | None,
        min_cycle_duration: timedelta | None,
        cold_tolerance: float,
        hot_tolerance: float,
        #keep_alive: timedelta | None,
        initial_hvac_mode: HVACMode | None,
        presets: dict[str, float],
        precision: float | None,
        target_temperature_step: float | None,
        unit: UnitOfTemperature,
        unique_id: str | None,
        access_id: str,
        access_secret: str,
        remote_id: str,
        ac_id: str,
        region: str,
    ) -> None:
        """Initialize the thermostat."""
        self._access_id = access_id
        self._access_secret = access_secret
        self._remote_id = remote_id
        self.remote_id_suffix = self._remote_id[-4:] #LOG 使用的设备标识
        self._ac_id = ac_id

        self._api_x = TuyaXAPI(
            hass,
            self._access_id,
            self._access_secret,
            self._ac_id,
            self._remote_id,
            region,
        )

        self._attr_name = name
        #self.heater_entity_id = heater_entity_id
        self.sensor_entity_id = sensor_entity_id

        self.ac_mode = ac_mode
        self.min_cycle_duration = min_cycle_duration
        self._cold_tolerance = cold_tolerance
        self._hot_tolerance = hot_tolerance
        #self._keep_alive = None        self._keep_alive = Nohe 让原设置失效，Tuya 不需要
        self._hvac_mode = initial_hvac_mode
        self._saved_target_temp = target_temp or next(iter(presets.values()), None)
        self._temp_precision = precision
        self._temp_target_temperature_step = target_temperature_step
        if self.ac_mode:
            self._attr_hvac_modes = [HVACMode.COOL, HVACMode.OFF]
        else:
            self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        # Log the ac_mode, _attr_hvac_modes, and remote_id
        #_LOGGER.info(f"AC Mode: {self.ac_mode}, HVAC Modes: {self._attr_hvac_modes}, Remote ID: {self._remote_id}")

        self._system_ready = False              #self._active = False 原参数很容易混淆
        self._cur_temp: float | None = None
        self._temp_lock = asyncio.Lock()
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._attr_preset_mode = PRESET_NONE
        self._fan_mode = FAN_AUTO #3.0.1
        self._target_temp = target_temp
        self._target_operat_temp = target_temp
        self._attr_temperature_unit = unit
        self._attr_unique_id = unique_id
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE #3.0.1 修改
            | ClimateEntityFeature.PRESET_MODE #3.0.1 修改
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )
        if len(presets):
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
            self._attr_preset_modes = [PRESET_NONE, *presets.keys()]
        else:
            self._attr_preset_modes = [PRESET_NONE]
        self._presets = presets

        ##self.hvac_action_fan_checkflag = False  #为开机设置 自动送风模式准备
        self._hvac_action = HVACAction.OFF  # 初始化 hvac_action 为 OFF
        
        #self._is_ac_cooling_or_heating = False 替代了  # 保留源代码部分，初始为False
        self._last_operation_time = None  # 或者其他适当的初始化方式
    
    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Add listener
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.sensor_entity_id], self._async_sensor_changed
            )
        )

        @callback
        def _async_startup(_: Event | None = None) -> None:
            """Init on startup."""
            sensor_state = self.hass.states.get(self.sensor_entity_id)
            if sensor_state and sensor_state.state not in (
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                self._async_update_temp(sensor_state)
                self.async_write_ha_state()

        if self.hass.state == CoreState.running:
            _async_startup()
        else:
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _async_startup)

        # Check If we have an old state
        if (old_state := await self.async_get_last_state()) is not None:
            # If we have no initial temperature, restore
            if self._target_temp is None:
                # If we have a previously saved temperature
                if old_state.attributes.get(ATTR_TEMPERATURE) is None:
                    if self.ac_mode:
                        self._target_temp = self.max_temp
                    else:
                        self._target_temp = self.min_temp
                    _LOGGER.warning(
                        "Undefined target temperature, falling back to %s",
                        self._target_temp,
                    )
                else:
                    self._target_temp = float(old_state.attributes[ATTR_TEMPERATURE])
            if (
                self.preset_modes
                and old_state.attributes.get(ATTR_PRESET_MODE) in self.preset_modes
            ):
                self._attr_preset_mode = old_state.attributes.get(ATTR_PRESET_MODE)
            if not self._hvac_mode and old_state.state:
                self._hvac_mode = HVACMode(old_state.state)

        else:
            # No previous state, try and restore defaults
            if self._target_temp is None:
                if self.ac_mode:
                    self._target_temp = self.max_temp
                else:
                    self._target_temp = self.min_temp
            _LOGGER.warning(
                "No previously saved temperature, setting to %s", self._target_temp
            )

        # Set default state to off
        if not self._hvac_mode:
            self._hvac_mode = HVACMode.OFF
            self._hvac_action = HVACAction.OFF

    @property
    def precision(self) -> float:
        """Return the precision of the system."""
        if self._temp_precision is not None:
            return self._temp_precision
        return super().precision

    @property
    def supported_features(self):
        return self._attr_supported_features  #Return the list of supported features.

    @property
    def target_temperature_step(self) -> float:
        """Return the supported step of target temperature."""
        if self._temp_target_temperature_step is not None:
            return self._temp_target_temperature_step
        # if a target_temperature_step is not defined, fallback to equal the precision
        return self.precision

    @property
    def current_temperature(self) -> float | None:
        """Return the sensor temperature."""
        return self._cur_temp

    @property
    def _is_ac_cooling_or_heating(self) -> bool | None:
        """
        检查空调是否在制冷或制热状态。
        
        :return: 如果空调在制冷或制热状态则返回 True，否则返回 False
        """
        return self._hvac_action in {HVACAction.COOLING, HVACAction.HEATING}

    # v3.8修改
    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current operation."""
        #if self.hvac_action in (HVACAction.FAN, HVACAction.IDLE) and self.ac_mode: 
        if self.hvac_action == HVACAction.FAN and self.ac_mode: #2025-1-5 
            return HVACMode.FAN_ONLY
        return self._hvac_mode

    @property  # 2.0.1
    def fan_modes(self):
        return [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
        
    @property #2.0.1
    def fan_mode(self):
        return self._fan_mode

    @property
    def hvac_action(self) -> HVACAction:
        return self._hvac_action

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        #_LOGGER.debug("[设备ID-%s][函数：target_temperature] 读取目标温度: %s", self.remote_id_suffix, self._target_temp)
        return self._target_temp

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set hvac mode."""
        # 保存当前状态
        saved_state = self._save_current_state()
        
        success = False

        if hvac_mode == HVACMode.HEAT:
            self._hvac_mode = HVACMode.HEAT
            success = await self._async_control_ac_operation(
                reset_ac_temp_or_fanmode=False,
                force_reset_min_cycle_duration=True
            )
            
        elif hvac_mode == HVACMode.COOL:
            self._hvac_mode = HVACMode.COOL
            success = await self._async_control_ac_operation(
                reset_ac_temp_or_fanmode=False,
                force_reset_min_cycle_duration=True
            )
                    
        elif hvac_mode == HVACMode.OFF:
            self._hvac_mode = HVACMode.OFF
            success = await self._async_ac_turn_off()
            
        else:
            _LOGGER.error("Unrecognized hvac mode: %s", hvac_mode)
            return

        if not success:
            # 操作失败时恢复状态
            _LOGGER.error("[设备ID-%s 函数：async_set_hvac_mode] 设置 HVAC 模式失败，恢复之前的状态", self.remote_id_suffix)
            self._rollback_state(saved_state)

        # 确保在更改模式后更新当前操作
        self.async_write_ha_state()


    # 2.0.1 设置风速
    async def async_set_fan_mode(self, fan_mode):
        """Set new fan mode."""

        # 保存当前状态，在风速模式被更改前
        saved_state = self._save_current_state()

        self._fan_mode = fan_mode
        fan_mode = self._convert_fan_mode_to_apicode_int(self._fan_mode)

        # 如果当前不在制热或制冷状态，直接返回
        if self.hvac_action != HVACAction.HEATING and self.hvac_action != HVACAction.COOLING:
            _LOGGER.debug("[设备ID-%s 函数：async_set_fan_mode] 当前不在制热或制冷状态，操作取消", self.remote_id_suffix)
            return  # 不在制冷和制热

        _LOGGER.debug(
            "[设备ID-%s 函数：async_set_fan_mode] 设置新的风速模式为: %s",
            self.remote_id_suffix,
            fan_mode
        )

        # 调用控制操作函数
        success = await self._async_control_ac_operation(reset_ac_temp_or_fanmode=True, force_reset_min_cycle_duration=False)

        if not success:
            _LOGGER.error("[设备ID-%s 函数：async_set_fan_mode] 操作失败，回滚到之前的状态", self.remote_id_suffix)
            self._rollback_state(saved_state)
        else:
            _LOGGER.info("[设备ID-%s 函数：async_set_fan_mode] 操作成功，当前状态已更新", self.remote_id_suffix)

        # 更新 Home Assistant 状态
        self.async_write_ha_state()


    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        # 保存当前状态
        saved_state = self._save_current_state()

        # 设置新的目标温度
        self._target_temp = temperature
        _LOGGER.debug(
            "[设备ID-%s 函数：async_set_temperature] 设置新的目标温度为: %s",
            self.remote_id_suffix,
            self._target_temp
        )
        
        if self._hvac_mode == HVACMode.OFF:
            return

        # 调用控制操作函数
        success = await self._async_control_ac_operation(reset_ac_temp_or_fanmode=True, force_reset_min_cycle_duration=True)

        if not success:
            _LOGGER.error("[设备ID-%s 函数：async_set_temperature] 操作失败，回滚到之前的状态", self.remote_id_suffix)
            self._rollback_state(saved_state)
        else:
            _LOGGER.info("[设备ID-%s 函数：async_set_temperature] 操作成功，当前状态已更新", self.remote_id_suffix)

        # 更新 Home Assistant 状态
        self.async_write_ha_state()

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        if self._min_temp is not None:
            return self._min_temp

        # get default temp from super class
        return super().min_temp

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        if self._max_temp is not None:
            return self._max_temp

        # Get default temp from super class
        return super().max_temp

    async def _async_sensor_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle temperature changes."""

        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        # 更新当前温度
        self._async_update_temp(new_state)
        # 保存当前状态
        saved_state = self._save_current_state()
        # 调用控制操作函数
        success = await self._async_control_ac_operation(reset_ac_temp_or_fanmode=False, force_reset_min_cycle_duration=False)
        # 如果操作失败，回滚到之前保存的状态
        if not success:
            _LOGGER.error("[设备ID-%s 函数：_async_sensor_changed] 操作失败", self.remote_id_suffix)
            self._rollback_state(saved_state)
        # 更新 Home Assistant 状态
        self.async_write_ha_state()

    @callback
    def _async_update_temp(self, state: State) -> None:
        """Update thermostat with latest state from sensor."""
        try:
            cur_temp = float(state.state)
            if not math.isfinite(cur_temp):
                raise ValueError(f"Sensor has illegal state {state.state}")
            self._cur_temp = cur_temp
        except ValueError as ex:
            _LOGGER.error("Unable to update from sensor: %s", ex)

    #### 
    async def _async_control_ac_operation(
        self, reset_ac_temp_or_fanmode: bool = False, force_reset_min_cycle_duration: bool = False
    ) -> bool:
        """
        检查是否需要开启或关闭恒温器。

        参数:
        reset_ac_temp_or_fanmode (bool): 指示是否重置空调温度、预设模式或风速模式。在空调制冷或制热时使用。
        force_reset_min_cycle_duration (bool): 指示是否强制重置最小循环周期计时。
        
        返回:
        bool: 表示操作是否成功。
        """

        async with self._temp_lock:
            # 如果 self._system_ready 为 False 且当前温度 (self._cur_temp) 和目标温度 (self._target_temp) 不为 None
            if not self._system_ready and None not in (self._cur_temp, self._target_temp):
                self._system_ready = True
                _LOGGER.info(
                    (
                        "[设备ID-%s 函数：_async_control_ac_operation] 获取当前和目标温度。"
                        "恒温器已激活。当前温度：%s，目标温度：%s"
                    ),
                    self.remote_id_suffix,
                    self._cur_temp,
                    self._target_temp,
                )

        if not self._system_ready or self._hvac_mode == HVACMode.OFF:
            return True # 返回的原因是恒温器未激活或者当前 HVAC 模式为 OFF，不需要进行控制操作

        # 检查当前温度是否极端太冷，2025-1-5，制热模式下没有极热状态
        if self.ac_mode:
            extreme_cur_temp_condition_met, extreme_cur_temp_condition_result = await self._async_control_extreme_cur_temp()
            # 如果检测到极端温度条件且空调已设置为闲置模式，则直接返回并带着 API 调用结果
            if extreme_cur_temp_condition_met:
                return extreme_cur_temp_condition_result


        # 支持在制冷、制热情况下，改变风速或温度，并不改变最小循环周期的计时
        if not force_reset_min_cycle_duration and reset_ac_temp_or_fanmode:
            _LOGGER.info(
                "[设备ID-%s 函数：_async_control_ac_operation] 在制冷、制热情况下，改变风速或温度，并不改变最小循环周期的计时",
                self.remote_id_suffix,
            )
            result = await self._async_ac_turn_on(force_reset_min_cycle_duration=False)
            return result

        # 检查最小循环周期
        if not force_reset_min_cycle_duration and not reset_ac_temp_or_fanmode and self.min_cycle_duration:
            # 检查是否已经过了足够的时间
            if self._last_operation_time is not None:
                elapsed_time = datetime.now() - self._last_operation_time
                if elapsed_time < self.min_cycle_duration:
                    # 如果设备处于 standby 状态，则确保在小循环周期内设备进入 standby 状态
                    if not self._is_ac_cooling_or_heating:
                        result = await self._async_ac_update_standby_status(force=False)
                        return result
                    return True

        # 确保当前温度和目标温度不为 None 判断是否太冷、判断是否太冷
        assert self._cur_temp is not None and self._target_temp is not None
        too_cold = self._target_temp >= self._cur_temp + self._cold_tolerance
        too_hot = self._cur_temp >= self._target_temp + self._hot_tolerance

        # 空调在制冷或制热状态
        if self._is_ac_cooling_or_heating:
            if (self.ac_mode and too_cold) or (not self.ac_mode and too_hot):
                _LOGGER.info(
                    "[设备ID-%s 函数：_async_control_ac_operation] 空调从制冷、制热切换到standby（送风或空闲）", 
                    self.remote_id_suffix
                )
                result = await self._async_ac_update_standby_status(force=True)
                self._last_operation_time = datetime.now()  # 更新操作时间
                return result
            elif reset_ac_temp_or_fanmode:
                _LOGGER.info(
                    "[设备ID-%s 函数：_async_control_ac_operation] 制冷或制热中、重新设置空调参数",
                    self.remote_id_suffix,
                )
                result = await self._async_ac_turn_on(force_reset_min_cycle_duration=True)
                self._last_operation_time = datetime.now()  # 更新操作时间
                return result
            return True

        # 空调不在制冷或制热状态
        if (self.ac_mode and too_hot) or (not self.ac_mode and too_cold):
            _LOGGER.info("[设备ID-%s 函数：_async_control_ac_operation] 开启空调", self.remote_id_suffix)
            result = await self._async_ac_turn_on(force_reset_min_cycle_duration=True)
            _LOGGER.debug("[设备ID-%s 函数：_async_control_ac_operation] _async_ac_turn_on 调用结果: %s", self.remote_id_suffix, result)
            self._last_operation_time = datetime.now()  # 更新操作时间
            return result
        else:
            result = await self._async_ac_update_standby_status(force=False)
            _LOGGER.debug("[设备ID-%s 函数：_async_control_ac_operation] _async_ac_update_standby_status 调用结果: %s", self.remote_id_suffix, result)
            self._last_operation_time = datetime.now()  # 更新操作时间
            return result

    async def _async_ac_turn_on(self, force_reset_min_cycle_duration: bool = True) -> bool:
        """
        打开空调并设置目标温度。
        参数:
            force_reset_min_cycle_duration (bool): 
                是否重置最小循环周期计时器。
                如果为 True，则会更新上次操作时间和设备状态，使空调能够打开并设置目标温度。
                如果为 False，则会跳过这些更新，仅调整空调的设置，而不重置循环周期计时器。
        """
        if force_reset_min_cycle_duration:
            # 更新上次操作时间和设备状态，以确保在最小循环周期内
            self._last_operation_time = datetime.now()

        mode = HVAC_MODE_COOL_API_CODE  # 默认制冷模式
        action_mode = HVACAction.COOLING
        if self._hvac_mode == HVACMode.HEAT:
            mode = HVAC_MODE_HEAT_API_CODE  # 制热模式
            action_mode = HVACAction.HEATING
        self._hvac_action = action_mode

        fan_mode = self._convert_fan_mode_to_apicode_int(self._fan_mode)
        target_temp = self.get_target_operat_temp()

        success = await self._api_x.send_full_command(
            power=POWER_ON_API_CODE,
            mode=mode,
            temp=target_temp,
            wind=fan_mode,
        )
        _LOGGER.info(
            "[设备ID-%s 函数：_async_ac_turn_on] 发送命令: power=%s, mode=%s, temp=%s, wind=%s - 结果: %s",
            self.remote_id_suffix,
            POWER_ON_API_CODE,
            mode,
            target_temp,
            fan_mode,
            "成功" if success else "失败"
        )
        return success

    async def _async_ac_turn_off(self) -> bool:
        self._last_operation_time = datetime.now()

        # 判断 HVAC 模式来调用 Tuya API ########## 8.1
        if self._hvac_mode == HVACMode.OFF:
            self._hvac_action = HVACAction.OFF
            if self.ac_mode:
                mode = HVAC_MODE_COOL_API_CODE  # 制冷模式
            else:
                mode = HVAC_MODE_HEAT_API_CODE  # 制热模式

            fan_mode = self._convert_fan_mode_to_apicode_int(self._fan_mode)
            target_temp = self.get_target_operat_temp()

            success = await self._api_x.send_full_command(
                power=POWER_OFF_API_CODE,
                mode=mode,
                temp=target_temp,
                wind=fan_mode,
            )

            _LOGGER.info(
                "[设备ID-%s 函数：_async_ac_turn_off] 发送命令: power=%s, mode=%s, temp=%s, wind=%s - 结果: %s",
                self.remote_id_suffix,
                POWER_OFF_API_CODE,
                mode,
                target_temp,
                fan_mode,
                "成功" if success else "失败"
            )
            return success

    async def _async_ac_update_standby_status(self, force: bool = False) -> bool:
        if not force:
            if self._hvac_mode == HVACMode.OFF or self._is_ac_cooling_or_heating:
                _LOGGER.debug("[设备ID-%s 函数：_async_ac_update_standby_status] HVAC 模式为 OFF 或设备已激活，返回", self.remote_id_suffix)
                return True

        if force:
            self._last_operation_time = datetime.now()
            ##self.hvac_action_fan_checkflag = False
            _LOGGER.debug("[设备ID-%s 函数：_async_ac_update_standby_status] 强制更新：_last_operation_time, _is_ac_cooling_or_heating, hvac_action_fan_checkflag", self.remote_id_suffix)

        current_time = datetime.now()
        # 2025 修改制热模式下，不需要送风模式
        if self.is_within_time_range(current_time, SLEEP_START_TIME, SLEEP_END_TIME) or self._attr_preset_mode == PRESET_SLEEP or not self.ac_mode:
            # 当前时间在睡眠时间段内且预设模式为 "sleep"
            if self._hvac_action != HVACAction.IDLE:
                self._hvac_action = HVACAction.IDLE
                success = await self._async_set_ac_to_idle_mode()
                if success:
                    _LOGGER.info("[设备ID-%s 函数：_async_ac_update_standby_status] 设置模式为IDLE， 空闲（空调主机关闭）IDLE", self.remote_id_suffix)
                else:
                    _LOGGER.error("[设备ID-%s 函数：_async_ac_update_standby_status] 设置模式为 IDLE 失败", self.remote_id_suffix)
                return success
            else:
                # 如果已经是 IDLE 模式，则返回 True
                return True
        else:
            # 当前时间不在睡眠时间段内或预设模式不是 "sleep"
            if self._hvac_action != HVACAction.FAN:
                self._hvac_action = HVACAction.FAN
                success = await self._async_set_ac_to_fan_only_mode()
                if success:
                    _LOGGER.info("[设备ID-%s 函数：_async_ac_update_standby_status] 设置模式为FAN，空调送风模式", self.remote_id_suffix)
                else:
                    _LOGGER.error("[设备ID-%s 函数：_async_ac_update_standby_status] 设置模式为 FAN 失败", self.remote_id_suffix)
                return success
            else:
                # 如果已经是 FAN 模式，则返回 True
                return True


    async def _async_control_extreme_cur_temp(self) -> Tuple[bool, bool]:
        """
        检查当前温度是否在制冷模式下极端太冷或制热模式下极端太热，如果是则设置空调为闲置模式。

        :return: 一个元组，第一个值表示是否触发极端温度并尝试设置空调为闲置模式，
                第二个值表示 API 调用是否成功（如果没有触发极端温度则为 False）
        """
        # 确保当前温度和目标温度不为 None
        assert self._cur_temp is not None and self._target_temp is not None

        # 判断是否极端太冷
        extremely_too_cold = self._target_temp >= self._cur_temp + EXTREME_COLD_MULTIPLIER * self._cold_tolerance
        # 判断是否极端太热
        extremely_too_hot = self._cur_temp >= self._target_temp + EXTREME_HOT_MULTIPLIER * self._hot_tolerance

        # 如果当前是制冷模式且极端太冷，或是制热模式且极端太热，则设置空调为闲置模式
        if (self.ac_mode and extremely_too_cold) or (not self.ac_mode and extremely_too_hot):
            # 避免重复调用，只有当当前不是IDLE状态时才设置
            if self._hvac_action != HVACAction.IDLE:
                _LOGGER.warning("[设备ID-%s] 极端温度条件触发：制冷模式极端太冷 (%s) 或制热模式极端太热 (%s)，设置模式为 IDLE", self.remote_id_suffix, extremely_too_cold, extremely_too_hot)

                # 备份当前状态参数
                original_hvac_action = self._hvac_action
                original_last_operation_time = self._last_operation_time

                # 更新状态参数
                self._hvac_action = HVACAction.IDLE
                self._last_operation_time = datetime.now()

                # 尝试设置空调为闲置模式
                success = await self._async_set_ac_to_idle_mode()

                if success:
                    _LOGGER.info("[设备ID-%s 函数：_async_control_extreme_cur_temp] 设置模式为 IDLE 成功", self.remote_id_suffix)
                    return True, True  # 第一个 True 表示触发了极端温度，第二个 True 表示 API 调用成功
                else:
                    _LOGGER.error("[设备ID-%s 函数：_async_control_extreme_cur_temp] 设置模式为 IDLE 失败", self.remote_id_suffix)
                    # 恢复原始状态参数
                    self._hvac_action = original_hvac_action
                    self._last_operation_time = original_last_operation_time
                    return True, False  # 第一个 True 表示触发了极端温度，第二个 False 表示 API 调用失败

        return False, False  # 如果未触发极端温度条件，返回两个 False


    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        
        # 检查是否为支持的模式
        if preset_mode not in (self.preset_modes or []):
            _LOGGER.error(
                "[设备ID-%s 函数：async_set_preset_mode] Got unsupported preset_mode %s. Must be one of %s",
                self.remote_id_suffix,
                preset_mode,
                self.preset_modes
            )
            return

        # 如果模式未更改，直接返回
        if preset_mode == self._attr_preset_mode:
            _LOGGER.debug(
                "[设备ID-%s 函数：async_set_preset_mode] 预设模式未更改: %s",
                self.remote_id_suffix,
                preset_mode
            )
            return

        # 保存当前状态
        saved_state = self._save_current_state()

        if preset_mode == PRESET_NONE:
            self._attr_preset_mode = PRESET_NONE
            self._target_temp = self._saved_target_temp
            _LOGGER.debug(
                "[设备ID-%s 函数：async_set_preset_mode] 预设模式设置为 NONE, 恢复保存的目标温度: %s",
                self.remote_id_suffix,
                self._saved_target_temp
            )
            success = await self._async_control_ac_operation(reset_ac_temp_or_fanmode=True, force_reset_min_cycle_duration=True)
        else:
            if self._attr_preset_mode == PRESET_NONE:
                self._saved_target_temp = self._target_temp
                _LOGGER.debug(
                    "[设备ID-%s 函数：async_set_preset_mode] 当前预设模式为 NONE, 保存当前目标温度: %s",
                    self.remote_id_suffix,
                    self._target_temp
                )
            self._attr_preset_mode = preset_mode
            self._target_temp = self._presets[preset_mode]
            _LOGGER.debug(
                "[设备ID-%s 函数：async_set_preset_mode] 设置新的预设模式: %s, 新的目标温度为: %s",
                self.remote_id_suffix,
                preset_mode,
                self._target_temp
            )
            success = await self._async_control_ac_operation(reset_ac_temp_or_fanmode=True, force_reset_min_cycle_duration=True)

        if not success:
            _LOGGER.error("[设备ID-%s 函数：async_set_preset_mode] 操作失败，回滚到之前的状态", self.remote_id_suffix)
            self._rollback_state(saved_state)
        else:
            _LOGGER.info("[设备ID-%s 函数：async_set_preset_mode] 操作成功，当前状态已更新", self.remote_id_suffix)

        # 更新 Home Assistant 状态
        self.async_write_ha_state()



    def _convert_fan_mode_to_apicode_int(self, fan_mode):
        fan_mode_str = api_fan_modes_map.get(fan_mode, ("0", FAN_AUTO))[0]  # 获取对应的速度代码
        return int(fan_mode_str)

    async def _async_set_ac_to_fan_only_mode(self) -> bool:
        """Set the air conditioner to fan-only mode via Tuya API."""
        success = await self._api_x.send_full_command(
            **AC_FAN_ONLY_API_CODE
        )
        if success:
            return True  # 操作成功返回 True
        else:
            return False  # 操作失败返回 False

    async def _async_set_ac_to_idle_mode(self) -> bool:
        """Set the air conditioner to idel mode via Tuya API.
        我haier空调没有idel 模式，我设置为关闭或送风
        """
        success = await self._api_x.send_full_command(
            **AC_IDLE_API_CODE
        )
        if success:
            return True  # 操作成功返回 True
        else:
            return False  # 操作失败返回 False

    # 3.5 版本，优化空调运行温度，不一定要等于目标温度，大家可以按照自己的制冷制热测量调整空调的温度
    def get_target_operat_temp(self):
        """
        获取优化后的空调运行温度，制冷时将目标温度减去全局变量 COOLING_TEMP_OFFSET 的值，
        制热时将目标温度加上全局变量 HEATING_TEMP_OFFSET 的值。
        
        返回调整后的运行温度，该温度在设置的最小和最大温度范围内。
        """
        # 取得小数点前的整数
        self._target_operat_temp = int(float(self._target_temp))

        if self._hvac_mode == HVACMode.COOL:
            # 减去1
            self._target_operat_temp -= COOLING_TEMP_OFFSET

            # 检查目标温度是否小于最小温度
            if self._target_operat_temp < self._min_temp:
                self._target_operat_temp = self._min_temp

            # 检查目标温度是否大于COOLING_MAX_OPERA_TEMP
            if self._target_operat_temp > COOLING_MAX_OPERA_TEMP:
                self._target_operat_temp = COOLING_MAX_OPERA_TEMP

        elif self._hvac_mode == HVACMode.HEAT:
            # 加上2
            self._target_operat_temp += HEATING_TEMP_OFFSET

            # 检查目标温度是否大于最大温度
            if self._target_operat_temp > self._max_temp:
                self._target_operat_temp = self._max_temp

            # 检查目标温度是否小于HEATING_MIN_OPERA_TEMP
            if self._target_operat_temp < HEATING_MIN_OPERA_TEMP:
                self._target_operat_temp = HEATING_MIN_OPERA_TEMP

        return self._target_operat_temp

    def is_within_time_range(self, current_time: datetime, start_time_str: str, end_time_str: str) -> bool:
        """
        检查当前时间是否在指定的时间范围内。

        :param current_time: 当前时间
        :param start_time_str: 时间范围的开始时间（字符串格式 "HH:MM"）
        :param end_time_str: 时间范围的结束时间（字符串格式 "HH:MM"）
        :return: 是否在指定时间范围内
        """
        start_time = time.fromisoformat(start_time_str)
        end_time = time.fromisoformat(end_time_str)
        current_time_only = current_time.time()

        if start_time < end_time:
            # 时间范围在同一天内
            return start_time <= current_time_only < end_time
        else:
            # 时间范围跨越午夜
            return current_time_only >= start_time or current_time_only < end_time

    def _save_current_state(self) -> dict:
        """
        保存当前状态以备回滚使用。
        """
        saved_state = {
            'system_ready': self._system_ready,
            'hvac_mode': self._hvac_mode,
            'hvac_action': self._hvac_action,
            'last_operation_time': self._last_operation_time,
            'target_temp': self._target_temp,
            'attr_preset_mode': self._attr_preset_mode,
            'fan_mode': self._fan_mode,
        }
        """
        添加调试日志
        _LOGGER.debug(
            "[设备ID-%s] 调用 _save_current_state: 保存的状态为: %s",
            self.remote_id_suffix,
            saved_state
        )
        """
        return saved_state
        
    def _rollback_state(self, saved_state: dict):
        """
        恢复到之前保存的状态。
        
        添加调试日志
        _LOGGER.debug(
            "[设备ID-%s] 调用 _rollback_state: 恢复之前的状态: %s",
            self.remote_id_suffix,
            saved_state
        )
        """
        self._system_ready = saved_state.get('system_ready', self._system_ready)
        self._hvac_mode = saved_state.get('hvac_mode', self._hvac_mode)
        self._hvac_action = saved_state.get('hvac_action', self._hvac_action)
        self._last_operation_time = saved_state.get('last_operation_time', self._last_operation_time)
        self._target_temp = saved_state.get('target_temp', self._target_temp)
        self._attr_preset_mode = saved_state.get('attr_preset_mode', self._attr_preset_mode)
        self._fan_mode = saved_state.get('fan_mode', self._fan_mode)
        
        self._attr_target_temperature = self._target_temp #8.12 更新


