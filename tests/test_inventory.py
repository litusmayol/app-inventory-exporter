import pytest
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import patch


# The application imports Tkinter at module import time.
# These lightweight stubs allow the inventory logic to be tested
# independently from the graphical interface.
tkinter_stub = types.ModuleType("tkinter")
tkinter_stub.Tk = object

ttk_stub = types.ModuleType("tkinter.ttk")
filedialog_stub = types.ModuleType("tkinter.filedialog")
messagebox_stub = types.ModuleType("tkinter.messagebox")

tkinter_stub.ttk = ttk_stub
tkinter_stub.filedialog = filedialog_stub
tkinter_stub.messagebox = messagebox_stub

sys.modules.setdefault("tkinter", tkinter_stub)
sys.modules.setdefault("tkinter.ttk", ttk_stub)
sys.modules.setdefault("tkinter.filedialog", filedialog_stub)
sys.modules.setdefault("tkinter.messagebox", messagebox_stub)


PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

MODULE_PATH = PROJECT_ROOT / "app_inventory.py"

spec = importlib.util.spec_from_file_location("app_inventory", MODULE_PATH)
app_inventory = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(app_inventory)


def create_app_object():
    return object.__new__(app_inventory.AppInventoryGUI)


def test_windows_branch_formats_collector_results():
    app = create_app_object()

    applications = [
        {
            "name": "Example App",
            "version": "2.5.0",
            "publisher": "Example Ltd",
            "install_location": r"C:\\Program Files\\Example App",
            "source": "Windows Registry",
        }
    ]

    with patch.object(app_inventory.platform, "system", return_value="Windows"), \
         patch.object(
             app_inventory,
             "collect_windows_applications",
             return_value=applications,
         ):
        content = app.generate_markdown_content()

    assert "| Windows | Registry | Example App |" in content
    assert "Versió: 2.5.0" in content
    assert "Editor: Example Ltd" in content


def test_macos_branch_formats_collector_results():
    app = create_app_object()

    applications = [
        {
            "name": "Safari",
            "version": "18.0",
            "publisher": "",
            "install_location": "/Applications/Safari.app",
            "bundle_identifier": "com.apple.Safari",
            "source": "macOS Application Bundle",
        }
    ]

    with patch.object(app_inventory.platform, "system", return_value="Darwin"), \
         patch.object(
             app_inventory,
             "collect_macos_applications",
             return_value=applications,
         ):
        content = app.generate_markdown_content()

    assert "| App macOS | Application Bundle | Safari |" in content
    assert "Versió: 18.0" in content
    assert "Identificador: com.apple.Safari" in content


def test_linux_branch_collects_apt_packages():
    app = create_app_object()

    with patch.object(app_inventory.platform, "system", return_value="Linux"), \
         patch.object(
             app_inventory.subprocess,
             "check_output",
             side_effect=[
                 "python3\nvim\n",
                 "Name Version Rev Tracking Publisher Notes\n",
             ],
         ), \
         patch.object(
             app_inventory.subprocess,
             "run",
             return_value=types.SimpleNamespace(
                 stdout="A package description\n",
                 returncode=0,
             ),
         ):
        content = app.generate_markdown_content()

    assert "| APT |" in content
    assert "python3" in content
    assert "vim" in content


def test_generated_content_contains_markdown_table():
    app = create_app_object()

    with patch.object(app_inventory.platform, "system", return_value="Windows"), \
         patch.object(
             app_inventory,
             "collect_windows_applications",
             return_value=[],
         ):
        content = app.generate_markdown_content()

    assert "| Tipus | Data / Font | Nom | Descripció |" in content
    assert content.startswith("# Llistat d'aplicacions")


class FakeRegistryKey:
    def __init__(self, values=None, subkeys=None):
        self.values = values or {}
        self.subkeys = subkeys or {}


class FakeRegistry:
    HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
    HKEY_LOCAL_MACHINE = "HKEY_LOCAL_MACHINE"
    KEY_READ = 1

    def __init__(self):
        uninstall_path = (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        )

        self.roots = {
            self.HKEY_CURRENT_USER: FakeRegistryKey(),
            self.HKEY_LOCAL_MACHINE: FakeRegistryKey(
                subkeys={
                    uninstall_path: FakeRegistryKey(
                        subkeys={
                            "ExampleApp": FakeRegistryKey(
                                values={
                                    "DisplayName": "Example App",
                                    "DisplayVersion": "2.5.0",
                                    "Publisher": "Example Ltd",
                                    "InstallLocation": (
                                        r"C:\Program Files\Example App"
                                    ),
                                }
                            ),
                            "SecondApp": FakeRegistryKey(
                                values={
                                    "DisplayName": "Second App",
                                    "DisplayVersion": "1.0",
                                    "Publisher": "Another Ltd",
                                }
                            ),
                        }
                    )
                }
            ),
        }

    def OpenKey(self, root_or_key, path, reserved=0, access=0):
        try:
            if isinstance(root_or_key, FakeRegistryKey):
                return root_or_key.subkeys[path]

            return self.roots[root_or_key].subkeys[path]
        except KeyError as error:
            raise OSError from error

    def QueryInfoKey(self, key):
        return (len(key.subkeys), 0, 0)

    def EnumKey(self, key, index):
        return list(key.subkeys.keys())[index]

    def QueryValueEx(self, key, value_name):
        if value_name not in key.values:
            raise OSError

        return key.values[value_name], None

    def CloseKey(self, key):
        return None


def test_windows_collector_reads_installed_applications():
    from inventory_collectors import collect_windows_applications

    registry = FakeRegistry()
    applications = collect_windows_applications(registry_module=registry)

    assert applications == [
        {
            "name": "Example App",
            "version": "2.5.0",
            "publisher": "Example Ltd",
            "install_location": r"C:\Program Files\Example App",
            "source": "Windows Registry",
        },
        {
            "name": "Second App",
            "version": "1.0",
            "publisher": "Another Ltd",
            "install_location": "",
            "source": "Windows Registry",
        },
    ]


def test_macos_collector_reads_bundle_metadata(tmp_path):
    from inventory_collectors import collect_macos_applications

    applications_directory = tmp_path / "Applications"
    application_bundle = applications_directory / "Example.app"
    contents_directory = application_bundle / "Contents"
    contents_directory.mkdir(parents=True)

    plist_path = contents_directory / "Info.plist"

    import plistlib

    plist_data = {
        "CFBundleDisplayName": "Example Application",
        "CFBundleShortVersionString": "3.2.1",
        "CFBundleIdentifier": "com.example.application",
    }

    with plist_path.open("wb") as plist_file:
        plistlib.dump(plist_data, plist_file)

    applications = collect_macos_applications(
        application_directories=(applications_directory,)
    )

    assert applications == [
        {
            "name": "Example Application",
            "version": "3.2.1",
            "publisher": "",
            "install_location": str(application_bundle),
            "bundle_identifier": "com.example.application",
            "source": "macOS Application Bundle",
        }
    ]


def test_headless_export_writes_active_destinations(tmp_path):
    import json

    first_directory = tmp_path / "first"
    second_directory = tmp_path / "second"
    inactive_directory = tmp_path / "inactive"

    config_path = tmp_path / "config.json"
    config_data = {
        "destinations": [
            {
                "active": True,
                "dir": str(first_directory),
                "file": "first-export",
            },
            {
                "active": True,
                "dir": str(second_directory),
                "file": "second-export.md",
            },
            {
                "active": False,
                "dir": str(inactive_directory),
                "file": "inactive.md",
            },
        ]
    }

    config_path.write_text(
        json.dumps(config_data),
        encoding="utf-8",
    )

    with patch.object(
        app_inventory.platform,
        "system",
        return_value="Windows",
    ), patch.object(
        app_inventory,
        "collect_windows_applications",
        return_value=[],
    ):
        written_count = app_inventory.export_from_config(config_path)

    assert written_count == 2
    assert (first_directory / "first-export.md").exists()
    assert (second_directory / "second-export.md").exists()
    assert not inactive_directory.exists()


def test_frequency_labels_convert_to_canonical_keys():
    assert app_inventory.frequency_key_from_value("Manual") == "manual"
    assert app_inventory.frequency_key_from_value("Cada hora") == "hourly"
    assert app_inventory.frequency_key_from_value("Every 6 hours") == "six_hourly"
    assert app_inventory.frequency_key_from_value("Diario") == "daily"
    assert (
        app_inventory.frequency_key_from_value("On system startup")
        == "startup"
    )


def test_frequency_labels_are_translated_from_canonical_keys():
    assert app_inventory.frequency_label_for("Català", "hourly") == "Cada hora"
    assert app_inventory.frequency_label_for("English", "daily") == "Daily"
    assert (
        app_inventory.frequency_label_for("Español", "startup")
        == "Al iniciar el sistema"
    )


def test_unknown_frequency_defaults_to_manual():
    assert app_inventory.frequency_key_from_value("unknown") == "manual"


def test_linux_scheduler_builds_hourly_units(tmp_path):
    from linux_scheduler import (
        build_service_content,
        build_timer_content,
        scheduler_paths,
        write_scheduler_files,
    )

    service_content = build_service_content(
        application_path=tmp_path / "app_inventory.py",
        python_executable="/usr/bin/python3",
    )
    timer_content = build_timer_content("hourly")

    assert "app_inventory.py" in service_content
    assert "--export" in service_content
    assert "OnActiveSec=1min" in timer_content
    assert "OnUnitActiveSec=1h" in timer_content

    with patch("linux_scheduler.platform.system", return_value="Linux"):
        paths = write_scheduler_files(
            "hourly",
            application_path=tmp_path / "app_inventory.py",
            python_executable="/usr/bin/python3",
            home_directory=tmp_path / "home",
        )

    assert paths["service"].exists()
    assert paths["timer"].exists()
    assert "OnUnitActiveSec=1h" in paths["timer"].read_text()


def test_linux_scheduler_builds_startup_timer(tmp_path):
    from linux_scheduler import build_timer_content

    content = build_timer_content("startup")

    assert "OnBootSec=1min" in content
    assert "Persistent=true" in content


def test_linux_scheduler_rejects_invalid_frequency():
    from linux_scheduler import build_timer_content

    with pytest.raises(ValueError):
        build_timer_content("manual")


def test_scheduler_wrapper_uses_canonical_frequency(tmp_path):
    with patch.object(
        app_inventory.platform,
        "system",
        return_value="Linux",
    ), patch.object(
        app_inventory,
        "configure_linux_scheduler",
        return_value={"timer": tmp_path / "app-inventory-exporter.timer"},
    ) as scheduler:
        result = app_inventory.configure_scheduler_for_frequency(
            "Cada 6 hores"
        )

    scheduler.assert_called_once_with(
        frequency="six_hourly",
        application_path=app_inventory.os.path.abspath(app_inventory.__file__),
        python_executable=app_inventory.sys.executable,
        activate=False,
    )
    assert result["timer"].name == "app-inventory-exporter.timer"


def test_scheduler_wrapper_does_nothing_on_non_linux():
    with patch.object(
        app_inventory.platform,
        "system",
        return_value="Windows",
    ), patch.object(app_inventory, "configure_linux_scheduler") as scheduler:
        result = app_inventory.configure_scheduler_for_frequency("hourly")

    assert result is None
    scheduler.assert_not_called()
