# Home Assistant Tuya IR AC Smart Integration (Generic Thermostat)

## 项目简介与功能

本项目是基于 Home Assistant 官方 `generic_thermostat` 插件的定制版本，专为 Tuya WiFi 红外遥控空调设备设计，通过 Tuya OpenAPI（支持多云区域）与设备通信，实现高精度智能温控。  
它不仅支持传统空调的基本遥控功能，还可结合外部温度传感器实现 0.1°C 精度温控，并通过温差控制（0.4–0.6°C）提升室内体感舒适度。

主要功能包括：

- **多区域 Tuya 云服务器支持**：覆盖 CN / US / EU / IN / SG 等全球区域，支持中英文 UI。  
- **外部温度传感器支持**：可接入任意 HA 温度传感器，实现更精确温控与舒适体验。  
- **Home Assistant 配置支持**：同时支持 UI 配置流程（Config Flow），也可在 Home Assistant 配置目录下的 `configuration.yaml` 文件中手动添加本插件配置，方便高级用户自定义参数。  
- **完整智能温控逻辑**：通过单个 HA `climate` 实体实现模式切换（制冷/制热，可通过 `ac_mode` 配置）、温度调节、风速控制、自动节能与舒适模式等功能。  
- **界面友好直观**：HA 仪表盘上展示简洁、美观、易操作的温控控制面板。  
- **全年覆盖**：一个实体即可同时管理夏季制冷与冬季制热，无需为不同模式创建多个实体。  
- **温控逻辑说明**：  
  设置空调为制冷或制热模式，设置室温目标的温度，和 cold_tolerance / hot_tolerance
  插件通过 HA `climate` 实体、外部温度传感器和 Tuya OpenAPI 完整实现智能温控控制，无需为制冷和制热创建两个实体。
## 安装方式

### 使用 HACS 安装（推荐）

由于本项项目暂作为HACS的“自定义存储库 (Custom repository)”进行添加。

**具体安装步骤：**
1. 打开 Home Assistant，进入左侧边栏的 **HACS** 面板。
2. 点击右上角的三点菜单（或者直接点击集成界面的底部），选择 **Custom repositories (自定义存储库)**。
3. 在弹出的对话框中填写以下信息：
   - **Repository (仓库地址)**: `https://github.com/jesustoachild/tuya_generic_thermostat`
   - **Category (类别)**: 选择 **Integration (集成)**
4. 点击 **Add (添加)**。
5. 添加成功后，在 HACS 的集成搜索栏中输入 `Tuya Generic Thermostat`。
6. 点击进入项目，点击右下角的 **Download (下载)**，建议选择最新版本进行安装。
7. **非常重要**：安装完成后，**必须重启 Home Assistant** 才能加载集成。

### 手动安装

1. 在 Home Assistant 主机的配置目录（通常为 `config/`）下，如果不存在则创建 `custom_components` 文件夹。
2. 下载本仓库的代码，将仓库内的 `custom_components/tuya_generic_thermostat/` 整个目录复制到你 HA 系统的 `config/custom_components/` 路径下。
3. **非常重要**：复制完成后，**必须重启 Home Assistant** 才能加载集成。

---

## 配置方式

当你通过上述任意一种方式完成安装，并且**重启 Home Assistant** 后，就可以正式配置使用了。

### 推荐：UI 图形化配置

1. 在 Home Assistant 主界面，进入 **配置 (Settings)** -> **设备与服务 (Devices & Services)**。
2. 点击右下角的 **添加集成 (Add Integration)**。
3. 搜索 **Tuya Generic Thermostat** 并点击添加。
4. 按照系统向导提示，填入你需要绑定的温度传感器、Tuya Access ID、Secret 和设备 ID 等信息即可完成加载。

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


