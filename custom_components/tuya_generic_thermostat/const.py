"""Constants for the Tuya Generic Thermostat integration."""

from homeassistant.components.climate import (
    PRESET_ACTIVITY,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_HOME,
    PRESET_SLEEP,
)

DOMAIN = "tuya_generic_thermostat"

CONF_ACCESS_ID = "access_id"
CONF_ACCESS_SECRET = "access_secret"
CONF_REMOTE_ID = "remote_id"
CONF_AC_ID = "ac_id"
CONF_REGION = "region"
CONF_SENSOR = "target_sensor"
CONF_AC_MODE = "ac_mode"
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"
CONF_MIN_DUR = "min_cycle_duration"
CONF_COLD_TOLERANCE = "cold_tolerance"
CONF_HOT_TOLERANCE = "hot_tolerance"
CONF_TARGET_TEMP = "target_temp"
CONF_INITIAL_HVAC_MODE = "initial_hvac_mode"
CONF_PRECISION = "precision"
CONF_TEMP_STEP = "target_temp_step"
CONF_PRESETS = {
    p: f"{p}_temp"
    for p in (
        PRESET_AWAY,
        PRESET_COMFORT,
        PRESET_ECO,
        PRESET_HOME,
        PRESET_SLEEP,
        PRESET_ACTIVITY,
    )
}
DEFAULT_TOLERANCE = 0.3
DEFAULT_NAME = "Tuya Generic Thermostat"

# --- 涂鸦红外控制使用的 API 代码常量 ---
# 为函数：get_target_operat_temp(self)定义变量
COOLING_MAX_OPERA_TEMP = 25         #定义制冷下，最高运行温度
HEATING_MIN_OPERA_TEMP = 25         #定义制热下，最低运行温度
COOLING_TEMP_OFFSET = 2             #定义制冷时候，空调运行温度比目的温度低多少
HEATING_TEMP_OFFSET = 2             #定义制热时候，空调运行温度比目的温度高多少

EXTREME_COLD_MULTIPLIER = 2  # 用于确定极端太冷的系数
EXTREME_HOT_MULTIPLIER = 2   # 用于确定极端太热的系数

SLEEP_START_TIME = "23:55"  # 晚上23:55
SLEEP_END_TIME = "08:00"    # 早上8:00

HVAC_MODE_COOL_API_CODE = 0
HVAC_MODE_HEAT_API_CODE = 1
HVAC_MODE_AUTO_API_CODE = 2
HVAC_MODE_FAN_ONLY_API_CODE = 3
HVAC_MODE_DRY_API_CODE = 4
HVAC_MODE_OFF_API_CODE = 5

POWER_ON_API_CODE = 1
POWER_OFF_API_CODE = 0

# 空调送风模式的 参数常量对象
AC_FAN_ONLY_API_CODE = {
    "power": POWER_ON_API_CODE,
    "mode": HVAC_MODE_FAN_ONLY_API_CODE,
    "temp": 25,
    "wind": 0,
}

# 空调空闲模式的 参数常量对象 (HVACAction.IDLE)
AC_IDLE_API_CODE = {
    "power": POWER_OFF_API_CODE,
    "mode": 0,
    "temp": 25,
    "wind": 0,
}

