"""Support for Weback Vaccum Robots."""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.vacuum import (STATE_CLEANING, STATE_DOCKED,
                                             STATE_ERROR, STATE_IDLE,
                                             STATE_PAUSED, STATE_RETURNING,
                                             StateVacuumEntity,
                                             VacuumEntityFeature)
from homeassistant.helpers import entity_platform
from homeassistant.helpers.icon import icon_for_battery_level

from . import DOMAIN, VacDevice

_LOGGER = logging.getLogger(__name__)

STATE_MAPPING = {
    # STATE_CLEANING
    VacDevice.CLEAN_MODE_AUTO: STATE_CLEANING,
    VacDevice.CLEAN_MODE_EDGE: STATE_CLEANING,
    VacDevice.CLEAN_MODE_EDGE_DETECT: STATE_CLEANING,
    VacDevice.CLEAN_MODE_SPOT: STATE_CLEANING,
    VacDevice.CLEAN_MODE_SINGLE_ROOM: STATE_CLEANING,
    VacDevice.CLEAN_MODE_ROOMS: STATE_CLEANING,
    VacDevice.CLEAN_MODE_MOP: STATE_CLEANING,
    VacDevice.CLEAN_MODE_SMART: STATE_CLEANING,
    VacDevice.ROBOT_PLANNING_LOCATION: STATE_CLEANING,
    VacDevice.CLEAN_MODE_Z: STATE_CLEANING,
    VacDevice.DIRECTION_CONTROL: STATE_CLEANING,
    VacDevice.ROBOT_PLANNING_RECT: STATE_CLEANING,
    VacDevice.RELOCATION: STATE_CLEANING,
    
    # STATE_DOCKED
    VacDevice.CHARGE_MODE_CHARGING: STATE_DOCKED,
    VacDevice.CHARGE_MODE_DOCK_CHARGING: STATE_DOCKED,
    VacDevice.CHARGE_MODE_DIRECT_CHARGING: STATE_DOCKED,
    VacDevice.CHARGE_MODE_CHARGE_DONE: STATE_DOCKED,
    
    # STATE_PAUSED
    VacDevice.CLEAN_MODE_STOP: STATE_PAUSED,
    
    # STATE_IDLE
    VacDevice.IDLE_MODE: STATE_IDLE,
    VacDevice.IDLE_MODE_HIBERNATING: STATE_IDLE,
    
    # STATE_RETURNING
    VacDevice.CHARGE_MODE_RETURNING: STATE_RETURNING,
    
    # STATE_ERROR
    VacDevice.ROBOT_ERROR: STATE_ERROR,
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Weback robot vacuums."""
    vacuums = []
    for device in hass.data[DOMAIN]:
        vacuums.append(WebackVacuumRobot(device))
        hass.loop.create_task(device.watch_state())
    
    _LOGGER.debug("Adding Weback Vacuums to Home Assistant: %s", vacuums)
    async_add_entities(vacuums, False)


class WebackVacuumRobot(StateVacuumEntity):
    """
    Weback Vacuum
    """
    def __init__(self, device: VacDevice):
        """Initialize the Weback Vacuum."""
        self.device = device
        self.device.subscribe(lambda vacdevice: self.schedule_update_ha_state(False))
        self._error = None

        self._attr_supported_features = (
                VacuumEntityFeature.TURN_ON
                | VacuumEntityFeature.TURN_OFF
                | VacuumEntityFeature.STATUS
                | VacuumEntityFeature.BATTERY
                | VacuumEntityFeature.PAUSE
                | VacuumEntityFeature.STOP
                | VacuumEntityFeature.RETURN_HOME
                | VacuumEntityFeature.CLEAN_SPOT
                | VacuumEntityFeature.LOCATE
                | VacuumEntityFeature.START
                | VacuumEntityFeature.SEND_COMMAND
                | VacuumEntityFeature.FAN_SPEED
        )
        _LOGGER.info(f"Vacuum initialized: {self.name}")

    @property
    def should_poll(self) -> bool:
        """Async update should_poll set to False"""
        return False

    # ==========================================================
    # Vacuum Entity
    # -> Properties

    @property
    def name(self):
        """Return the name of the device."""
        return self.device.nickname

    @property
    def available(self):
        _LOGGER.debug(f"Vacuum: available={self.device.is_available}")
        """Returns true if vacuum is online"""
        return self.device.is_available

    @property
    def state(self):
        """Return the current state of the vacuum."""
        try:
            state_mapping = STATE_MAPPING[self.device.current_mode]
            _LOGGER.debug(f"Vacuum: state(from mapping)={state_mapping}")
            return state_mapping
        except KeyError:
            _LOGGER.error(f"Found an unsupported state, state_code: {self.device.current_mode}")
            return None

    @property
    def battery_level(self):
        """Return the battery level of the vacuum cleaner."""
        return self.device.battery_level

    @property
    def battery_icon(self):
        """Return the battery icon for the vacuum cleaner."""
        _LOGGER.debug(f"Vacuum: battery_icon battery_level={self.battery_level}, charging={self.is_charging}")
        return icon_for_battery_level(
            battery_level=self.battery_level, charging=self.is_charging
        )

    @property
    def fan_speed(self):
        """Return the fan speed of the vacuum cleaner."""
        # Check if robot is in Vacuum/Mop mode
        if self.device.vacuum_or_mop == 1:
            # Vacuum mode
            _LOGGER.debug(f"Vacuum: (vacuum mode) fan_speed={self.device.fan_status}")
            return self.device.fan_status
        elif self.device.vacuum_or_mop == 2:
            # Mop mode
            _LOGGER.debug(f"Vacuum: (mop mode) fan_speed={self.device.mop_status}")
            return self.device.mop_status
        else:
            # No Mop / No Fan
            _LOGGER.debug(f"Vacuum: no Fan / no Mop")
            return None

    @property
    def fan_speed_list(self):
        """Get the list of available fan speed or /water level steps of the vacuum cleaner."""
        # Check if robot is in Vacuum/Mop mode
        if self.device.vacuum_or_mop == 1:
            # Vacuum mode
            _LOGGER.debug(f"Vacuum: (vacuum mode) fan_speed_list={self.device.fan_speed_list}")
            return self.device.fan_speed_list
        elif self.device.vacuum_or_mop == 2:
            # Mop mode
            _LOGGER.debug(f"Vacuum: (mop mode) fan_speed_list={self.device.mop_level_list}")
            return self.device.mop_level_list
        else:
            # No Mop / No Fan
            _LOGGER.debug(f"Vacuum: no Fan / no Mop fan_speed_list=None")
            return None

    @property
    def error(self):
        _LOGGER.debug(f"Vacuum: error={self.device.error_info}")
        return self.device.error_info
    
    @property
    def unique_id(self) -> str:
        """Return an unique ID."""
        return self.device.name
    
    @property
    def is_on(self):
        """Return true if vacuum is currently cleaning."""
        _LOGGER.debug(f"Vacuum: is_on={self.device.is_cleaning}")
        return self.device.is_cleaning
    
    @property
    def is_charging(self):
        """Return true if vacuum is currently charging."""
        return self.device.is_charging
    
    @property
    def extra_state_attributes(self) -> dict:
        """Return the device-specific state attributes of this vacuum."""

        if self.device.vacuum_or_mop == 1:
            mode = "vacuum"
        else:
            mode = "mop"

        extra_value = {
            "robot_mode": mode,
            "error_info": self.device.error_info,
        }

        if 'volume' in self.device.robot_status:
            extra_value['volume'] = self.device.robot_status['volume']
            
        if 'voice' in self.device.robot_status:
            extra_value['voice'] = self.device.robot_status['voice']
            
        if 'undisturb_mode' in self.device.robot_status:
            extra_value['undisturb_mode'] = self.device.robot_status['undisturb_mode']

        if 'clean_area' in self.device.robot_status:
            clean_area = self.device.robot_status['clean_area']
            if clean_area is None:
                clean_area = 0
            extra_value['clean_area'] = round(clean_area, 1)

        if 'clean_time' in self.device.robot_status:
            clean_time = self.device.robot_status['clean_time']
            if clean_time is None:
                clean_time = 0
            extra_value['clean_time'] = round(clean_time / 60, 0),

        return extra_value


    # ==========================================================
    # Vacuum Entity
    # -> Method
    
    def on_error(self, error):
        """Handle robot's error"""
        if error == self.device.ROBOT_ERROR_NO:
            self._error = None
        else:
            self._error = error
        _LOGGER.debug(f"Vacuum: on_error={self._error}")
        self.hass.bus.fire("weback_vacuum", {"entity_id": self.entity_id, "error": error})
        self.schedule_update_ha_state(False)

    async def async_turn_on(self, **kwargs):
        """Turn the vacuum on and start cleaning."""
        _LOGGER.debug("Vacuum: turn_on")
        await self.device.turn_on()

    async def async_start(self, **kwargs):
        """Turn the vacuum on and start cleaning."""
        _LOGGER.debug("Vacuum: async_start")
        await self.device.turn_on()

    async def async_stop(self, **kwargs):
        """Stop the vacuum cleaner."""
        await self.device.return_to_base()

    async def async_turn_off(self, **kwargs):
        """Turn the vacuum off stopping the cleaning and returning home."""
        _LOGGER.debug("Vacuum: async_turn_off")
        self.return_to_base()

    async def async_return_to_base(self, **kwargs):
        """Set the vacuum cleaner to return to the dock."""
        _LOGGER.debug("Vacuum: return_to_base")
        await self.device.return_to_base()

    async def async_pause(self):
        """Pause the vacuum cleaner, do not return to base."""
        _LOGGER.debug("Vacuum: pause")
        await self.device.pause()

    async def async_locate(self, **kwargs) -> None:
        """Locate the vacuum cleaner."""
        _LOGGER.debug("Vacuum: locate")
        await self.device.locate()
        return

    async def async_set_fan_speed(self, fan_speed, **kwargs):
        """Set fan speed"""
        _LOGGER.debug(f"Vacuum: set_fan_speed (speed={fan_speed})")
        await self.device.set_fan_water_speed(fan_speed)

    async def async_clean_spot(self, **kwargs):
        """Perform a spot clean-up."""
        _LOGGER.debug("Vacuum: clean_spot")
        await self.device.clean_spot()
    
    async def async_goto_location(self, point: str):
        """Ask vacuum go to location point"""
        _LOGGER.debug(f"Vacuum: goto_location (point={point})")
        await self.device.goto(point)

    async def async_clean_rectangle(self, rectangle: str):
        """Perform a rectangle defined clean-up."""
        _LOGGER.debug(f"Vacuum: clean_rectangle (rectangle={rectangle})")
        await self.device.clean_rect(rectangle)

    async def async_send_command(self, command, params=None, **kwargs):
        """Send a command to a vacuum cleaner."""
        _LOGGER.debug(f"Vacuum: send_command (command={command} / params={params} / kwargs={kwargs})")
        if(command == 'app_segment_clean'):
            await self.device.clean_room(params)
        else:
            await self.device.send_command(self.name, self.sub, params)
