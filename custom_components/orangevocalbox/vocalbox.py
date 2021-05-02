"""Orange VocalBox API."""
import json
import logging
from functools import partial

from homeassistant.exceptions import ConfigEntryNotReady
from requests import Session
from requests.exceptions import RequestException

from .const import JSON_HEADER, ORANGE_URI, ORANGE_VOCALBOX_URI

_LOGGER = logging.getLogger(__name__)


class VocalBox:
    """Class for Vocal Box."""

    def __init__(self, hass):
        """Init variables."""
        self._hass = hass
        self._session = Session()
        self._session.headers = JSON_HEADER
        self._messages = None

    async def async_connect(self, mail, password):
        """Connect to Orange Vocal Box."""
        resp = await self._hass.async_add_executor_job(self._session.get, ORANGE_URI)
        if resp.status_code != 200:
            raise VocalboxError(
                f"ERROR NotFound - HTTP {resp.status_code} ({resp.reason})",
                "cannot_connect",
            )
        resp = await self._hass.async_add_executor_job(
            partial(
                self._session.post,
                url=f"{ORANGE_URI}/api/login",
                data=json.dumps({"login": mail, "params": {}}),
                cookies=resp.cookies,
            )
        )
        if resp.status_code != 200:
            raise VocalboxError(
                f"ERROR CheckLogin - HTTP {resp.status_code} ({resp.reason})",
                "cannot_connect",
            )

        login = resp.json()
        login_encrypt = login.get("loginEncrypt", None)
        password = {"login": mail, "loginEncrypt": login_encrypt, "password": password}
        if login_encrypt:
            resp = await self._hass.async_add_executor_job(
                partial(
                    self._session.post,
                    url=f"{ORANGE_URI}/api/password",
                    data=json.dumps(password),
                    cookies=resp.cookies,
                )
            )
            if resp.status_code != 200:
                content = resp.json()
                raise VocalboxError(
                    f"ERROR CheckPass - HTTP {resp.status_code} ({content['message']})",
                    "login_inccorect",
                )
                return False

        return True

    async def async_fetch_datas(self):
        """Get messages in box."""
        self._messages = {"voiceMsg": [], "missedCall": [], "messagesUri": None}
        resp = await self._hass.async_add_executor_job(
            partial(
                self._session.get,
                url=f"{ORANGE_VOCALBOX_URI}/boxes",
                cookies=self._session.cookies,
            )
        )
        if resp.status_code != 200:
            raise VocalboxError(
                f"ERROR ListBoxes - HTTP {resp.status_code} ({resp.reason})", "unknown"
            )
        rboxes = resp.json()
        if len(rboxes) != 1:
            raise VocalboxError("ERROR Vocalbox not found")

        self._messages["messagesUri"] = rboxes[0].get("mainLine").get("messagesUri")
        mUri = self._messages["messagesUri"]
        self._session.headers.update(
            {
                "MVF-organization": rboxes[0].get("organisation"),
                "MVF-service": rboxes[0].get("service"),
            }
        )
        resp = await self._hass.async_add_executor_job(
            partial(
                self._session.get,
                url=f"{ORANGE_VOCALBOX_URI}{mUri}",
                cookies=resp.cookies,
            )
        )
        if resp.status_code != 200:
            raise VocalboxError(
                f"ERROR ListMsg - HTTP {resp.status_code} ({resp.reason})", "unknown"
            )
        for item in resp.json():
            if item.get("read") is False:
                message = {
                    "id": item.get("id"),
                    "lineid": item.get("lineId"),
                    "datetime": item.get("timestamp"),
                    "type": item.get("type"),
                    "caller": item.get("caller"),
                    "duration": item.get("duration"),
                }
                if item.get("type") == "voiceMsg":
                    file = item.get("fileUri")
                    message.update({"mp3file": f"{ORANGE_VOCALBOX_URI}{file}"})
                    (self._messages["voiceMsg"]).append(message)
                    continue
                (self._messages["missedCall"]).append(message)

        return self._messages

    async def async_delete_datas(self, id, type):
        """Delete message."""
        mUri = self._messages["messagesUri"]
        array_del_msg = [
            msg["id"]
            for msg in self._messages[type]
            if msg.get("lineid") == str(id) or id == "all"
        ]
        resp = await self._hass.async_add_executor_job(
            partial(
                self._session.delete,
                url=f"{ORANGE_VOCALBOX_URI}{mUri}",
                data=json.dumps(array_del_msg),
                cookies=self._session.cookies,
            )
        )
        if resp.status_code != 200:
            raise VocalboxError(
                f"ERROR DeleteMsg - HTTP {resp.status_code} ({resp.reason})", "unknown"
            )


class VocalboxError(Exception):
    """General Orange Vocalbox exception occurred."""
