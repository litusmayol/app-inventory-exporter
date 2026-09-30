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


def test_macos_branch_lists_app_bundles_from_applications():
    app = create_app_object()

    with patch.object(app_inventory.platform, "system", return_value="Darwin"), \
         patch.object(app_inventory.os.path, "exists", return_value=True), \
         patch.object(
             app_inventory.os,
             "listdir",
             return_value=["Safari.app", "Notes.app", "readme.txt"],
         ):
        content = app.generate_markdown_content()

    assert "| App macOS | /Applications | Safari |" in content
    assert "| App macOS | /Applications | Notes |" in content
    assert "readme.txt" not in content


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
