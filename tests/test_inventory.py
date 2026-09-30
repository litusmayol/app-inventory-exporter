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


MODULE_PATH = Path(__file__).parents[1] / "app_inventory.py"

spec = importlib.util.spec_from_file_location("app_inventory", MODULE_PATH)
app_inventory = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(app_inventory)


def create_app_object():
    return object.__new__(app_inventory.AppInventoryGUI)


def test_windows_branch_currently_returns_placeholder_row():
    app = create_app_object()

    with patch.object(app_inventory.platform, "system", return_value="Windows"):
        content = app.generate_markdown_content()

    assert "| Windows |" in content
    assert "Programari Windows" in content


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

    with patch.object(app_inventory.platform, "system", return_value="Windows"):
        content = app.generate_markdown_content()

    assert "| Tipus | Data / Font | Nom | Descripció |" in content
    assert content.startswith("# Llistat d'aplicacions")
