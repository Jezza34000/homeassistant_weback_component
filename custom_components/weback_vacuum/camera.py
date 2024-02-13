"""Support for Weback Vacuum Robot map camera."""

from __future__ import annotations

import logging

from homeassistant.components.camera import (
    ENTITY_ID_FORMAT,
    Camera,
)
from homeassistant.helpers.entity import generate_entity_id

from . import DOMAIN, VacDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the camera entities for each robot"""
    vacuums = []

    for device in hass.data[DOMAIN]:
        entity_id = generate_entity_id(ENTITY_ID_FORMAT, device.name, hass=hass)
        vacuums.append(WebackVacuumCamera(device, entity_id))

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
        self._vacdevice.register_map_camera(self)
        self.content_type = "image/png"
        self._error = None
        _LOGGER.info("Vacuum Camera initialized: %s", self.name)

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
        if self._vacdevice.map is not None:
            attributes["calibration_points"] = self._vacdevice.map.calibration_points()
            attributes["rooms"] = self._vacdevice.map.get_predefined_selections()

        return attributes

    def camera_image(
        self,
        width: int | None = None,
        height: int | None = None,
    ) -> bytes | None:
        """Return bytes of camera image."""
        if self._vacdevice.map:
            return self.generate_image()
        return None

    def generate_image(self):
        return self._vacdevice.map_image_buffer
