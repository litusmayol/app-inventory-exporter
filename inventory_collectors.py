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
