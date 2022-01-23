"""Orange VocalBox API."""
import json
import logging
import requests
from datetime import datetime
from .const import ORANGE_URI, ORANGE_VOCALBOX_URI
from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)


class VocalBox:
    """Class for Vocal Box."""

    def __init__(self, mail: str, password: str, session=None):
        """Init variables."""
        self._session = session if session else ClientSession()
        self._messages = None
        self._mail = mail
        self._password = password

    async def async_connect(self) -> None:
        """Connect to Orange Vocal Box."""
        try:
            resp = await self._session.get(ORANGE_URI)
            if resp.status != 200:
                raise VocalboxError(
                    f"ERROR NotFound - HTTP {resp.status} ({resp.reason})",
                    "cannot_connect",
                )

            resp = await self._session.post(
                url=f"{ORANGE_URI}/api/login",
                data=json.dumps({"login": self._mail, "params": {}}),
            )
            if resp.status != 200:
                raise VocalboxError(
                    f"ERROR CheckLogin - HTTP {resp.status} ({resp.reason})",
                    "cannot_connect",
                )
            login = await resp.json()
            if login_encrypt := login.get("loginEncrypt"):
                resp = await self._session.post(
                    url=f"{ORANGE_URI}/api/password",
                    data=json.dumps(
                        {
                            "login": self._mail,
                            "loginEncrypt": login_encrypt,
                            "password": self._password,
                        }
                    ),
                )
                if resp.status != 200:
                    content = await resp.json()
                    raise VocalboxError(
                        f"CheckPass - HTTP {resp.status} ({content['message']})",
                        "login_inccorect",
                    )
        except requests.RequestException as error:
            raise VocalboxError("Request exception %s", error) from error

        return True

    async def async_fetch_datas(self):
        """Get messages in box."""
        if await self.async_connect() is False:
            raise VocalboxError("Connexion error", "fetch_data")

        try:
            self._messages = {"voiceMsg": [], "missedCall": []}
            resp = await self._session.get(url=f"{ORANGE_VOCALBOX_URI}/boxes")
            if resp.status != 200:
                raise VocalboxError(
                    f"ListBoxes - HTTP {resp.status} ({resp.reason})", "fetch_data"
                )
            rboxes = await resp.json()
            if len(rboxes) != 1:
                raise VocalboxError("ERROR Vocalbox not found", "fetch_data")
            mUri = rboxes[0].get("mainLine").get("messagesUri")
            self._messages.update({"messagesUri": mUri})

            self._session.headers.update(
                {
                    "MVF-organization": rboxes[0].get("organisation"),
                    "MVF-service": rboxes[0].get("service"),
                }
            )
            resp = await self._session.get(url=f"{ORANGE_VOCALBOX_URI}{mUri}")
            if resp.status != 200:
                raise VocalboxError(
                    f"ListMsg - HTTP {resp.status} ({resp.reason})", "fetch_data"
                )
            i = 0
            items = await resp.json()
            for item in items:
                i += 1
                message = {
                    "id": item.get("id"),
                    "lineid": i,
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
            self._messages.update({"last_seen": datetime.now()})
        except requests.RequestException as error:
            raise VocalboxError("Fetch exception %s", error) from error

        return self._messages

    async def async_delete_datas(self, id: int, type: str) -> None:
        """Delete message."""
        if await self.async_connect() is False:
            raise VocalboxError("Connexion error", "delete_datas")

        mUri = self._messages["messagesUri"]
        array_del_msg = [
            msg["id"]
            for msg in self._messages[type]
            if str(msg.get("lineid")) == str(id) or id == "all"
        ]

        try:
            resp = await self._session.delete(
                url=f"{ORANGE_VOCALBOX_URI}{mUri}", data=json.dumps(array_del_msg)
            )
            if resp.status != 200:
                raise VocalboxError(
                    f"ERROR DeleteMsg - HTTP {resp.status} ({resp.reason})",
                    "delete_datas",
                )
        except requests.RequestException as error:
            raise VocalboxError("Delete exception %s", error) from error


class VocalboxError(Exception):
    """General Orange Vocalbox exception occurred."""
