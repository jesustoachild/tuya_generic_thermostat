# tuya_generic_thermostat

## Project Description / 项目描述

**English**:  
This project is a tailored version of the Home Assistant (HA) official `generic_thermostat`, specifically designed for Tuya WiFi infrared remote controls. It integrates the core functionality of the `generic_thermostat` with additional features to optimize control of Tuya-compatible air conditioners.

**中文**:  
这个项目是 Home Assistant (HA) 官方 `generic_thermostat` 的一个定制版本，特别设计用于 Tuya WiFi 红外遥控器。它在保留 `generic_thermostat` 核心功能的基础上，增加了针对 Tuya 兼容空调的优化功能。

## Keep `generic_thermostat` Key Features / 保留的 `generic_thermostat` 关键特性

**English**:

- **Precise Temperature Control**: Maintain indoor temperature within a specified range (e.g., ±0.3°C). The thermostat automatically switches between cooling and heating modes to achieve and maintain the desired temperature.
  
- **Minimum Cycle Duration**: Set a minimum cycle duration (e.g., 3 minutes) to prevent frequent on/off switching of the air conditioner, protecting the hardware.

- **Preset Modes**: Supports multiple preset modes such as activity, comfort, and sleep, each with predefined temperatures. For example, in sleep mode, the air conditioner will shut off once the target temperature is reached, ensuring a quieter environment.

- **Cooling and Heating Mode**: Control the air conditioner's cooling and heating modes. By setting `ac_mode: false` in the YAML configuration, heating during winter can be controlled while maintaining a comfortable room temperature.

**中文**:

- **精准温控**：保持室内温度在指定范围内（例如 ±0.3°C）。自动在制冷和制热模式之间切换，以保持目标温度。
  
- **最小循环时间**：设置最小循环时间（例如 3 分钟），以防止空调频繁开关，保护硬件。

- **预设模式**：支持活动、舒适、睡眠等模式，每种模式都有预定义的温度。例如，在睡眠模式下，当达到目标温度时，空调将关闭，以确保安静的环境。

- **制冷和制热模式**：控制空调的制冷和制热模式。通过在 YAML 配置中设置 `ac_mode: false` 参数，可以在冬季进行制热，同时保持舒适的室内温度。

## New Functionalities / 新增功能

**English**:

- **Fan Speed Control**: Supports fan speed settings—low, medium, high, and auto. This feature is added to enhance control beyond the basic on/off switch functionality provided by the original `generic_thermostat`.

- **Fan Only Mode**: When the target temperature is reached, the air conditioner switches to fan-only mode to circulate air and maintain room temperature. This mode ensures that the air is continually moved without active heating or cooling.

- **Idle Mode**: If the temperature deviates significantly beyond the tolerance range (e.g., ±0.6°C), the air conditioner will automatically turn off and enter idle mode. Additionally, during specific times (SLEEP_START_TIME = "23:55" to SLEEP_END_TIME = "08:00") or when the sleep preset is active, the system will bypass Fan Only Mode and directly enter Idle Mode to maintain a quieter environment during sleep.

- **Separate User-Defined Target Temperatures and AC Operating Temperatures**: Allows setting separate user-defined target temperatures and operating temperatures for the air conditioner. For example, if the target room temperature is set to 24°C, the air conditioner can cool to 22°C to reach the target temperature more quickly.

- **Tuya API Integration**: Supports Tuya API calls with automatic reconnection in case of failure, ensuring reliable communication with the Tuya cloud. Note: This code is configured to work with Tuya's China server. If you are in other countries or regions, please replace the API URL in `api_x.py` from <span style="color:red;">https://openapi.tuyacn.com</span> to the appropriate data center URL for your location.


**中文**:

- **风速控制**：支持低、中、高和自动风速设置，以增强对空调的控制，超越原有的开/关功能。

- **仅风扇模式**：当达到目标温度时，切换到仅风扇模式，以维持空气流通而不进行加热或制冷。

- **待机模式**：如果温度显著偏离（例如 ±0.6°C），空调将自动关闭并进入待机模式。在特定时间（例如 SLEEP_START_TIME = "23:55" 到 SLEEP_END_TIME = "08:00"）或激活睡眠预设时，系统将直接进入待机模式，以保持安静环境。

- **分开的用户设置的目标温度和空调运行温度**：允许设置独立的目标温度和空调运行温度。例如，如果目标室内温度设为 24°C，空调可以降到 22°C，以更快达到目标温度。

- **Tuya API 集成**：支持 Tuya API 调用，并在失败时自动重新连接，确保与 Tuya 云的可靠通信。注意：该代码配置为使用 Tuya 的中国服务器。如果你在其他国家或地区，请将 `api_x.py` 中的 API URL 从 <span style="color:red;">https://openapi.tuyacn.com</span> 更改为适合你位置的数据中心 URL。

## Simplified Configuration / 简化配置

**English**:

The configuration file has been streamlined by removing the `heater_entity_id` and `keep_alive` parameters, replacing them with four Tuya API IDs:
- `access_id`
- `access_secret`
- `remote_id`
- `ac_id`

**中文**:

配置文件已通过移除 `heater_entity_id` 和 `keep_alive` 参数而简化，取而代之的是四个 Tuya API ID：
- `access_id`
- `access_secret`
- `remote_id`
- `ac_id`

### Cooling Mode
![Cooling Mode](images/WechatIMG228.jpg)
_This image shows the system in Cooling mode, where the air conditioner is actively cooling the room._

### Heating Mode
![Heating Mode](images/WechatIMG230.jpg)
_This image demonstrates the Heating mode, with the air conditioner set to warm the room._

### Fan-Only Mode
![Fan-Only Mode](images/WechatIMG226.jpg)
_This image illustrates the Fan-Only mode, where the air conditioner is circulating air without active heating or cooling._

### Idle Mode
![Idle Mode](images/WechatIMG227.jpg)
_This image represents the Idle mode, where the air conditioner is turned off and the system is not actively controlling the room temperature._

## YAML Configuration Instructions

In this customized version of the `generic_thermostat`, the following changes have been made to the configuration:

### Removed Parameters

- **heater**: This parameter, which was used to specify the entity controlling the heating switch, has been removed.
- **keep_alive**: This parameter has also been removed as it is no longer required.

### Added Parameters

To integrate with Tuya WiFi infrared remote controls, the following new parameters have been introduced:

- **access_id**: _(Required)_ Your Tuya API Access ID.
- **access_secret**: _(Required)_ Your Tuya API Access Secret.
- **remote_id**: _(Required)_ The ID of the remote control device.
- **ac_id**: _(Required)_ The ID of the air conditioner device.

These four parameters must be filled out correctly for the integration to work properly.

---

## YAML 配置说明

在这个定制版本的 `generic_thermostat` 中，配置发生了以下变化：

### 移除的参数

- **heater**：此参数用于指定控制加热开关的实体，现已移除。
- **keep_alive**：此参数也已被移除，不再需要。

### 新增的参数

为了与涂鸦 WiFi 红外遥控器集成，添加了以下新参数：

- **access_id**：_(必填)_ 你的涂鸦 API Access ID。
- **access_secret**：_(必填)_ 你的涂鸦 API Access Secret。
- **remote_id**：_(必填)_ 遥控设备的 ID。
- **ac_id**：_(必填)_ 空调设备的 ID。

这四个参数必须正确填写，才能使集成正常工作。



## HA configuration.yaml Sample

Here's a sample configuration for integrating the `tuya_generic_thermostat` with Home Assistant:

```yaml
climate:
  - platform: tuya_generic_thermostat
    name: "主卧空调"
    #heater: switch.master_bedroom_tcooling_switch
    target_sensor: sensor.temperature_humidity_sensor_XXXXX_temperature
    #target_sensor: sensor.ble_temperature_zhu_wo_qing_XXXXX_du_ji
    unique_id: "主卧空调xxx，一定要唯一"
    access_id: "tty7xxxxxxxnuw"
    access_secret: "a60xxxxxxxxxxxxxed"
    remote_id: "6cxxxxxxxxvif0"
    ac_id: "6c3xxxxxxxcttx5"
    min_temp: 16
    max_temp: 30
    ac_mode: true
    target_temp: 24.7
    sleep_temp: 26.7
    activity_temp: 22.7
    comfort_temp: 24.7
    cold_tolerance: 0.3
    hot_tolerance: 0.3
    min_cycle_duration:
      minutes: 3
    initial_hvac_mode: "off"
    precision: 0.1

```
## Before Using / 使用前准备

**English**:

Please install `tuya-connector-python` as per the instructions on the [tuya-connector-python GitHub page](https://github.com/tuya/tuya-connector-python). To obtain your Tuya ID, visit [Tuya Platform](https://platform.tuya.com/).

**中文**:

请按照 [tuya-connector-python GitHub 页面](https://github.com/tuya/tuya-connector-python) 的说明安装 `tuya-connector-python`。获取你的 Tuya ID 请访问 [Tuya 平台](https://platform.tuya.com/)。

## About `generic_thermostat`

**English**:

The `generic_thermostat` is an official Home Assistant (HA) integration that acts as a simple thermostat to control heating or cooling devices. It works by turning a switch or any other entity on or off based on the current temperature and a target temperature set by the user. This integration is highly customizable and can be adapted to various HVAC systems.

For more details, you can visit the [official Home Assistant documentation](https://www.home-assistant.io/integrations/generic_thermostat/) and view the source code on [GitHub](https://github.com/home-assistant/core/blob/dev/homeassistant/components/generic_thermostat/).

**中文**:

`generic_thermostat` 是 Home Assistant (HA) 的官方集成，充当简单的温控器，用于控制供暖或制冷设备。它根据当前温度和用户设置的目标温度来打开或关闭一个开关或其他实体。这个集成具有高度的可定制性，可以适用于各种 HVAC 系统。

更多详情请访问 [Home Assistant 官方文档](https://www.home-assistant.io/integrations/generic_thermostat/) 并查看 [GitHub 上的源代码](https://github.com/home-assistant/core/blob/dev/homeassistant/components/generic_thermostat/)。


## Acknowledgements / 致谢

**English**:

Parts of the Tuya API implementation in this project were inspired by and reference the work from [David Ilie](https://github.com/DavidIlie) on the [tuya-smart-ir-ac](https://github.com/DavidIlie/tuya-smart-ir-ac) project. We are grateful for the insights and inspiration his work provided.

**中文**:

本项目中的部分涂鸦 API 实现参考并借鉴了 [David Ilie](https://github.com/DavidIlie) 在 [tuya-smart-ir-ac](https://github.com/DavidIlie/tuya-smart-ir-ac) 项目中的工作。我们对他的项目给予的启发和参考深表感谢。
