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
        LOG.debug("Init entity with config: %s", config)

    async def async_added_to_hass(self):
        LOG.debug("async_added_to_hass appelée")
        try:
            self._mqtt_data = await self.get_ecoflow_mqtt_data()
            self._client = self.connect_mqtt()
            LOG.debug("Init async entity OK")
        except Exception as e:
            LOG.error("Erreur init async entity: %s", e)

    async def get_ecoflow_mqtt_data(self):
        # Code auth (inchangé, avec logs)
        # ...

    def connect_mqtt(self):
        # Code MQTT (inchangé)
        # ...

    @property
    def native_value(self):
        LOG.debug("native_value appelée, retour: %s", self._state)
        return self._state

    def set_native_value(self, value):
        LOG.debug("set_native_value appelée avec value: %s", value)
        if self._mqtt_data is None or self._client is None:
            LOG.error("MQTT non initialisé - Vérifiez creds EcoFlow ou connexion")
            return

        try:
            dynset = int(value) * 10
            LOG.debug("Dynset calculé: %s", dynset)
            # Code message et publish (inchangé)
            # ...
            LOG.info(f"Injection envoyée : {dynset / 10}")
            self._state = value
            self.async_write_ha_state()
        except Exception as e:
            LOG.error("Erreur set_value: %s", e)
