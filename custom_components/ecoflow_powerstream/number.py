import logging
import time
import requests
import base64
from paho.mqtt import client as mqtt_client
from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from .const import DOMAIN

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
        try:
            self._mqtt_data = self.get_ecoflow_mqtt_data()
            self._client = self.connect_mqtt()
            LOG.debug("Init entity OK avec MQTT data: %s", self._mqtt_data)
        except Exception as e:
            LOG.error("Erreur init entity (auth ou connexion): %s", e)

    def get_ecoflow_mqtt_data(self):
        url = "https://api.ecoflow.com/auth/login"
        data = {
            "email": self._config["email"],
            "password": base64.b64encode(self._config["password"].encode()).decode(),
            "scene": "IOT_APP",
            "userType": "ECOFLOW"
        }
        response = requests.post(url, json=data)
        response.raise_for_status()
        token = response.json()["data"]["token"]
        userid = response.json()["data"]["user"]["userId"]

        url_cert = f"https://api.ecoflow.com/iot-auth/app/certification?userId={userid}"
        headers = {"Authorization": f"Bearer {token}"}
        response_cert = requests.get(url_cert, headers=headers)
        response_cert.raise_for_status()
        cert_data = response_cert.json()["data"]
        return {
            "url": cert_data["url"],
            "port": int(cert_data["port"]),
            "user": cert_data["certificateAccount"],
            "password": cert_data["certificatePassword"],
            "client_id": f"ANDROID_{int(time.time())}_{userid}",
            "user_id": userid
        }

    def connect_mqtt(self):
        client = mqtt_client.Client(self._mqtt_data["client_id"])
        client.username_pw_set(self._mqtt_data["user"], self._mqtt_data["password"])
        client.connect(self._mqtt_data["url"], self._mqtt_data["port"], 60)
        client.loop_start()
        return client

    @property
    def native_value(self):
        return self._state

    def set_native_value(self, value):
        if self._mqtt_data is None or self._client is None:
            LOG.error("MQTT non initialisé - Vérifiez creds EcoFlow ou connexion")
            return  # Ne rien faire si init a échoué

        try:
            dynset = int(value) * 10
            # Préparez le message
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

            # Encode en Protobuf (simplifié)
            from google.protobuf import struct_pb2 as struct
            proto_msg = struct.Struct()
            proto_msg.update(muster_set_ac)
            buffer = proto_msg.SerializeToString()

            topic = f"/app/{self._mqtt_data['user_id']}/{self._config['serial_number']}/thing/property/set"
            self._client.publish(topic, buffer, qos=1)
            LOG.info(f"Injection envoyée : {dynset / 10}")
            self._state = value
            self.async_write_ha_state()
        except Exception as e:
            LOG.error("Erreur set_value: %s", e)
