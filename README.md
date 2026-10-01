# App Inventory Exporter

[ English ] | [ Català ]

---

## English

A desktop GUI application that exports installed-application information to Markdown (`.md`) format.

## Current status

This project is currently an early preview.

### Currently available

- Manual Markdown export from a graphical interface built with Tkinter.
- Up to five output destinations for each export.
- Interface labels in Catalan, English, and Spanish.
- Linux APT package detection on Debian/Ubuntu-like systems.
- Best-effort Snap package detection when Snap is installed.
- Limited macOS support: lists `.app` bundles directly inside `/Applications`.

### Platform status

| Platform | Application build | Automatic scheduling |
| --- | --- | --- |
| Linux x86-64 | Available | Available through `systemd --user` |
| Windows x86-64 | Available as `.exe` | Not implemented |
| macOS Apple Silicon | Available as `.zip` containing an `.app` | Not implemented |

### Known limitations

- This is a preview release and has not been tested on every supported operating-system version.
- The Windows executable is not Authenticode-signed.
- The macOS application is Apple Silicon (`arm64`) only.
- The macOS application is not notarized by Apple.
- GNOME extension detection is not implemented.
- Direct SMB authentication or mounting is not implemented.
- Complete application inventories for every Linux distribution are not implemented.
- The Linux scheduler depends on the user's `systemd --user` service.
- Windows and macOS scheduler integration is not implemented yet.

## Downloads

The current preview release is:

[v0.2.0 - Cross-platform Preview](https://github.com/litusmayol/app-inventory-exporter/releases/tag/v0.2.0 )

Available downloads:

- `AppInventoryExporter-linux-x86_64` — Linux x86-64.
- `AppInventoryExporter-windows-x86_64.exe` — Windows x86-64.
- `AppInventoryExporter-macos-arm64.zip` — macOS Apple Silicon only.
- `SHA256SUMS.txt` — checksums for verifying downloads.

Windows and macOS downloads are preview builds and are not signed/notarized production installers.

## Català

Aplicació d'escriptori amb interfície gràfica que exporta informació sobre les aplicacions instal·lades al sistema en format Markdown (`.md`).

## Estat actual

Aquest projecte es troba actualment en una fase inicial de proves.

### Funcionalitats disponibles

- Exportació manual a Markdown mitjançant una interfície gràfica desenvolupada amb Tkinter.
- Fins a cinc destinacions de sortida per a cada exportació.
- Etiquetes de la interfície en català, anglès i castellà.
- Detecció de paquets APT en sistemes semblants a Debian/Ubuntu.
- Detecció subjecta a disponibilitat dels paquets Snap quan Snap està instal·lat.
- Suport limitat per a macOS: mostra els paquets `.app` situats directament dins de `/Applications`.

### Estat per plataforma

| Plataforma | Versió de l'aplicació | Exportacions automàtiques |
| --- | --- | --- |
| Linux x86-64 | Disponible | Disponible mitjançant `systemd --user` |
| Windows x86-64 | Disponible com a `.exe` | Encara no implementades |
| macOS Apple Silicon | Disponible com a `.zip` amb una aplicació `.app` | Encara no implementades |

### Limitacions conegudes

- Aquesta és una versió preliminar i no s'ha provat en totes les versions dels sistemes operatius compatibles.
- L'executable de Windows no està signat amb Authenticode.
- L'aplicació de macOS només és per a Apple Silicon (`arm64`).
- L'aplicació de macOS no està notaritzada per Apple.
- La detecció d'extensions del GNOME no està implementada.
- L'autenticació o el muntatge directe de recursos SMB no està implementat.
- No s'han implementat inventaris complets per a totes les distribucions Linux.
- El planificador de Linux depèn del servei `systemd --user` de la sessió de l'usuari.
- La integració amb els planificadors de Windows i macOS encara no està implementada.

## Descàrregues

La versió preliminar actual és:

[v0.2.0 - Cross-platform Preview](https://github.com/litusmayol/app-inventory-exporter/releases/tag/v0.2.0 )

Descàrregues disponibles:

- `AppInventoryExporter-linux-x86_64` — Linux x86-64.
- `AppInventoryExporter-windows-x86_64.exe` — Windows x86-64.
- `AppInventoryExporter-macos-arm64.zip` — només macOS Apple Silicon.
- `SHA256SUMS.txt` — sumes de comprovació per verificar les descàrregues.

Les versions de Windows i macOS són preliminars i no són instal·ladors de producció signats/notaritzats.

## Execució des del codi font

Requisits:

- Python 3.10 o posterior.
- Tkinter.

Execució:

```bash
python3 app_inventory.py
```

El botó **Desar configuració** desa la configuració. A Linux, seleccionar una freqüència automàtica també configura i activa el temporitzador `systemd` de l'usuari.
