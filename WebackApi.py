import configparser
import hashlib
import json
import logging
import queue
import threading
import time
from datetime import datetime, timedelta

import httpx
import websocket

_LOGGER = logging.getLogger(__name__)

# Socket
SOCK_OPEN = "Open"
SOCK_CLOSE = "Close"
SOCK_ERROR = "Error"
SUCCESS_OK = 'success'

# API
AUTH_URL = "https://user.grit-cloud.com/prod/oauth"
ROBOT_UPDATE = "thing_status_update"
MAP_DATA = "map_data"
N_RETRY = 5
ACK_TIMEOUT = 5


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
        else:
            # Login NOK
            _LOGGER.error(f"WebackApi login failed (details : {resp})")
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
            config.set('weback_token', 'jwt_token', self.jwt_token)
            config.set('weback_token', 'token_exp', self.token_exp)
            config.set('weback_token', 'api_url', self.api_url)
            config.set('weback_token', 'wss_url', self.wss_url)
            config.set('weback_token', 'region_name', self.region_name)
            with open('weback_creds', 'wb') as configfile:
                config.write(configfile)
            _LOGGER.debug(f"WebackApi saved new creds")
        except:
            _LOGGER.debug(f"WebackApi failed to saved new creds")

    @staticmethod
    def check_token_is_valid(token: str) -> bool:
        """
        Check if token validity is still OK or not
        """
        _LOGGER.debug(f"WebackApi checking token validity : {token}")
        try:
            now_date = datetime.today()
            dt_token = datetime.strptime(token, "%Y-%d-%m %H:%M:%S.%f")
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
        _LOGGER.debug("WebackApi - robot list")

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

    @staticmethod
    async def send_http(url, **params):
        """
        Send HTTP request
        """
        _LOGGER.debug(f"Send HTTP request Url={url} Params={params}")
        timeout = httpx.Timeout(60.0, connect=60.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                for attempt in range(N_RETRY):
                    r = await client.post(url, **params)
                    if r.status_code == 200:
                        # Server status OK
                        _LOGGER.debug(f"WebackApi : Send HTTP OK, return=200")
                        _LOGGER.debug(f"WebackApi : HTTP data received = {r.json()}")
                        return r.json()
                    else:
                        # Server status NOK
                        _LOGGER.warning(f"WebackApi : Bad server response (status code={r.status_code}) retry... ({attempt}/{N_RETRY})")
                else:
                    _LOGGER.error(
                        f"WebackApi : Bad server response after {N_RETRY} retry (status code={r.status_code})")
                    return {"msg": "error", "details": f"bad response code={r.status_code}"}
        except httpx.RequestError as e:
            _LOGGER.error(f"Send HTTP exception details={e}")
            return {"msg": "error", "details": e}


# def null_callback(message):
#     _LOGGER.debug(f"WebackVacuumApi (WSS) null_callback: {message}")


class WebackWssCtrl:
    """
    WebSocket Weback API controller
    Handle websocket to send/receive robot control
    """
    def __init__(self, wss_url, region_name, jwt_token):
        _LOGGER.debug("WebackApi WSS Control __init__")
        self.ws = None
        self.authorization = "Basic KG51bGwpOihudWxsKQ=="
        self.socket_state = SOCK_CLOSE
        self.jwt_token = jwt_token
        self.region_name = region_name
        self.wss_url = wss_url
        self.robot_status = None
        self.wst = None
        self.ws = None
        self.recv_message = queue.Queue()

    async def connect_wss(self):
        """
        Connect WebSocket to Weback Server and create a thread to maintain connexion alive
        """
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
                                             on_error=self.on_error)
            
            self.wst = threading.Thread(target=self.ws.run_forever)
            self.wst.start()
            
            if self.wst.is_alive():
                _LOGGER.debug("WebackApi (WSS) Connecting...")
            else:
                _LOGGER.error("WebackApi (WSS) Thread connection init has FAILED")
                return False

        except Exception as e:
            self.socket_state = SOCK_ERROR
            _LOGGER.debug("WebackApi (WSS) Error while opening socket", e)
            return False
    
    def on_error(self, ws, error):
        """Socket "On_Error" event"""
        if error:
            details = f"(details : {error})"
        _LOGGER.debug(f"WebackApi (WSS) Error {details}")
        ws.close()
        self.socket_state = SOCK_ERROR

    def on_close(self, ws, close_status_code, close_msg):
        """Socket "On_Close" event"""
        if close_status_code or close_msg:
            details = f"(details : {close_status_code} / {close_msg})"
        _LOGGER.debug(f"WebackApi (WSS) Closed {details}")
        self.socket_state = SOCK_CLOSE
    
    def on_open(self, ws):
        """Socket "On_Open" event"""
        _LOGGER.debug(f"WebackApi (WSS) Connexion established OK")
        self.socket_state = SOCK_OPEN
    
    def on_message(self, ws, message):
        """Socket "On_Message" event"""
        wss_data = json.loads(message)
        _LOGGER.debug(f"WebackApi (WSS) Msg received {wss_data}")
        if wss_data["notify_info"] == ROBOT_UPDATE:
            self.recv_message.put(wss_data['thing_status'])
            self.robot_status = wss_data['thing_status']
            # self.update_callback(self.robot_status)
        elif wss_data["notify_info"] == MAP_DATA:
            # TODO : MAP support
            _LOGGER.debug(f"WebackApi (WSS) MAP data received")
        else:
            _LOGGER.error(f"WebackApi (WSS) Received an unknown message from server : {wss_data}")
    
    async def publish_wss(self, dict_message):
        """
        Publish payload over WSS connexion
        """
        json_message = json.dumps(dict_message)
        _LOGGER.debug(f"WebackApi (WSS) Publishing message : {json_message}")
        if self.socket_state != SOCK_OPEN:
            _LOGGER.debug(f"WebackApi (WSS) Not connected, state: {self.socket_state}, reconnecting...")
            await self.connect_wss()

        logging.debug(f"WebackApi (WSS) Thread was init, looking for cnx")

        for i in range(15):
            logging.debug(f"WebackApi (WSS) awaiting connexion established... {i}")
            if self.socket_state == SOCK_OPEN:
                break
            time.sleep(0.5)

        if self.socket_state == SOCK_OPEN:
            try:
                self.ws.send(json_message)
                _LOGGER.debug(f"WebackApi (WSS) Msg published OK")
                return True
            except websocket.WebSocketConnectionClosedException as e:
                _LOGGER.debug(f"WebackApi (WSS) Error while publishing message (details: {e})")
                self.socket_state = SOCK_CLOSE
        else:
            _LOGGER.debug(f"WebackApi (WSS) Error while publishing message, can't reconnect")
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
        await self.publish_wss(payload)
        time.sleep(2)
        return

    async def update_status(self, thing_name, sub_type):
        """
        Request to update robot status
        """
        _LOGGER.debug(f"WebackApi (WSS) update_status {thing_name}")
        payload = {
            "opt": "thing_status_get",
            "sub_type": sub_type,
            "thing_name": thing_name,
        }
        await self.publish_wss(payload)
        if await self.await_api_response():
            return True
        return False

    async def await_api_response(self):
        """
        Wait for receiving an API response from WSS
        """
        while True:
            _LOGGER.debug(f"WebackApi (WSS) awaiting response...")
            try:
                item = self.recv_message.get(timeout=ACK_TIMEOUT)
                if item is None:
                    _LOGGER.warning(f"WebackApi (WSS) awaiting timeout")
                    break
                # Response received
                self.recv_message.task_done()
                return True
            except Exception as error:
                _LOGGER.error(f"WebackApi (WSS) awaiting exception (details={error})")
        return False
