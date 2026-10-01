import platform
import subprocess
import sys
from pathlib import Path


TASK_NAME = "App Inventory Exporter"


FREQUENCY_SCHEDULES = {
    "hourly": {
        "schedule": "HOURLY",
        "modifier": "1",
    },
    "six_hourly": {
        "schedule": "HOURLY",
        "modifier": "6",
    },
    "daily": {
        "schedule": "DAILY",
        "modifier": "1",
    },
    "startup": {
        "schedule": "ONSTART",
        "modifier": None,
    },
}


def build_schtasks_create_command(
    frequency,
    application_path=None,
    python_executable=None,
):
    """Build the Windows Task Scheduler command without executing it."""
    if frequency not in FREQUENCY_SCHEDULES:
        raise ValueError(f"Unsupported automatic frequency: {frequency}")

    application = Path(
        application_path
        or Path(__file__).resolve().with_name("app_inventory.py")
    ).resolve()

    executable = Path(python_executable or sys.executable).resolve()
    schedule = FREQUENCY_SCHEDULES[frequency]

    task_command = f'"{executable}" "{application}" --export'

    command = [
        "schtasks.exe",
        "/Create",
        "/TN",
        TASK_NAME,
        "/TR",
        task_command,
        "/SC",
        schedule["schedule"],
        "/F",
    ]

    if schedule["modifier"] is not None:
        command.extend(["/MO", schedule["modifier"]])

    return command


def build_schtasks_delete_command():
    """Build the command that removes the scheduled Windows task."""
    return [
        "schtasks.exe",
        "/Delete",
        "/TN",
        TASK_NAME,
        "/F",
    ]


def configure_windows_scheduler(
    frequency,
    application_path=None,
    python_executable=None,
    runner=subprocess.run,
):
    """Create or remove the Windows scheduled task."""
    if platform.system() != "Windows":
        raise RuntimeError(
            "The Windows Task Scheduler is only supported on Windows."
        )

    if frequency == "manual":
        command = build_schtasks_delete_command()
    else:
        command = build_schtasks_create_command(
            frequency=frequency,
            application_path=application_path,
            python_executable=python_executable,
        )

    runner(command, check=False, capture_output=True, text=True)
    return command
