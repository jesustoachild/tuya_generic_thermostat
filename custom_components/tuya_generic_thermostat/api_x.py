import asyncio
import logging
import json
from homeassistant.core import HomeAssistant
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval
from tuya_connector import TuyaOpenAPI

# 创建日志记录器
_LOGGER = logging.getLogger(__name__)
#_LOGGER.setLevel(logging.INFO)
_LOGGER.setLevel(logging.WARNING)

# 全局变量，设置失败后的重新连接间隔为1分钟
FAIL_RECONNECT_INTERVAL = timedelta(minutes=1)
DEFAULT_APICALL_TIMEOUT = 5  # API调用的默认超时

# --- Tuya OpenAPI 云端大区配置 ---
TUYA_REGION_MAP = {
    "CN": "https://openapi.tuyacn.com",
    "US": "https://openapi.tuyaus.com",
    "EU": "https://openapi.tuyaeu.com",
    "IN": "https://openapi.tuyain.com",
}

class TuyaXAPI:
    def __init__(self, hass: HomeAssistant, access_id, access_secret, thermostat_device_id, ir_remote_device_id, region="CN"):
        self.access_id = access_id
        self.access_secret = access_secret
        self.thermostat_device_id = thermostat_device_id
        self.ir_remote_device_id = ir_remote_device_id
        self.ir_remote_suffix = ir_remote_device_id[-4:]
        self.hass = hass

        # 根据 UI 传入的 region 映射涂鸦 API 服务器 endpoint (默认兜底为 CN)
        self.tuya_endpoint = TUYA_REGION_MAP.get(region, "https://openapi.tuyacn.com")
        _LOGGER.info(f"[设备ID-{self.ir_remote_suffix}] API API 初始化设定涂鸦服务器地址为: {self.tuya_endpoint}")

        self._temperature = "25"
        self._mode = "0"
        self._power = "0"
        self._wind = "0"

        # 初始化时首次连接
        self.cancel_reconnect_task = None  # 用于存储取消任务的函数
        self.hass.loop.create_task(self.async_connect())

    async def async_connect(self, _now=None):
        try:
            # 使用初始化时设定的动态涂鸦 Endpoint
            openapi = TuyaOpenAPI(self.tuya_endpoint, self.access_id, self.access_secret)
            connect_result = await self.hass.async_add_executor_job(openapi.connect)
            self.openapi = openapi
            _LOGGER.info(f"[设备ID-{self.ir_remote_suffix} 函数：async_connect] TuyaOpenAPI 连接成功: {connect_result}")

            # 连接成功时，立即取消轮询
            if self.cancel_reconnect_task:
                self.cancel_reconnect_task()  # 取消之前的任务
                self.cancel_reconnect_task = None
                _LOGGER.info(f"[设备ID-{self.ir_remote_suffix} 函数：async_connect] 取消之前的重新连接任务")

        except Exception as e:
            _LOGGER.error(f"[设备ID-{self.ir_remote_suffix} 函数：async_connect] 连接 TuyaOpenAPI 失败: {e}")
            self.openapi = None

            # 如果连接失败，使用短间隔重新连接
            if self.cancel_reconnect_task is None:
                _LOGGER.info(f"[设备ID-{self.ir_remote_suffix} 函数：async_connect] 下次重新连接的间隔为: {FAIL_RECONNECT_INTERVAL}")
                self.cancel_reconnect_task = async_track_time_interval(
                    self.hass,
                    self.async_connect,
                    FAIL_RECONNECT_INTERVAL
                )

    async def send_command(self, code, value):
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/air-conditioners/{self.thermostat_device_id}/command"
        max_attempts = 3  # 最大尝试次数
        attempt = 0

        async def _send():
            nonlocal attempt
            attempt += 1
            try:
                _LOGGER.debug(f"[设备ID-{self.ir_remote_suffix} 函数：send_command] 第 {attempt} 次尝试，发送命令: code={code}, value={value}")
                data = await asyncio.wait_for(
                    self.hass.async_add_executor_job(
                        self.openapi.post,
                        url,
                        {
                            "code": code,
                            "value": value,
                        }
                    ),
                    timeout=DEFAULT_APICALL_TIMEOUT  # 设置 5 秒超时
                )
                api_string = f"发送：URL: {url}, PAYLOAD: {json.dumps({'code': code, 'value': value}, separators=(',', ':'))}，结果返回：{json.dumps(data, separators=(',', ':'))}"
                
                if data.get("success"):
                    _LOGGER.info(f"[设备ID-{self.ir_remote_suffix} 函数：send_command] 第 {attempt} 次尝试成功: {api_string}")
                    return True
                else:
                    _LOGGER.warning(f"[设备ID-{self.ir_remote_suffix} 函数：send_command] 第 {attempt} 次尝试失败: {api_string}")
                    return False
            except asyncio.TimeoutError:
                _LOGGER.warning(f"[设备ID-{self.ir_remote_suffix} 函数：send_command] 第 {attempt} 次尝试发送命令超时 (5 秒).")
                return False
            except Exception as e:
                _LOGGER.warning(f"[设备ID-{self.ir_remote_suffix} 函数：send_command] 第 {attempt} 次尝试发送命令错误: {e}")
                return False

        result = False
        while attempt < max_attempts and not result:
            result = await _send()

            if not result and attempt == 2:  # 第二次失败后，尝试重新连接并更新 token
                _LOGGER.warning(f"[设备ID-{self.ir_remote_suffix} 函数：send_command] 第二次发送失败，准备重新连接 TuyaOpenAPI 并更新 token")
                try:
                    _LOGGER.info(f"[设备ID-{self.ir_remote_suffix} 函数：send_command] 正在重新连接 TuyaOpenAPI 并更新 token")
                    await self.async_connect()
                    _LOGGER.info(f"[设备ID-{self.ir_remote_suffix} 函数：send_command] 重新连接 TuyaOpenAPI 成功，并已更新 token")
                except Exception as e:
                    _LOGGER.error(f"[设备ID-{self.ir_remote_suffix} 函数：send_command] 重新连接 TuyaOpenAPI 失败，后续操作中止: {e}")
                    break

        return result


    async def send_full_command(self, power, mode, temp, wind):
        url = f"/v2.0/infrareds/{self.ir_remote_device_id}/air-conditioners/{self.thermostat_device_id}/scenes/command"
        max_attempts = 3  # 最大尝试次数
        attempt = 0

        payload = {
            "power": int(power),
            "mode": int(mode),
            "temp": int(temp),
            "wind": int(wind),
        }

        async def _send_full():
            nonlocal attempt
            attempt += 1
            try:
                # 使用 asyncio.wait_for 设置 5 秒的超时
                data = await asyncio.wait_for(
                    self.hass.async_add_executor_job(self.openapi.post, url, payload),
                    timeout=DEFAULT_APICALL_TIMEOUT
                )
                api_string = f"发送：URL: {url}, PAYLOAD: {json.dumps(payload, separators=(',', ':'))}，结果返回：{json.dumps(data, separators=(',', ':'))}"
                
                if data.get("success"):
                    _LOGGER.info(f"[设备ID-{self.ir_remote_suffix} 函数：send_full_command] 第 {attempt} 次尝试成功: {api_string}")
                    return True
                else:
                    _LOGGER.warning(f"[设备ID-{self.ir_remote_suffix} 函数：send_full_command] 第 {attempt} 次尝试失败: {api_string}")
                    return False
            except asyncio.TimeoutError:
                _LOGGER.warning(f"[设备ID-{self.ir_remote_suffix} 函数：send_full_command] 第 {attempt} 次尝试: 发送命令超时 (5 秒).")
                return False
            except Exception as e:
                _LOGGER.warning(f"[设备ID-{self.ir_remote_suffix} 函数：send_full_command] 第 {attempt} 次尝试: 发送完整命令错误: {e}")
                return False

        result = False
        task = None
        while attempt < max_attempts and not result:
            if task:
                # 取消之前的任务（如果存在）
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    _LOGGER.info(f"[设备ID-{self.ir_remote_suffix} 函数：send_full_command] 第 {attempt} 次尝试: 之前的任务被取消")

            # 创建新的任务并等待结果
            task = asyncio.create_task(_send_full())
            result = await task

            if not result and attempt < max_attempts:  # 第两次失败后，重新连接并尝试发送
                if attempt == 2:  # 第三次尝试前进行重连
                    _LOGGER.warning(f"[设备ID-{self.ir_remote_suffix} 函数：send_full_command] 第 {attempt} 次尝试失败，准备重新连接 TuyaOpenAPI 并更新 token")
                    try:
                        _LOGGER.info(f"[设备ID-{self.ir_remote_suffix} 函数：send_full_command] 正在重新连接 TuyaOpenAPI 并更新 token")
                        await self.async_connect()
                        _LOGGER.info(f"[设备ID-{self.ir_remote_suffix} 函数：send_full_command] 重新连接 TuyaOpenAPI 成功，并已更新 token")
                    except Exception as e:
                        _LOGGER.error(f"[设备ID-{self.ir_remote_suffix} 函数：send_full_command] 重新连接 TuyaOpenAPI 失败，后续操作中止: {e}")
                        break

        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                _LOGGER.info(f"[设备ID-{self.ir_remote_suffix} 函数：send_full_command] 第 {attempt} 次尝试: 最终任务被取消")

        return result

