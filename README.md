# Home Assistant Tuya IR Air Conditioner Integration (Generic Thermostat)
## 项目简介与功能

本项目是基于 Home Assistant 官方 `generic_thermostat` 插件的定制版本，专为 Tuya WiFi 红外遥控空调设备设计。  
它不仅支持传统空调基本遥控功能，还让传统空调结合外部温度传感器实现高精度温控（0.1°C 级别），并通过温差控制（0.4–0.6°C）提升体感舒适度。  

主要功能包括：

- 支持多 Tuya 云服务器（全球各大区，如 CN / US / EU / IN / SG 等）  
- 外部温度传感器支持，用于更精确温控  
- 温差控制设置，提升舒适体验  
- 支持 HA 配置流程（Config Flow），无需手动写 YAML  
- 完整的智能温控逻辑（模式、温度、风速等）  
- 界面友好，美观直观  

这不仅是一款空调遥控集成，更是一个完整的智能温控解决方案，让控制与监测更加简单友好。

---

## 安装方式

### 使用 HACS 安装（推荐）

1. 在 Home Assistant 安装并启用 Home Assistant Community Store (HACS)  
2. 在 HACS 界面搜索 “Tuya Generic Thermostat”  
3. 安装插件并重启 Home Assistant  

### 手动安装

1. 将整个 `tuya_generic_thermostat` 文件夹放入 Home Assistant 配置目录下的：

2. 重启 Home Assistant  
3. 在 **设置 → 设备与服务 → 添加集成** 中选择本插件进行配置

---

## 配置方式

### 推荐：UI 图形化配置

通过 Home Assistant UI 进入 **配置 → 设备与服务 → 添加集成**，搜索 **Tuya Generic Thermostat** 并按照向导完成配置。

### 备选：YAML 配置（高级用户）

```yaml
climate:
  - platform: tuya_generic_thermostat
    name: "客厅空调"
    target_sensor: sensor.living_room_temperature
    access_id: "YOUR_ACCESS_ID"
    access_secret: "YOUR_ACCESS_SECRET"
    remote_id: "YOUR_IR_REMOTE_DEVICE_ID"
    ac_id: "YOUR_AIR_CONDITIONER_DEVICE_ID"
    region: "CN"
    ac_mode: true
    target_temp: 26
    min_temp: 16
    max_temp: 30
    target_temp_step: 1.0
    cold_tolerance: 0.5
    hot_tolerance: 0.5
    min_cycle_duration:
      minutes: 10
    away_temp: 28
    eco_temp: 27
    comfort_temp: 25
    sleep_temp: 26
logger:
  default: info
  logs:
    custom_components.tuya_generic_thermostat: debug
