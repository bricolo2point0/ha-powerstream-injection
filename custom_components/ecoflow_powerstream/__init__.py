import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

PLATFORMS = ["number"]  # Plateformes supportées (ici, number pour l'injection)

LOG = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    try:
        hass.data.setdefault(DOMAIN, {})
        # Stockez les configs saisies via UI (email, pass, serial)
        hass.data[DOMAIN][entry.entry_id] = entry.data
        LOG.debug("Setup entry OK avec data: %s", entry.data)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    except Exception as e:
        LOG.error("Erreur setup entry: %s", e)
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
