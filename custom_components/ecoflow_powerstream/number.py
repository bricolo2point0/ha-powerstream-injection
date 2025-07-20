import logging
import time
import base64
from paho.mqtt import client as mqtt_client
from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from .const import DOMAIN
import aiohttp
from google.protobuf import descriptor_pool, message_factory, symbol_database

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
        # Code auth (inchangé)
        # ...

    def connect_mqtt(self):
        # Code MQTT (inchangé, avec callback_api_version)
        # ...

    @property
    def native_value(self):
        return self._state

    def set_native_value(self, value):
        if self._mqtt_data is None or self._client is None:
            LOG.error("MQTT non initialisé - Vérifiez creds EcoFlow ou connexion")
            return

        try:
            dynset = int(value) * 10
            LOG.debug("Dynset calculé: %s", dynset)

            # Message
            muster_set_ac = {
                "header": {
                    "pdata": {"value": dynset},
                    "src": 32,
                    "dest": 53,
                    "dSrc": 1,
                    "dDest": 1,
                    "checkType": 3,
                    "cmdFunc": 20,
                    "cmdId": 129,
                    "dataLen": 3,
                    "needAck": 1,
                    "seq": int(time.time()),
                    "version": 19,
                    "payloadVer": 1,
                    "from": 'ios',
                    "deviceSn": self._config["serial_number"]
                }
            }
            LOG.debug("Message préparé: %s", muster_set_ac)

            # Compilation et encoding Protobuf (plus précis avec votre proto)
            pool = descriptor_pool.Default()
            # Ajoutez votre protoSource2 ici (simplifié ; étendez si besoin)
            desc = pool.AddSerializedFile(b'votre_proto_compilée')  # Compilez votre protoSource2 avec protoc et ajoutez le .pb
            factory = message_factory.MessageFactory(pool)
            msg_type = factory.GetPrototype(pool.FindMessageTypeByName('setMessage'))
            proto_msg = msg_type()
            # Remplissez proto_msg avec muster_set_ac (adaptez les champs)
            buffer = proto_msg.SerializeToString()
            LOG.debug("Protobuf encodé OK, buffer: %s", buffer)

            topic = f"/app/{self._mqtt_data['user_id']}/{self._config['serial_number']}/thing/property/set"
            LOG.debug("Topic: %s", topic)
            self._client.publish(topic, buffer, qos=1)
            LOG.debug("Publish effectué")

            LOG.info(f"Injection envoyée : {dynset / 10}")
            self._state = value
            self.async_write_ha_state()
        except Exception as e:
            LOG.error("Erreur set_value: %s", e)
