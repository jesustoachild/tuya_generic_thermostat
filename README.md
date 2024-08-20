# tuya_generic_thermostat

## Project Description

This project is a specialized version of the Home Assistant (HA) `generic_thermostat`, tailored for Tuya WiFi infrared remote controls. It extends the core functionality of the `generic_thermostat` with features optimized for Tuya-compatible air conditioners.

## Keep generic_thermostat Key Features

- **Precise Temperature Control**: Maintain indoor temperatures within a specified range (e.g., ±0.3°C). Automatically switches between cooling and heating modes to maintain the desired temperature.
  
- **Minimum Cycle Duration**: Set a minimum cycle duration (e.g., 3 minutes) to prevent frequent on/off switching, protecting the air conditioner hardware.

- **Preset Modes**: Supports modes such as activity, comfort, and sleep, each with predefined temperatures. In sleep mode, the air conditioner shuts off once the target temperature is reached to ensure quiet operation.

- **Cooling and Heating Mode**: Control the air conditioner for both cooling and heating. The `ac_mode: false` parameter in the YAML configuration allows for heating during winter while maintaining a comfortable room temperature.

## New Functionalities

- **Fan Speed Control**: Adjust fan speeds to low, medium, high, or auto for enhanced control beyond the basic on/off functionality.

- **Fan Only Mode**: Switch to fan-only mode when the target temperature is reached to maintain air circulation without active heating or cooling.

- **Idle Mode**: Automatically turn off the air conditioner and enter idle mode if temperatures deviate significantly (e.g., ±0.6°C). During specified times (e.g., SLEEP_START_TIME = "23:55" to SLEEP_END_TIME = "08:00") or when the sleep preset is active, the system enters Idle Mode for quieter operation.

- **Separate Target and Operating Temperatures**: Set different target and operating temperatures for quicker temperature adjustments. For example, if the target is 24°C, the air conditioner can cool to 22°C to reach the target faster.

- **Tuya API Integration**: Reliable communication with the Tuya cloud, with automatic reconnection on failure. Note: Configured for Tuya's China server. Change the API URL in `api_x.py` to the appropriate data center URL if outside China.

## Simplified Configuration

The configuration file has been streamlined by removing `heater_entity_id` and `keep_alive` parameters, replacing them with four Tuya API IDs:
- `access_id`
- `access_secret`
- `remote_id`
- `ac_id`

## Before Using

Install `tuya-connector-python` following the instructions on the [tuya-connector-python GitHub page](https://github.com/tuya/tuya-connector-python). Obtain your Tuya ID from the [Tuya Platform](https://platform.tuya.com/).
