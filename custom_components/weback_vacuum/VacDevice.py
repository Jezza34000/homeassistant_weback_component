import logging

from .WebackApi import WebackWssCtrl

_LOGGER = logging.getLogger(__name__)


class VacDevice(WebackWssCtrl):
    def __init__(self, thing_name, thing_nickname, sub_type, thing_status, wss_url, region_name, jwt_token):
        _LOGGER.debug("WebackApi RobotController __init__")
        super().__init__(wss_url, region_name, jwt_token)
        self.name = thing_name
        self.nickname = thing_nickname
        self.sub_type = sub_type

        # First init status from HTTP API
        if self.robot_status is None:
            self.robot_status = thing_status

    # ==========================================================
    # Update controller

    async def watch_state(self):
        """ State watcher from VacDevice"""
        _LOGGER.debug(f"VacDevice: starting state watcher for= {self.name} {self.sub_type}")
        try:
            await self.refresh_handler(self.name, self.sub_type)
        except:
            _LOGGER.exception('Error on watch_state starting refresh_handler')

    # ==========================================================
    # Vacuum Entity
    # -> Properties
    
    @property
    def current_mode(self) -> str:
        """ Raw working_status field string """
        return self.robot_status['working_status']
    
    @property
    def raw_status(self) -> str:
        """ Raw thing_status JSON """
        _LOGGER.debug(f"raw_status {self.robot_status}")
        return self.robot_status
    
    @property
    def is_cleaning(self) -> bool:
        """ Boolean define if robot is in cleaning state """
        _LOGGER.debug(f"is_cleaning = {self.current_mode}")
        return self.current_mode in self.CLEANING_STATES
    
    @property
    def is_available(self):
        """ Boolean define if robot is connected to cloud """
        return self.robot_status['connected'] == 'true'
    
    @property
    def is_charging(self):
        """ Boolean define if robot is charging """
        return self.current_mode in self.CHARGING_STATES
    
    @property
    def error_info(self):
        """ Raw error_info field string """
        return self.robot_status["error_info"]
    
    @property
    def battery_level(self):
        """ Raw battery_level field integer """
        return int(self.robot_status["battery_level"])

    @property
    def fan_status(self):
        """ Raw fan_status field string """
        return self.robot_status["fan_status"]

    @property
    def mop_status(self):
        """ Raw fan_status field string """
        return self.robot_status["water_level"]
    
    @property
    def fan_speed_list(self):
        """ Return Fan speed list available"""
        return [self.FAN_SPEED_QUIET, self.FAN_SPEED_NORMAL, self.FAN_SPEED_HIGH]

    @property
    def mop_level_list(self):
        """ Return Mop level list available"""
        return [self.MOP_SPEED_LOW, self.MOP_SPEED_NORMAL, self.MOP_SPEED_HIGH]

    @property
    def clean_time(self):
        """Return clean time"""
        return self.robot_status["clean_time"]

    @property
    def clean_area(self):
        """Return clean area in square meter"""
        return self.robot_status["clean_area"]

    @property
    def vacuum_or_mop(self) -> int:
        """ Find if the robot is in vacuum or mop mode """
        if 'fan_status' and 'water_level' in self.robot_status:
            if self.robot_status['fan_status'] == self.FAN_DISABLED and self.robot_status['water_level'] != self.MOP_DISABLED:
                return self.MOP_ON
            return self.VACUUM_ON
        return self.NO_FAN_NO_MOP

    # ==========================================================
    # Vacuum Entity
    # -> Method

    async def set_fan_water_speed(self, speed):
        """ User for set both : fan speed and water level"""
        # Checking if robot is running otherwise it will not apply value
        if not self.is_cleaning:
            _LOGGER.info(f"Vacuum: Can't set set fan/water speed (value={speed}) robot is not running.")
            return
        # Checking value are allowed
        if speed not in self.FAN_SPEEDS and speed not in self.MOP_SPEEDS:
            _LOGGER.error(f"Error: Fan/Mop value={speed} is not available")
            return
        # Sending command
        working_payload = {self.SET_FAN_SPEED: speed}
        await self.send_command(self.name, self.sub_type, working_payload)
        return
    
    async def turn_on(self):
        working_payload = {self.ASK_STATUS: self.CLEAN_MODE_AUTO}
        await self.send_command(self.name, self.sub_type, working_payload)
        return

    async def turn_off(self):
        working_payload = {self.ASK_STATUS: self.CHARGE_MODE_RETURNING}
        await self.send_command(self.name, self.sub_type, working_payload)
        return
    
    async def pause(self):
        working_payload = {self.ASK_STATUS: self.CLEAN_MODE_STOP}
        await self.send_command(self.name, self.sub_type, working_payload)
        return
    
    async def clean_spot(self):
        working_payload = {self.ASK_STATUS: self.CLEAN_MODE_SPOT}
        await self.send_command(self.name, self.sub_type, working_payload)
        return
    
    async def locate(self):
        working_payload = {self.ASK_STATUS: self.ROBOT_LOCATION_SOUND}
        await self.send_command(self.name, self.sub_type, working_payload)
        return
    
    async def return_to_base(self):
        working_payload = {self.ASK_STATUS: self.CHARGE_MODE_RETURNING}
        await self.send_command(self.name, self.sub_type, working_payload)
        return

    async def goto(self, point: str):
        working_payload = {
            self.ASK_STATUS: self.ROBOT_PLANNING_LOCATION,
            self.GOTO_POINT: point,
        }
        await self.send_command(self.name, self.sub_type, working_payload)
        return
    
    async def clean_rect(self, rectangle: str):
        working_payload = {
            self.ASK_STATUS: self.ROBOT_PLANNING_RECT,
            self.RECTANGLE_INFO: rectangle,
        }
        await self.send_command(self.name, self.sub_type, working_payload)
        return

    async def voice_mode(self, state: str):
        if state in self.SWITCH_VALUES:
            working_payload = {self.VOICE_SWITCH: state}
            await self.send_command(self.name, self.sub_type, working_payload)
        else:
            _LOGGER.error(f"Voice mode can't be set with value : {state}")
        return

    async def undisturb_mode(self, state: str):
        if state in self.SWITCH_VALUES:
            working_payload = {self.UNDISTURB_MODE: state}
            await self.send_command(self.name, self.sub_type, working_payload)
        else:
            _LOGGER.error(f"Undisturb mode can't be set with value : {state}")
        return
