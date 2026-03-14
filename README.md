# 🌡️ Home Assistant Tuya IR Air Conditioner Integration (Generic Thermostat)

![version](https://img.shields.io/badge/version-1.6.2-blue.svg)
![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg)

A custom component for Home Assistant that deeply integrates Tuya Smart IR remotes and generic air conditioners into a native `climate` entity via the Tuya OpenAPI.

---

## ✨ 核心特性 (Core Features)

*   **多地域数据中心支持**：原生支持切换 Tuya 云端 API 数据中心（CN/US/EU/IN），降低 API 请求延迟。
*   **分步式引导配置流 (Config Flow)**：支持通过 Home Assistant UI 完成全部配置项，按功能模块分为：授权凭证、运行参数及预设温度三个向导步骤。
*   **API 异常状态自愈**：内置断线重连与 Token 热加载机制。当命令下发因 Token 过期被拒绝时，后台会静默执行鉴权刷新并自动重传指令，前端界面无错误抛出。
*   **向下兼容**：完整的向下兼容性支持，旧版本基于 `configuration.yaml` 配置的实体在升级后无需重新配置，默认绑定中国（CN）大区。

## 📱 设备兼容性 (Device Compatibility)

*   **已测试环境**：目前作者使用的网关设备为 **涂鸦智能 Wi-Fi / 433 射频红外遥控器**，受控设备为 **海尔 (Haier) 中央空调**。经过配置与实战检验，除仅损失极个别进阶指令（如上下摆风控制）外，制冷、制热及恒温控制皆完美运行。
*   **高通用性声明**：基于涂鸦平台底层的红外抽象架构理论，只要您的遥控/网关设备在涂鸦 App 内归属于 **「万能遥控器 (Infrared Remote)」**，且目标空调配置成功并支持反控执行（如制冷、制热、调节温度、调节风速四大基操），本组件即能全面接管控制。

## 📦 安装 (Installation using HACS)

推荐使用 [HACS (Home Assistant Community Store)](https://hacs.xyz/) 进行安装与未来更新管理：

1.  打开 HACS 界面，进入 **集成 (Integrations)**。
2.  点击右上方的菜单按钮，选择 **自定义存储库 (Custom repositories)**。
3.  将本项目的 GitHub 链接粘贴进 URL 框，类别选择 **Integration** 并添加。
4.  搜索 **Tuya Generic Thermostat** 并点击下载。
5.  重启您的 Home Assistant 服务。

## 🔑 凭证获取指南 (Retrieve Information from Tuya IoT)

使用本组件需要您在涂鸦开发者平台注册云项目，并获取对应的凭据及设备 ID。

1.  **获取 Access ID / Client ID 与 Access Secret / Client Secret：**
    访问 [涂鸦 IoT 开发者平台 (Tuya Developer Platform)](https://platform.tuya.com/cloud)，进入左侧菜单 `云开发 (Cloud)` -> `云项目 (Cloud Project)`。打开您的项目后，可以在概览页获取这两个密钥参数。

2.  **获取对应 Device ID：**
    在同一云项目页面的 `设备 (Devices)` 选项卡中，查找到您已绑定的红外遥控器网关，及其下挂载的虚拟空调设备，并复制它们的 Device ID。

## ⚙️ 配置方式 (Configuration)

### 推荐：UI 图形化配置
进入 **配置 (Settings) -> 设备与服务 (Devices & Services) -> 添加集成 (Add Integration)**。搜索 **Tuya Generic Thermostat** 并按照智能表单引导完成配置。

### 备选：YAML 代码配置 (支持高级选项)
支持在 `configuration.yaml` 中通过代码片段注册设备：

```yaml
climate:
  - platform: tuya_generic_thermostat
    name: "Living Room AC"
    target_sensor: sensor.living_room_temperature
    access_id: "YOUR_ACCESS_ID"
    access_secret: "YOUR_ACCESS_SECRET"
    remote_id: "YOUR_IR_REMOTE_DEVICE_ID"
    ac_id: "YOUR_AIR_CONDITIONER_DEVICE_ID"
    
    # API 区域（新特性）
    # 可选项：CN (中国), US (美洲), EU (欧洲), IN (印度)。留空默认 CN。
    region: "CN"
    
    # 运行逻辑参数
    ac_mode: true              # true 为制冷设备，false 为制热设备
    target_temp: 26            # 默认目标温度
    min_temp: 16               # 温度下限
    max_temp: 30               # 温度上限
    target_temp_step: 1.0      # 单次调节步长
    
    cold_tolerance: 0.5        # 冷容差阈值
    hot_tolerance: 0.5         # 热容差阈值
    min_cycle_duration:
      minutes: 10              # 最小动作间隔，用于压缩机保护

    # 情景预设 (Presets)
    away_temp: 28              # 离家模式
    eco_temp: 27               # 节能模式
    comfort_temp: 25           # 舒适模式
    sleep_temp: 26             # 睡眠模式
```

## 💡 架构哲学设计 (Architecture Rationale)

在此特别说明，鉴于红外光线这种“泼出去的水”的单向通信物理特性——当用户在家里使用真正的物理遥控器改变了空调设置时，涂鸦云端是完全收不到反馈的。基于真实的家庭使用场景痛点，本分支**刻意舍弃了各大主流涂鸦衍生插件皆在尝试的「云端状态轮询同步 (Cloud State Sync/Polling)」策略**。

与之相对，本项目坚信**高优先级的 HA 本地局域网闭环控制**：在运行期间，涂鸦云端仅被纯粹地作为控制指令的发射通道；插件逻辑只关心 HA 侧室内传感读数与空调面板动作的强一致性，从而彻底从根源上避免了因“云端滞后的伪状态”覆写系统面板，所造成的不可控的逻辑冲突与温控紊乱。

## 🐞 问题排查 (Debug & Troubleshooting)

若遇到特殊设备不支持或红外回调异常，请在 HA 的 `configuration.yaml` 中为本组件开启日志收集，并提交到 [Issues](https://github.com/jesustoachild/tuya_generic_thermostat/issues) 进行讨论：
```yaml
logger:
  default: info
  logs:
    custom_components.tuya_generic_thermostat: debug
```

## 👏 致谢与版权说明 (Acknowledgements & License)

本项目的重构与开发离不开开源社区的支持，特别鸣谢以下项目的开源贡献与代码启发：

*   [**Home Assistant Core: Generic Thermostat**](https://github.com/home-assistant/core/tree/dev/homeassistant/components/generic_thermostat)：提供了气候系统精准恒温逻辑与原生代码的坚实结构。
*   [**DavidIlie / tuya-smart-ir-ac**](https://github.com/DavidIlie/tuya-smart-ir-ac) 与 [**EnzoD86 / tuya-smart-ir-ac**](https://github.com/EnzoD86/tuya-smart-ir-ac)：针对基于 Tuya OpenAPI 网关和红外空调控制的底层协议机制，本分支的绝大部分通信逻辑直接溯源并高度借鉴了前者的开源成果，同时后者严谨的说明文档结构也给予了极大的参考启迪。

此项目遵循与 Home Assistant 相同的 Apache License 2.0 开源协议进行分发。
