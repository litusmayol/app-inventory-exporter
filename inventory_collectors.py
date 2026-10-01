import subprocess
import platform


WINDOWS_UNINSTALL_PATHS = (
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
)


def collect_windows_applications(registry_module=None):
    """
    Return installed Windows applications from the uninstall registry keys.

    Each result is a dictionary with:
    name, version, publisher, install_location, source.

    registry_module is injectable so this collector can be tested on
    non-Windows systems.
    """
    if platform.system() != "Windows" and registry_module is None:
        return []

    if registry_module is None:
        import winreg as registry_module

    applications = []
    seen = set()

    registry_roots = (
        registry_module.HKEY_CURRENT_USER,
        registry_module.HKEY_LOCAL_MACHINE,
    )

    for root in registry_roots:
        for uninstall_path in WINDOWS_UNINSTALL_PATHS:
            try:
                uninstall_key = registry_module.OpenKey(
                    root,
                    uninstall_path,
                    0,
                    registry_module.KEY_READ,
                )
            except OSError:
                continue

            try:
                subkey_count = registry_module.QueryInfoKey(uninstall_key)[0]
            except OSError:
                registry_module.CloseKey(uninstall_key)
                continue

            try:
                for index in range(subkey_count):
                    try:
                        subkey_name = registry_module.EnumKey(
                            uninstall_key,
                            index,
                        )
                        app_key = registry_module.OpenKey(
                            uninstall_key,
                            subkey_name,
                            0,
                            registry_module.KEY_READ,
                        )
                    except OSError:
                        continue

                    try:
                        name = _read_registry_value(
                            registry_module,
                            app_key,
                            "DisplayName",
                        ).strip()

                        if not name:
                            continue

                        version = _read_registry_value(
                            registry_module,
                            app_key,
                            "DisplayVersion",
                        ).strip()

                        publisher = _read_registry_value(
                            registry_module,
                            app_key,
                            "Publisher",
                        ).strip()

                        install_location = _read_registry_value(
                            registry_module,
                            app_key,
                            "InstallLocation",
                        ).strip()

                        identity = (
                            name.casefold(),
                            version.casefold(),
                            publisher.casefold(),
                        )

                        if identity in seen:
                            continue

                        seen.add(identity)
                        applications.append(
                            {
                                "name": name,
                                "version": version,
                                "publisher": publisher,
                                "install_location": install_location,
                                "source": "Windows Registry",
                            }
                        )
                    finally:
                        registry_module.CloseKey(app_key)
            finally:
                registry_module.CloseKey(uninstall_key)

    applications.sort(key=lambda item: item["name"].casefold())
    return applications


def _read_registry_value(registry_module, key, value_name):
    try:
        value, _value_type = registry_module.QueryValueEx(key, value_name)
    except OSError:
        return ""

    if value is None:
        return ""

    return str(value)


def collect_macos_applications(
    application_directories=None,
    filesystem_module=None,
    plist_module=None,
    home_directory=None,
):
    """Return macOS .app bundles with basic bundle metadata."""

    if application_directories is None:
        home = home_directory or __import__("pathlib").Path.home()
        application_directories = (
            __import__("pathlib").Path("/Applications"),
            __import__("pathlib").Path("/System/Applications"),
            home / "Applications",
        )

    if filesystem_module is None:
        import os as filesystem_module

    if plist_module is None:
        import plistlib as plist_module

    applications = []

    for directory in application_directories:
        if not filesystem_module.path.isdir(directory):
            continue

        try:
            entries = filesystem_module.listdir(directory)
        except OSError:
            continue

        for entry in entries:
            if not entry.endswith(".app"):
                continue

            app_path = filesystem_module.path.join(directory, entry)
            if not filesystem_module.path.isdir(app_path):
                continue

            info_path = filesystem_module.path.join(
                app_path,
                "Contents",
                "Info.plist",
            )

            metadata = {}
            try:
                with open(info_path, "rb") as info_file:
                    metadata = plist_module.load(info_file)
            except (OSError, ValueError, plist_module.InvalidFileException):
                metadata = {}

            name = (
                metadata.get("CFBundleDisplayName")
                or metadata.get("CFBundleName")
                or entry.removesuffix(".app")
            )

            version = (
                metadata.get("CFBundleShortVersionString")
                or metadata.get("CFBundleVersion")
                or ""
            )

            applications.append(
                {
                    "name": str(name),
                    "version": str(version),
                    "publisher": "",
                    "install_location": str(app_path),
                    "bundle_identifier": str(
                        metadata.get("CFBundleIdentifier", "")
                    ),
                    "source": "macOS Application Bundle",
                }
            )

    applications.sort(key=lambda item: item["name"].casefold())
    return applications


def collect_gnome_extensions(runner=None):
    """Return installed GNOME Shell extensions and their states."""
    if runner is None:
        runner = subprocess.run

    try:
        result = runner(
            ["gnome-extensions", "list"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []

    extensions = []

    for line in result.stdout.splitlines():
        uuid = line.strip()

        if not uuid:
            continue

        try:
            info_result = runner(
                ["gnome-extensions", "info", uuid],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            info_result = None

        metadata = _parse_gnome_extension_info(
            info_result.stdout if info_result else ""
        )

        extensions.append(
            {
                "uuid": uuid,
                "name": metadata.get("name", uuid),
                "state": metadata.get("state", "Unknown"),
                "enabled": metadata.get("enabled", ""),
                "description": metadata.get("description", ""),
                "source": "GNOME Shell Extension",
            }
        )

    extensions.sort(key=lambda item: item["name"].casefold())
    return extensions


def _parse_gnome_extension_info(output):
    """Parse the human-readable output of gnome-extensions info."""
    metadata = {}
    description_lines = []
    reading_description = False

    for raw_line in output.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            normalized_key = key.strip().casefold()
            value = value.strip()

            if normalized_key in {"name", "nom"}:
                metadata["name"] = value
            elif normalized_key in {"state", "estat"}:
                metadata["state"] = value
            elif normalized_key in {"description", "descripció", "descripcio"}:
                metadata["description"] = value
                reading_description = True
            elif normalized_key in {"enabled", "habilitat"}:
                metadata["enabled"] = value
            elif reading_description:
                description_lines.append(line)
        elif reading_description:
            description_lines.append(line)

    if description_lines:
        metadata["description"] = " ".join(description_lines)

    return metadata


def collect_flatpak_applications(runner=None):
    """Return installed Flatpak applications."""
    if runner is None:
        runner = subprocess.run

    command = [
        "flatpak",
        "list",
        "--app",
        "--columns=application,name,version,installation",
    ]

    try:
        result = runner(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []

    applications = []

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        fields = line.split("\t")

        if len(fields) < 4:
            fields = line.split(None, 3)

        if len(fields) < 4:
            continue

        application_id, name, version, installation = (
            field.strip() for field in fields[:4]
        )

        if not application_id:
            continue

        applications.append(
            {
                "application_id": application_id,
                "name": name or application_id,
                "version": version,
                "installation": installation or "unknown",
                "source": "Flatpak",
            }
        )

    applications.sort(key=lambda item: item["name"].casefold())
    return applications
