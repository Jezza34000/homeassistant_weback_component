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

    VACUUM_ON = 1
    MOP_ON = 2

    # Error state
    ROBOT_ERROR = "Malfunction"

    # Robot Error codes
    ROBOT_ERROR_NO = "NoError"
    ROBOT_ERROR_UNKNOWN = "UnknownError"
    ROBOT_ERROR_LEFT_WHEEL = "LeftWheelWinded"
    ROBOT_ERROR_RIGHT_WHEEL = "RightWheelWinded"
    ROBOT_ERROR_WHEEL_WINDED = "WheelWinded"
    ROBOT_ERROR_60017 = "LeftWheelSuspend"
    ROBOT_ERROR_60019 = "RightWheelSuspend"
    ROBOT_ERROR_WHEEL_SUSPEND = "WheelSuspend"
    ROBOT_ERROR_LEFT_BRUSH = "LeftSideBrushWinded"
    ROBOT_ERROR_RIGHT_BRUSH = "RightSideBrushWinded"
    ROBOT_ERROR_SIDE_BRUSH = "SideBrushWinded"
    ROBOT_ERROR_60031 = "RollingBrushWinded"
    ROBOT_ERROR_COLLISION = "AbnormalCollisionSwitch"
    ROBOT_ERROR_GROUND = "AbnormalAntiFallingFunction"
    ROBOT_ERROR_FAN = "AbnormalFan"
    ROBOT_ERROR_DUSTBOX2 = "NoDustBox"
    ROBOT_ERROR_CHARGE_FOUND = "CannotFindCharger"
    ROBOT_ERROR_CHARGE_ERROR = "BatteryMalfunction"
    ROBOT_ERROR_LOWPOWER = "LowPower"
    ROBOT_ERROR_CHARGE = "BottomNotOpenedWhenCharging"
    ROBOT_ERROR_CAMERA_CONTACT_FAIL = "CameraContactFailure"
    ROBOT_ERROR_LIDAR_CONNECT_FAIL = "LidarConnectFailure"
    ROBOT_ERROR_TANK = "AbnormalTank"
    ROBOT_ERROR_SPEAKER = "AbnormalSpeaker"
    ROBOT_ERROR_NO_WATER_BOX = "NoWaterBox"
    ROBOT_ERROR_NO_WATER_MOP = "NoWaterMop"
    ROBOT_ERROR_WATER_BOX_EMPTY = "WaterBoxEmpty"
    ROBOT_ERROR_FLOATING = "WheelSuspendInMidair"
    ROBOT_ERROR_DUSTBOX = "DustBoxFull"
    ROBOT_ERROR_GUN_SHUA = "BrushTangled"
    ROBOT_ERROR_TRAPPED = "RobotTrapped"
    ROBOT_CHARGING_ERROR = "ChargingError"
    ROBOT_BOTTOM_NOT_OPENED_WHEN_CHARGING = "BottomNotOpenedWhenCharging"
    ROBOT_ERROR_60024 = "CodeDropped"
    ROBOT_ERROR_60026 = "NoDustBox"
    ROBOT_ERROR_60028 = "OperatingCurrentOverrun"
    ROBOT_ERROR_60029 = "VacuumMotorTangled"
    ROBOT_ERROR_60032 = "StuckWheels"
    ROBOT_ERROR_STUCK = "RobotStuck"
    ROBOT_ERROR_BE_TRAPPED = "RobotBeTrapped"
    ROBOT_ERROR_COVER_STUCK = "LaserHeadCoverStuck"
    ROBOT_ERROR_LASER_HEAD = "AbnormalLaserHead"
    ROBOT_ERROR_WALL_BLOCKED = "WallSensorBlocked"
    ROBOT_ERROR_VIR_WALL_FORB = "VirtualWallForbiddenZoneSettingError"

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

        # First init status from HTTP API
        if self.robot_status is None:
            self.robot_status = thing_status

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
    def fan_status(self):
        """ Raw fan_status field string """
        return self.robot_status["fan_status"]
    
    @property
    def error_info(self):
        """ Raw error_info field string """
        return self.robot_status["error_info"]
    
    @property
    def battery_level(self):
        """ Raw battery_level field integer """
        return int(self.robot_status["battery_level"])
    
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
        if self.robot_status['fan_status'] == self.FAN_DISABLED and self.robot_status['water_level'] != self.MOP_DISABLED:
            return self.MOP_ON
        return self.VACUUM_ON

    # ==========================================================
    # Vacuum Entity
    # -> Method

    async def update(self):
        _LOGGER.debug("VacDevice: update")
        if await self.update_status(self.name, self.sub_type):
            return True
        _LOGGER.error("VacDevice: update failed")
        return False

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