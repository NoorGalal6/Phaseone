
from config.config_manager import ConfigManager


def test_switch_profile(monkeypatch):
    config = ConfigManager()

    # Prevent changes to the real settings.json file
    monkeypatch.setattr(config, "save_settings", lambda: None)

    result = config.switch_profile("operator_2")

    assert result is True
    assert config.get_active_profile()["keyboard"]["forward"] == "up"


def test_invalid_profile():
    config = ConfigManager()

    result = config.switch_profile("unknown")

    assert result is False


def test_load_controller_profile(monkeypatch):
    config = ConfigManager()

    config.settings["controller_profiles"] = {
        "Xbox Controller": "default"
    }

    # Prevent changes to the real settings.json file
    monkeypatch.setattr(config, "save_settings", lambda: None)

    result = config.load_controller_profile("Xbox Controller")

    assert result is True
    assert config.settings["active_profile"] == "default"
    assert config.get_active_profile()["keyboard"]["forward"] == "w"
