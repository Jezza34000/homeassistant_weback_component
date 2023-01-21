"""Support for Weback Vacuum Robot map camera."""
import logging
import resource
import time

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.vacuum import (STATE_CLEANING, STATE_DOCKED,
                                             STATE_ERROR, STATE_IDLE,
                                             STATE_PAUSED, STATE_RETURNING,
                                             StateVacuumEntity,
                                             VacuumEntityFeature)
from homeassistant.helpers import entity_platform
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.components.camera import Camera, ENTITY_ID_FORMAT, PLATFORM_SCHEMA, SUPPORT_ON_OFF, CameraEntityFeature

from . import DOMAIN, VacDevice
from .VacMap import VacMap, VacMapDraw

import io

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the camera entities for each robot"""
    vacuums = []
    
    for device in hass.data[DOMAIN]:
        entity_id = generate_entity_id(ENTITY_ID_FORMAT, device.name, hass=hass)
        vacuums.append(WebackVacuumCamera(device, entity_id))
        hass.loop.create_task(device.watch_state())
    
    _LOGGER.debug("Adding Weback Vacuums Maps to Home Assistant: %s", vacuums)

    async_add_entities(vacuums)

class WebackVacuumCamera(Camera):
    """
    Weback Camera
    """
    def __init__(self, device: VacDevice, entity_id):
        """Initialize the Weback Vacuum Map"""
        super().__init__()
        self._vacdevice = device
        # self.entity_id = entity_id
        self.content_type = "image/png"
        
        # self._vacdevice.subscribe(lambda vacdevice: self.schedule_update_ha_state(False))
        
        self._error = None 

        # self._attr_supported_features = ()
        _LOGGER.info(f"Vacuum Camera initialized: {self.name}")
    
    @property
    def name(self):
        """Return the name of the device."""
        return self._vacdevice.nickname + " Map"
    
    @property
    def unique_id(self) -> str:
        """Return an unique ID."""
        return self._vacdevice.name + "_map"

    @property
    def extra_state_attributes(self):
        attributes = {}
        if(self._vacdevice.map is not None):
            attributes["calibration_points"] = self._vacdevice.map.calibration_points()
            attributes["rooms"] = self._vacdevice.map.get_predefined_selections()


        return attributes

    def camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        if(self._vacdevice.map):
            return self.generate_image()
        else:
            return None

    def generate_image(self):
        return self._vacdevice.map_image_buffer
