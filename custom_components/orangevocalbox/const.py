"""Constants for the component."""
ATTR_ID = "id"
ATTR_TYPE = "type"
DOMAIN = "orangevocalbox"
JSON_HEADER = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (HomeAssistant; +http://www.github.com/cyr-ius/hass-orangevocalbox) Firefox/1000",
}
ORANGE_URI = "https://login.orange.fr"
ORANGE_VOCALBOX_URI = "https://boitevocale5w.orange.fr/backend"
SERVICE_CLEAN = "clean"
VALUES_TYPE = ["missedCall", "voiceMsg", "all"]