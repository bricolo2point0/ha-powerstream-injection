import logging
import time
import base64
from paho.mqtt import client as mqtt_client
from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from .const import DOMAIN
import aiohttp

LOG = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    config = hass.data[DOMAIN][entry.entry_id]
    LOG.debug("Setup number entity avec config: %s", config)
    async_add_entities([PowerStreamInjectionEntity(config)])

class PowerStreamInjectionEntity(NumberEntity):
    def __init__(self, config):
        self._config = config
        self._attr_name = "PowerStream Injection"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 8000
        self._attr_native_step = 10
        self._state = 0
        self._mqtt_data = None
        self._client = None

    async def async_added_to_hass(self):
        try:
            self._mqtt_data = await self.get_ecoflow_mqtt_data()
            self._client = self.connect_mqtt()
            LOG.debug("Init async entity OK")
        except Exception as e:
            LOG.error("Erreur init async entity: %s", e)

    async def get_ecoflow_mqtt_data(self):
        try:
            LOG.debug("Début auth EcoFlow avec email: %s", self._config["email"])
            url = "https://api.ecoflow.com/auth/login"
            data = {
                "email": self._config["email"],
                "password": base64.b64encode(self._config["password"].encode()).decode(),
                "scene": "IOT_APP",
                "userType": "ECOFLOW"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    response.raise_for_status()
                    resp_json = await response.json()
                    token = resp_json["data"]["token"]
                    userid = resp_json["data"]["user"]["userId"]
                    LOG.debug("Auth login OK, userid: %s", userid)

            url_cert = f"https://api.ecoflow.com/iot-auth/app/certification?userId={userid}"
            headers = {"Authorization": f"Bearer {token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url_cert, headers=headers) as response:
                    response.raise_for_status()
                    resp_json = await response.json()
                    cert_data = resp_json["data"]
                    LOG.debug("Auth cert OK: %s", cert_data)
                    return {
                        "url": cert_data["url"],
                        "port": int(cert_data["port"]),
                        "user": cert_data["certificateAccount"],
                        "password": cert_data["certificatePassword"],
                        "client_id": f"ANDROID_{int(time.time())}_{userid}",
                        "user_id": userid
                    }
        except aiohttp.ClientError as e:
            LOG.error("Erreur réseau/auth EcoFlow:
