"""CL Control Web: isolated, native Home Assistant custom panel."""
from pathlib import Path
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.http import StaticPathConfig
from homeassistant.components import panel_custom
from .const import DOMAIN, STATIC_URL, PANEL_PATH, VERSION

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    directory = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(directory), True)]
    )
    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="cl-control-web-panel",
        frontend_url_path=PANEL_PATH,
        module_url=f"{STATIC_URL}/panel.js?v={VERSION}",
        sidebar_title="CL Control Next",
        sidebar_icon="mdi:home-automation",
        require_admin=False,
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from homeassistant.components import frontend
    frontend.async_remove_panel(hass, PANEL_PATH)
    return True
