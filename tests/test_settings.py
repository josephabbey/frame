import tempfile
from pathlib import Path

from frame.settings import Settings, SettingsStore


def test_settings_defaults_and_serialization():
    settings = Settings(frame_name="Living Room")

    assert settings.frame_name == "Living Room"
    data = settings.to_dict()
    assert data["frame_name"] == "Living Room"
    restored = Settings.from_dict(data)
    assert restored.frame_name == "Living Room"


def test_settings_store_lifecycle_and_atomicity():
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "sub" / "settings.json"
        store = SettingsStore(config_path)

        initial = store.load()
        assert config_path.exists()
        assert initial.frame_name == "Frame"

        notifications = []
        unsubscribe = store.add_listener(lambda s: notifications.append(s.frame_name))

        store.update(frame_name="Kitchen Display")
        assert len(notifications) == 1
        assert notifications[0] == "Kitchen Display"

        fresh_store = SettingsStore(config_path)
        loaded = fresh_store.load()
        assert loaded.frame_name == "Kitchen Display"

        unsubscribe()
        store.update(frame_name="Gallery")
        assert len(notifications) == 1
