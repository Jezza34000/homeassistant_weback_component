import asyncio
import configparser
import hashlib
import json
import logging
import threading
import time
from datetime import datetime, timedelta

import httpx
import websocket

from .VacMap import VacMap

_LOGGER = logging.getLogger(__name__)

# Socket
SOCK_CONNECTED = "Open"
SOCK_CLOSE = "Close"
SOCK_ERROR = "Error"
# API Answer
SUCCESS_OK = 'success'
SERVICE_ERROR = 'ServiceErrorException'
USER_NOT_EXIST = 'UserNotExist'
PASSWORD_NOK = 'PasswordInvalid'

# API
AUTH_URL = "https://user.grit-cloud.com/prod/oauth"
ROBOT_UPDATE = "thing_status_update"
MAP_DATA = "map_data"
N_RETRY = 8
ACK_TIMEOUT = 5
HTTP_TIMEOUT = 5


class WebackApi:
    """
    WeBack API
    Handle connexion with OAuth server to get WSS credentials
    """
    def __init__(self, user, password, region, country, app, client_id, api_version):
        _LOGGER.debug("WebackApi __init__")

        # HTTP Oauth required param
        self.user = user
        self.password = password
        self.region = region
        self.app = app
        self.country = country
        self.client_id = client_id
        self.api_version = api_version

        # API auth & connexion param
        self.jwt_token = None
        self.region_name = None
        self.wss_url = None
        self.api_url = None
        self.token_duration = 0
        self.token_exp = None

    async def login(self) -> bool:
        """"
        Login to WebBack platform
        """
        params = {
            "json": {
                "payload": {
                    "opt": "login",
                    "pwd": hashlib.md5(self.password.encode()).hexdigest()
                },
                "header": {
                    "language": self.country,
                    "app_name": self.app,
                    "calling_code": "00" + self.region,
                    "api_version": self.api_version,
                    "account": self.user,
                    "client_id": self.client_id
                }
            }
        }

        # Checking if there is cached token and is still valid
        if self.verify_cached_creds():
            return True

        resp = await self.send_http(AUTH_URL, **params)

        if resp['msg'] == SUCCESS_OK:

            # Login OK
            self.jwt_token = resp['data']['jwt_token']
            self.region_name = resp['data']['region_name']
            self.wss_url = resp['data']['wss_url']
            self.api_url = resp['data']['api_url']
            self.token_duration = resp['data']['expired_time'] - 60

            # Calculate token expiration
            now_date = datetime.today()
            self.token_exp = now_date + timedelta(seconds=self.token_duration)
            _LOGGER.debug("WebackApi login successful")

            self.save_token_file()
            return True
        elif resp['msg'] == SERVICE_ERROR:
            # Wrong APP
            _LOGGER.error(f"WebackApi login failed, application is not recognized, "
                          f"try to change 'application' field (this field is case sensitive) in your configuration.yaml")
            return False
        elif resp['msg'] == USER_NOT_EXIST:
            # User NOK
            _LOGGER.error(f"WebackApi login failed, user does not exist, check you login and you area code ?")
            return False
        elif resp['msg'] == PASSWORD_NOK:
            # Password NOK
            _LOGGER.error(f"WebackApi login failed, wrong password")
            return False
        else:
            # Login NOK
            _LOGGER.error(f"WebackApi can't login (reason is : {resp['msg']})")
            return False

    def verify_cached_creds(self):
        """
        Check if cached creds are not outdated
        """
        creds_data = self.get_token_file()
        if "weback_token" in creds_data:
            if self.check_token_is_valid(creds_data['weback_token']['token_exp']):
                # Valid creds to use, loading it
                self.jwt_token = creds_data['weback_token']['jwt_token']
                self.region_name = creds_data['weback_token']['region_name']
                self.wss_url = creds_data['weback_token']['wss_url']
                self.api_url = creds_data['weback_token']['api_url']
                self.token_exp = creds_data['weback_token']['token_exp']
                _LOGGER.debug("WebackApi use cached creds.")
                return True
        _LOGGER.debug("WebackApi has no or invalid cached creds, renew it...")
        return False

    @staticmethod
    def get_token_file() -> dict:
        """
        Open token file and get all data.
        """
        creds_data = {}
        try:
            config = configparser.ConfigParser()
            config.read('weback_creds')
            creds_data = config._sections
        except:
            _LOGGER.debug(f"WebackApi not found or invalid weback creds file")
        return creds_data

    def save_token_file(self):
        """
        Save token file with all information
        """
        try:
            config = configparser.ConfigParser()
            config.add_section('weback_token')
            config.set('weback_token', 'jwt_token', str(self.jwt_token))
            config.set('weback_token', 'token_exp', str(self.token_exp))
            config.set('weback_token', 'api_url', str(self.api_url))
            config.set('weback_token', 'wss_url', str(self.wss_url))
            config.set('weback_token', 'region_name', str(self.region_name))
            with open('weback_creds', 'w') as configfile:
                config.write(configfile)
            _LOGGER.debug(f"WebackApi saved new creds")
        except Exception as e:
            _LOGGER.debug(f"WebackApi failed to saved new creds details={e}")

    @staticmethod
    def check_token_is_valid(token) -> bool:
        """
        Check if token validity is still OK or not
        """
        _LOGGER.debug(f"WebackApi checking token validity : {token}")
        try:
            now_date = datetime.today() - timedelta(minutes=15)
            dt_token = datetime.strptime(str(token), "%Y-%m-%d %H:%M:%S.%f")
            if now_date < dt_token:
                _LOGGER.debug(f"WebackApi token is valid")
                return True
        except Exception as e:
            _LOGGER.debug(f"WebackApi failed to check token : {e}")
        _LOGGER.debug(f"WebackApi token not valid")
        return False

    async def get_robot_list(self):
        """
        Get robot things list registered from Weback server
        """
        _LOGGER.debug("WebackApi ask : robot list")

        params = {
            "json": {
                "opt": "user_thing_list_get"
            },
            "headers": {
                'Token': self.jwt_token,
                'Region': self.region_name
            }
        }

        resp = await self.send_http(self.api_url, **params)

        if resp['msg'] == SUCCESS_OK:
            _LOGGER.debug(f"WebackApi get robot list OK : {resp['data']['thing_list']}")
            return resp['data']['thing_list']
        else:
            _LOGGER.error(f"WebackApi failed to get robot list (details : {resp})")
            return []
    
    async def get_reuse_map_by_id(self, id, sub_type, thing_name):
        """
        Get reuse map object by id
        """
        _LOGGER.debug(f"WebackApi ask : get reuse map {id}")

        params = {
            "json": {
                "opt": "reuse_map_get",
                "map_id": str(id),
                "sub_type": sub_type,
                "thing_name": thing_name
            },
            "headers": {
                'Token': self.jwt_token,
                'Region': self.region_name
            }
        }

        resp = await self.send_http(self.api_url, **params)

        if resp['msg'] == SUCCESS_OK:
            _LOGGER.debug(f"WebackApi get reuse map OK")
            return resp['data']['map_data']
        else:
            _LOGGER.error(f"WebackApi failed to get reuse map (details : {resp})")
            return []

    @staticmethod
    async def send_http(url, **params):
        """
        Send HTTP request
        """
        _LOGGER.debug(f"Send HTTP request Url={url} Params={params}")
        timeout = httpx.Timeout(HTTP_TIMEOUT, connect=15.0)
        for attempt in range(N_RETRY):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    r = await client.post(url, **params)
                    if r.status_code == 200:
                        # Server status OK
                        _LOGGER.debug(f"WebackApi : Send HTTP OK, return=200")
                        _LOGGER.debug(f"WebackApi : HTTP data received = {r.json()}")
                        return r.json()
                    else:
                        # Server status NOK
                        _LOGGER.warning(f"WebackApi : Bad server response (status code={r.status_code}) retry... ({attempt}/{N_RETRY})")
            except httpx.RequestError as e:
                _LOGGER.debug(f"Send HTTP exception details={e} retry... ({attempt}/{N_RETRY})")
        else:
            _LOGGER.error(f"WebackApi : HTTP error after {N_RETRY} retry")
            return {"msg": "error", "details": f"Failed after {N_RETRY} retry"}


# def null_callback(message):
#     _LOGGER.debug(f"WebackVacuumApi (WSS) null_callback: {message}")


class WebackWssCtrl(WebackApi):

    # Clean mode
    CLEAN_MODE_AUTO = 'AutoClean'
    CLEAN_MODE_EDGE = 'EdgeClean'
    CLEAN_MODE_EDGE_DETECT = 'EdgeDetect'
    CLEAN_MODE_SPOT = 'SpotClean'
    CLEAN_MODE_SINGLE_ROOM = 'RoomClean'
    CLEAN_MODE_ROOMS = 'SelectClean'
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
    IDLE_MODE_HIBERNATING = 'Hibernating'
    IDLE_MODE = 'Idle'

    # Standby/Paused state
    CLEAN_MODE_STOP = 'Standby'

    # Fan level
    FAN_DISABLED = 'None'
    FAN_SPEED_QUIET = 'Quiet'
    FAN_SPEED_NORMAL = 'Normal'
    FAN_SPEED_HIGH = 'Strong'
    FAN_SPEED_MAX = 'Max'

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

    NO_FAN_NO_MOP = 0
    VACUUM_ON = 1
    MOP_ON = 2

    # Error state
    ROBOT_ERROR = 'Malfunction'

    # Unknow state
    ROBOT_UNKNOWN = 'unknown'

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
        CLEAN_MODE_ROOMS, CLEAN_MODE_MOP, CLEAN_MODE_SMART
    }

    CHARGING_STATES = {
        CHARGE_MODE_CHARGING, CHARGE_MODE_DOCK_CHARGING, CHARGE_MODE_DIRECT_CHARGING
    }

    DOCKED_STATES = {
        CHARGE_MODE_CHARGING, CHARGE_MODE_DOCK_CHARGING, CHARGE_MODE_DIRECT_CHARGING, CHARGE_MODE_CHARGE_DONE
    }

    # Payload attributes
    ASK_STATUS = "working_status"
    SET_FAN_SPEED = "fan_status"
    GOTO_POINT = "goto_point"
    RECTANGLE_INFO = "virtual_rect_info"
    SPEAKER_VOLUME = "volume"
    SELECTED_ZONE = "selected_zone"
    # Payload switches
    VOICE_SWITCH = "voice_switch"
    UNDISTURB_MODE = "undisturb_mode"
    SWITCH_VALUES = ['on', 'off']

    """
    WebSocket Weback API controller
    Handle websocket to send/receive robot control
    """
    def __init__(self, user, password, region, country, app, client_id, api_version):
        super().__init__(user, password, region, country, app, client_id, api_version)
        _LOGGER.debug("WebackApi WSS Control __init__")
        self.ws = None
        self.authorization = "Basic KG51bGwpOihudWxsKQ=="
        self.socket_state = SOCK_CLOSE
        self.robot_status = None
        self.subscriber = []
        self.wst = None
        self.ws = None
        self._refresh_time = 60
        self.sent_counter = 0
        
        # Reloading cached creds
        self.verify_cached_creds()

    async def check_credentials(self):
        """
        Check if credentials for WSS link are OK
        """
        _LOGGER.debug(f"WebackApi (WSS) Checking credentials...")
        if not self.region_name or not self.jwt_token or not self.check_token_is_valid(self.token_exp):
            _LOGGER.debug(f"WebackApi (WSS) Credentials need renewal")
            # Cred renewal necessary
            if await self.login():
                return True
            else:
                return False
        _LOGGER.debug(f"WebackApi (WSS) Credentials are OK")
        return True

    async def open_wss_thread(self):
        """
        Connect WebSocket to Weback Server and create a thread to maintain connexion alive
        """
        if not await self.check_credentials():
            _LOGGER.error(f"WebackApi (WSS) Failed to obtain WSS credentials")
            return False

        _LOGGER.debug(f"WebackApi (WSS) Addr={self.wss_url} / Region={self.region_name} / Token={self.jwt_token}")
        
        try:
            self.ws = websocket.WebSocketApp(self.wss_url, header={"Authorization": self.authorization,
                                                                   "region": self.region_name,
                                                                   "token": self.jwt_token,
                                                                   "Connection": "keep-alive, Upgrade",
                                                                   "handshakeTimeout": "10000"},
                                             on_message=self.on_message,
                                             on_close=self.on_close,
                                             on_open=self.on_open,
                                             on_error=self.on_error,
                                             on_pong=self.on_pong)

            self.wst = threading.Thread(target=self.ws.run_forever)
            self.wst.start()
            
            if self.wst.is_alive():
                _LOGGER.debug("WebackApi (WSS) Thread was init")
                return True
            else:
                _LOGGER.error("WebackApi (WSS) Thread connection init has FAILED")
                return False

        except Exception as e:
            self.socket_state = SOCK_ERROR
            _LOGGER.debug("WebackApi (WSS) Error while opening socket", e)
            return False
        
    async def connect_wss(self):
        if self.socket_state == SOCK_CONNECTED:
            return True

        _LOGGER.debug(f"WebackApi (WSS) Not connected, connecting...")

        if await self.open_wss_thread():
            logging.debug(f"WebackApi (WSS) Connecting...")
        else:
            return False

        for i in range(15):
            logging.debug(f"WebackApi (WSS) awaiting connexion established... {i}")
            if self.socket_state == SOCK_CONNECTED:
                return True
            await asyncio.sleep(0.5)
        return False
    
    def on_error(self, ws, error):
        """Socket "On_Error" event"""
        details = ""
        if error:
            details = f"(details : {error})"
        _LOGGER.debug(f"WebackApi (WSS) Error {details}")
        self.socket_state = SOCK_ERROR

    def on_close(self, ws, close_status_code, close_msg):
        """Socket "On_Close" event"""
        _LOGGER.debug(f"WebackApi (WSS) Closed")

        if close_status_code or close_msg:
            _LOGGER.debug("WebackApi (WSS) Close Status_code: " + str(close_status_code))
            _LOGGER.debug("WebackApi (WSS) Close Message: " + str(close_msg))
        self.socket_state = SOCK_CLOSE

    def on_pong(self, message):
        _LOGGER.debug("WebackApi (WSS) Got a Pong")
    
    def on_open(self, ws):
        """Socket "On_Open" event"""
        _LOGGER.debug(f"WebackApi (WSS) Connexion established OK")
        self.socket_state = SOCK_CONNECTED
    
    def on_message(self, ws, message):
        """Socket "On_Message" event"""
        self.sent_counter = 0
        wss_data = json.loads(message)
        _LOGGER.debug(f"WebackApi (WSS) Msg received {wss_data}")
        if wss_data["notify_info"] == ROBOT_UPDATE:
            self.adapt_refresh_time(wss_data['thing_status'])

            if wss_data['thing_status'] != self.robot_status:
                _LOGGER.debug('New update from cloud ->> push update')
                self.robot_status = wss_data['thing_status']
                self._call_subscriber()
            else:
                _LOGGER.debug('No update from cloud')
        elif wss_data["notify_info"] == MAP_DATA:
            _LOGGER.debug(f"WebackApi (WSS) Map data received")
            self.map.wss_update(wss_data['map_data'])
            self.render_map()
            self._call_subscriber()
        else:
            _LOGGER.error(f"WebackApi (WSS) Received an unknown message from server : {wss_data}")

        # Close WSS link if we don't need it anymore or it will get closed by remote side
        if self._refresh_time == 120:
            _LOGGER.debug("WebackApi (WSS) Closing WSS...")
            self.ws.close()
            self.socket_state = SOCK_CLOSE
    
    async def publish_wss(self, dict_message):
        """
        Publish payload over WSS connexion
        """
        json_message = json.dumps(dict_message)
        _LOGGER.debug(f"WebackApi (WSS) Publishing message : {json_message}")

        if self.sent_counter >= 5:
            # Server do not answer (maybe other app are open ???) re-start WSS connexion
            _LOGGER.warning(f"WebackApi (WSS) Link is UP, but server has stopped answering request. "
                            f"Maybe other WeBack app are opened ? (re-open it...)")
            self.sent_counter = 0
            self.ws.close()
            self.socket_state = SOCK_CLOSE

        for attempt in range(N_RETRY):
            if self.socket_state == SOCK_CONNECTED:
                try:
                    self.ws.send(json_message)
                    self.sent_counter += 1
                    _LOGGER.debug(f"WebackApi (WSS) Msg published OK")
                    return True
                except websocket.WebSocketConnectionClosedException as e:
                    self.socket_state = SOCK_CLOSE
                    _LOGGER.debug(f"WebackApi (WSS) Error while publishing message (details: {e})")
            else:
                _LOGGER.debug(f"WebackApi (WSS) Can't publish message socket_state={self.socket_state}, reconnecting...")
                await self.connect_wss()
        else:
            _LOGGER.error(f"WebackApi (WSS) Failed to puslish message after {N_RETRY} retry")
        return False
    
    async def send_command(self, thing_name, sub_type, working_payload):
        """
        Pack command to send
        """
        _LOGGER.debug(f"WebackApi (WSS) send_command={working_payload} for robot={thing_name}")
        payload = {
            "topic_name": "$aws/things/" + thing_name + "/shadow/update",
            "opt": "send_to_device",
            "sub_type": sub_type,
            "topic_payload": {
                "state": working_payload
            },
            "thing_name": thing_name,
        }
        self._refresh_time = 5
        await self.publish_wss(payload)
        await self.force_cmd_refresh(thing_name, sub_type)
        return

    async def force_cmd_refresh(self, thing_name, sub_type):
        """ Force refresh """
        _LOGGER.debug(f"WebackApi (WSS) force refresh after sending cmd...")
        for i in range(4):
            await asyncio.sleep(0.6)
            await self.update_status(thing_name, sub_type)

    async def update_status(self, thing_name, sub_type):
        """
        Request to update robot status
        """
        _LOGGER.debug(f"WebackApi (WSS) update_status {thing_name}")
        payload = {
            "topic_name": "grit_tech/notify/server_2_device/" + thing_name,
            "opt": "sync_thing",
            "sub_type": sub_type,
            "topic_payload": {
                "notify_info": "sync_thing",
                "cmd_timestamp_s": int(time.time())
            },
            "thing_name": thing_name,
        }
        await self.publish_wss(payload)

    def adapt_refresh_time(self, status):
        """Adapt refreshing time depending on robot status"""
        _LOGGER.debug(f"WebackApi (WSS) adapt for : {status}")
        if 'working_status' in status:
            if status['working_status'] not in self.DOCKED_STATES:
                _LOGGER.debug("WebackApi (WSS) > Set refreshing to 5s")
                self._refresh_time = 5
                return
        _LOGGER.debug("WebackApi (WSS) > Set refreshing to 120s")
        self._refresh_time = 120
    
    async def refresh_handler(self, thing_name, sub_type):
        _LOGGER.debug("WebackApi (WSS) Start refresh_handler")
        while True:
            try:
                if self.socket_state != SOCK_CONNECTED:
                    await self.connect_wss()

                _LOGGER.debug(f"WebackApi (WSS) Refreshing...")
                await self.update_status(thing_name, sub_type)
                await asyncio.sleep(self._refresh_time)
            except Exception as e:
                _LOGGER.error(f"WebackApi (WSS) Error during refresh_handler (details={e})")

    def subscribe(self, subscriber):
        _LOGGER.debug("WebackApi (WSS): adding a new subscriber")
        self.subscriber.append(subscriber)

    def _call_subscriber(self):
        _LOGGER.debug("WebackApi (WSS): Calling subscriber (schedule_update_ha_state)")
        for subscriber in self.subscriber:
            subscriber(self)
