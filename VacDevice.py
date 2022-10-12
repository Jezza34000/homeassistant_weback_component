import logging
from .WebackApi import WebackWssCtrl

_LOGGER = logging.getLogger(__name__)


class VacDevice(WebackWssCtrl):
    # Clean mode
    CLEAN_MODE_AUTO = 'AutoClean'
    CLEAN_MODE_EDGE = 'EdgeClean'
    CLEAN_MODE_EDGE_DETECT = 'EdgeDetect'
    CLEAN_MODE_SPOT = 'SpotClean'
    CLEAN_MODE_SINGLE_ROOM = 'RoomClean'
    CLEAN_MODE_MOP = 'MopClean'
    CLEAN_MODE_SMART = 'SmartClean'
    CLEAN_MODE_Z = 'ZmodeClean'
    ROBOT_PLANNING_LOCATION = 'PlanningLocation'
    ROBOT_PLANNING_RECT = 'PlanningRect'

    # Other Working state
    RELOCATION = 'Relocation'
    CHARGE_MODE_RETURNING = 'BackCharging'
    DIRECTION_CONTROL = 'DirectionControl'
    ROBOT_LOCATION_SOUND = 'LocationAlarm'

    # Charging state
    CHARGE_MODE_CHARGING = 'Charging'
    CHARGE_MODE_DOCK_CHARGING = 'PileCharging'
    CHARGE_MODE_DIRECT_CHARGING = 'DirCharging'
    CHARGE_MODE_CHARGE_DONE = 'ChargeDone'

    # Idle state
    CHARGE_MODE_IDLE = 'Hibernating'

    # Standby/Paused state
    CLEAN_MODE_STOP = 'Standby'

    # Fan level
    FAN_DISABLED = 'Pause'
    FAN_SPEED_QUIET = 'Quiet'
    FAN_SPEED_NORMAL = 'Normal'
    FAN_SPEED_HIGH = 'Strong'

    FAN_SPEEDS = {
        FAN_SPEED_QUIET,
        FAN_SPEED_NORMAL,
        FAN_SPEED_HIGH
    }

    # MOP Water level
    MOP_DISABLED = 'None'
    MOP_SPEED_LOW = 'Low'
    MOP_SPEED_NORMAL = 'Default'
    MOP_SPEED_HIGH = 'High'

    MOP_SPEEDS = {
        MOP_SPEED_LOW,
        MOP_SPEED_NORMAL,
        MOP_SPEED_HIGH
    }

    # Error state
    ROBOT_ERROR = "Malfunction"

    CLEANING_STATES = {
        DIRECTION_CONTROL, ROBOT_PLANNING_RECT, RELOCATION, CLEAN_MODE_Z, CLEAN_MODE_AUTO,
        CLEAN_MODE_EDGE, CLEAN_MODE_EDGE_DETECT, CLEAN_MODE_SPOT, CLEAN_MODE_SINGLE_ROOM,
        CLEAN_MODE_MOP, CLEAN_MODE_SMART
    }
    CHARGING_STATES = {
        CHARGE_MODE_CHARGING, CHARGE_MODE_DOCK_CHARGING, CHARGE_MODE_DIRECT_CHARGING
    }
    DOCKED_STATES = {
        CHARGE_MODE_IDLE, CHARGE_MODE_CHARGING, CHARGE_MODE_DOCK_CHARGING, CHARGE_MODE_DIRECT_CHARGING
    }

    # Payload attributes
    ASK_STATUS = "working_status"
    SET_FAN_SPEED = "fan_status"
    GOTO_POINT = "goto_point"
    RECTANGLE_INFO = "virtual_rect_info"
    SPEAKER_VOLUME = "volume"
    # Payload switches
    VOICE_SWITCH = "voice_switch"
    UNDISTURB_MODE = "undisturb_mode"
    SWITCH_VALUES = ['on', 'off']
    
    def __init__(self, thing_name, thing_nickname, sub_type, thing_status, wss_url, region_name, jwt_token):
        _LOGGER.debug("WebackApi RobotController __init__")
        super().__init__(wss_url, region_name, jwt_token)
        self.name = thing_name
        self.nickname = thing_nickname
        self.sub_type = sub_type
        self.status = thing_status

    # ==========================================================
    # Vacuum Entity
    # -> Properties
    
    @property
    def current_mode(self) -> str:
        """ Raw working_status field string """
        return self.status['working_status']
    
    @property
    def raw_status(self) -> str:
        """ Raw thing_status JSON """
        _LOGGER.debug(f"raw_status {self.status}")
        return self.status
    
    @property
    def is_cleaning(self) -> bool:
        """ Boolean define if robot is in cleaning state """
        _LOGGER.debug(f"is_cleaning = {self.current_mode}")
        return self.current_mode in self.CLEANING_STATES
    
    @property
    def is_available(self):
        """ Boolean define if robot is connected to cloud """
        return self.status['connected'] == 'true'
    
    @property
    def is_charging(self):
        """ Boolean define if robot is charging """
        return self.current_mode in self.CHARGING_STATES
    
    @property
    def fan_status(self):
        """ Raw fan_status field string """
        return self.status["fan_status"]
    
    @property
    def error_info(self):
        """ Raw error_info field string """
        return self.status["error_info"]
    
    @property
    def battery_level(self):
        """ Raw battery_level field integer """
        return int(self.status["battery_level"])
    
    @property
    def fan_speed_list(self):
        """ Return Fan speed list available"""
        return [self.FAN_SPEED_QUIET, self.FAN_SPEED_NORMAL, self.FAN_SPEED_HIGH]

    @property
    def clean_time(self):
        """Return clean time"""
        return self.status["clean_time"]

    @property
    def clean_area(self):
        """Return clean area in square meter"""
        return self.status["clean_area"]

    # ==========================================================
    # Vacuum Entity
    # -> Method

    async def update(self):
        _LOGGER.debug("update")
        await self.update_status(self.name, self.sub_type)
        return

    async def set_fan_water_speed(self, speed):
        """ User for set both : fan speed and water level"""
        # Checking if robot is running otherwise it will not apply value
        if not self.is_cleaning:
            _LOGGER.info(f"Vacuum: Can't set set fan/water speed (value={speed}) robot is not running.")
            return
        # Checking value are allowed²
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