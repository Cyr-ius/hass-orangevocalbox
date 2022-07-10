"""VocalBox binary sensor entities."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Defer binary sensor setup to the shared sensor module."""
    coordinator = hass.data[DOMAIN]
    async_add_entities([VocalStatus(coordinator), MissedStatus(coordinator)])


class VocalStatus(CoordinatorEntity, BinarySensorEntity):
    """Representation of a VocalMsg sensor."""

    _attr_name = "Vocal Message"
    _attr_unique_id = "voicemsg_status"

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return len(self.coordinator.data.get("voiceMsg", [])) != 0

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        messages = []
        for attr in self.coordinator.data.get("voiceMsg"):
            messages.append(
                {
                    "id": attr["lineid"],
                    "phone_number": attr["caller"],
                    "datetime": attr["datetime"],
                    "duration": attr["duration"],
                    "link": attr["mp3file"],
                }
            )
        return {"messages": messages}


class MissedStatus(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Missed call sensor."""

    _attr_name = "Missed caller"
    _attr_unique_id = "missedCall_status"

    def __init__(self, coordinator):
        """Initialize the sensor."""
        self.coordinator = coordinator

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return len(self.coordinator.data.get("missedCall", [])) != 0

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        misscall = []
        for attr in self.coordinator.data.get("missedCall"):
            misscall.append(
                {
                    "id": attr["lineid"],
                    "phone_number": attr["caller"],
                    "datetime": attr["datetime"],
                }
            )
        return {"messages": misscall}
