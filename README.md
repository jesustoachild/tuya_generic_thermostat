# tuya_generic_thermostat
This project is an enhanced version of the Home Assistant (HA) official generic_thermostat, modified to work with Tuya Wi-Fi IR remote hardware. It retains all the original functionalities of generic_thermostat, including:

Precise Temperature Control: Maintain indoor temperature within a specified range (e.g., ±0.3°C). The thermostat automatically switches between cooling and heating modes to achieve and maintain the desired temperature. (Original feature from generic_thermostat)

Minimum Cycle Duration: Set a minimum cycle duration (e.g., 3 minutes) to prevent frequent on/off switching of the air conditioner, protecting the hardware from potential damage. (Original feature from generic_thermostat)

Preset Modes: Supports multiple preset modes such as activity, comfort, and sleep, each with predefined temperatures. For example, in sleep mode, the air conditioner will shut off once the target temperature is reached, ensuring a quieter environment. (Original feature from generic_thermostat)

Heating Mode: With the ac_mode: false parameter in the YAML configuration, the air conditioner can be controlled for heating during winter, maintaining a comfortable room temperature. (Original feature from generic_thermostat)

In addition to retaining these original features, this project introduces the following advanced functionalities:

Fan Speed Control: Supports fan speed settings—low, medium, high, and auto. This feature is added to enhance control beyond the basic on/off switch functionality provided by the original generic_thermostat.

Fan Only Mode: When the target temperature is reached, the air conditioner switches to fan-only mode to circulate air and maintain room temperature. This mode ensures that the air is continually moved without active heating or cooling.

Idle Mode: If the temperature deviates significantly beyond the tolerance range (e.g., ±0.6°C, controlled by EXTREME_COLD_MULTIPLIER and EXTREME_HOT_MULTIPLIER), the air conditioner will automatically turn off and enter idle mode. Additionally, during specific times (SLEEP_START_TIME = "23:55" to SLEEP_END_TIME = "08:00") or when the sleep preset is active, the system will bypass Fan Only Mode and directly enter Idle Mode to maintain a quieter environment during sleep.

Separate User-Defined Target Temperatures and AC Operating Temperatures: Allows setting separate user-defined target temperatures and operating temperatures for the air conditioner. For example, if the target room temperature is set to 24°C, the air conditioner can cool to 22°C to reach the target temperature more quickly.

Tuya API Integration: Supports Tuya API calls with automatic reconnection in case of failure, ensuring reliable communication with the Tuya cloud. Note: This code is configured to work with Tuya's China server. If you are in other countries or regions, please replace the API URL in api_x.py from https://openapi.tuyacn.com to the appropriate data center URL for your location.

Simplified Configuration: The configuration file has been streamlined by removing the heater_entity_id and keep_alive parameters, replacing them with four Tuya API IDs：    
  access_id
  access_secret
  remote_id
  ac_id
Before Using: Please install tuya-connector-python. For more details, visit tuya-connector-python GitHub page https://github.com/tuya/tuya-connector-python . To obtain your Tuya ID, visit Tuya Platform. https://platform.tuya.com/


