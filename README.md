# Home Assistant Tuya IR Air Conditioner Integration (Generic Thermostat)

## 项目简介与功能

本项目是基于 Home Assistant 官方 `generic_thermostat` 插件的定制版本，专为 Tuya WiFi 红外遥控空调设备设计，并通过 Tuya OpenAPI（支持多云区域）与设备通信，实现高精度智能温控。  
它不仅支持传统空调的基本遥控功能，还可结合外部温度传感器实现 0.1°C 精度温控，并通过温差控制（0.4–0.6°C）提升室内体感舒适度。

主要功能包括：

- **多区域 Tuya 云服务器支持**：覆盖 CN / US / EU / IN / SG 等全球区域，支持中英文 UI。  
- **外部温度传感器支持**：可接入任意 HA 温度传感器，实现更精确的温控与舒适体验。  
- **Home Assistant 配置支持**：同时支持 UI 配置流程（Config Flow），也可在 Home Assistant 配置目录下的 `configuration.yaml` 文件中手动添加本插件配置，方便高级用户自定义参数。
- **完整智能温控逻辑**：通过单个 HA `climate` 实体实现模式切换、温度调节、风速控制、自动节能与舒适模式等功能。  
- **界面友好直观**：HA 仪表盘上展示简洁、美观、易操作的温控控制面板。

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
