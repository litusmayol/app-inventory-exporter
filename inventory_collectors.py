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
