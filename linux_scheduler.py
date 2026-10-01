import os
import platform
import shlex
import subprocess
import sys
from pathlib import Path


SERVICE_NAME = "app-inventory-exporter.service"
TIMER_NAME = "app-inventory-exporter.timer"

FREQUENCY_INTERVALS = {
    "hourly": "1h",
    "six_hourly": "6h",
    "daily": "1d",
}


def systemd_user_directory(home_directory=None):
    home = Path(home_directory or Path.home())
    return home / ".config" / "systemd" / "user"


def scheduler_paths(home_directory=None):
    directory = systemd_user_directory(home_directory)
    return {
        "directory": directory,
        "service": directory / SERVICE_NAME,
        "timer": directory / TIMER_NAME,
    }


def build_service_content(
    application_path=None,
    python_executable=None,
):
    """Build a user-level systemd service for headless export."""
    application = Path(
        application_path
        or Path(__file__).resolve().with_name("app_inventory.py")
    ).resolve()

    executable = Path(python_executable or sys.executable).resolve()

    command = " ".join(
        (
            shlex.quote(str(executable)),
            shlex.quote(str(application)),
            "--export",
        )
    )

    return f"""[Unit]
Description=Export installed applications to Markdown

[Service]
Type=oneshot
ExecStart={command}
"""


def build_timer_content(frequency):
    """Build a timer unit for a canonical frequency key."""
    if frequency == "startup":
        schedule = "OnBootSec=1min"
    elif frequency in FREQUENCY_INTERVALS:
        interval = FREQUENCY_INTERVALS[frequency]
        schedule = f"OnUnitActiveSec={interval}"
    else:
        raise ValueError(f"Unsupported automatic frequency: {frequency}")

    return f"""[Unit]
Description=Schedule installed application export

[Timer]
{schedule}
Persistent=true
Unit={SERVICE_NAME}

[Install]
WantedBy=default.target
"""


def write_scheduler_files(
    frequency,
    application_path=None,
    python_executable=None,
    home_directory=None,
):
    """Write service/timer files and return their paths.

    This does not enable or start the timer.
    """
    if platform.system() != "Linux":
        raise RuntimeError("The systemd scheduler is only supported on Linux.")

    paths = scheduler_paths(home_directory)
    paths["directory"].mkdir(parents=True, exist_ok=True)

    paths["service"].write_text(
        build_service_content(application_path, python_executable),
        encoding="utf-8",
    )
    paths["timer"].write_text(
        build_timer_content(frequency),
        encoding="utf-8",
    )

    return paths


def remove_scheduler_files(home_directory=None):
    """Remove the service and timer files without calling systemctl."""
    paths = scheduler_paths(home_directory)

    for key in ("service", "timer"):
        paths[key].unlink(missing_ok=True)

    return paths


def reload_user_systemd():
    """Ask the current user systemd manager to reload unit files."""
    subprocess.run(
        ["systemctl", "--user", "daemon-reload"],
        check=True,
    )


def enable_and_start_timer():
    """Enable and start the configured timer for the current user."""
    subprocess.run(
        [
            "systemctl",
            "--user",
            "enable",
            "--now",
            TIMER_NAME,
        ],
        check=True,
    )


def disable_and_stop_timer():
    """Stop and disable the timer for the current user."""
    subprocess.run(
        [
            "systemctl",
            "--user",
            "disable",
            "--now",
            TIMER_NAME,
        ],
        check=False,
    )


def configure_linux_scheduler(
    frequency,
    application_path=None,
    python_executable=None,
    home_directory=None,
    activate=False,
):
    """Configure or remove the scheduler.

    By default, this only writes or removes files. Pass activate=True
    only after the generated files have been inspected.
    """
    if frequency == "manual":
        disable_and_stop_timer()
        paths = remove_scheduler_files(home_directory)
        reload_user_systemd()
        return paths

    paths = write_scheduler_files(
        frequency=frequency,
        application_path=application_path,
        python_executable=python_executable,
        home_directory=home_directory,
    )

    reload_user_systemd()

    if activate:
        enable_and_start_timer()

    return paths
