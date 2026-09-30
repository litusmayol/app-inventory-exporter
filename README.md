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

### Not yet implemented

- Windows installed-application detection.
- A Windows `.exe` download.
- A macOS application download.
- Automatic hourly, six-hourly, daily, or startup exports.
- GNOME extension detection.
- Direct SMB authentication or mounting.
- Complete application inventories for macOS or for Linux distributions beyond the currently supported package sources.

## Downloads

The current release contains one Linux x86-64 executable:

- `AppInventoryExporter` — Linux x86-64 only.

Windows and macOS users should not download this file. Native Windows and macOS builds are planned but are not available yet.

## Running from source

Requirements:

- Python 3.10 or newer.
- Tkinter.

Run:

```bash
python3 app_inventory.py
```

The **Save Settings** button must be pressed to save the configuration. The frequency selector currently stores a preference but does not yet run exports automatically.

---

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

### Funcionalitats encara no implementades

- Detecció d'aplicacions instal·lades a Windows.
- Descàrrega d'un fitxer `.exe` per a Windows.
- Descàrrega d'una aplicació per a macOS.
- Exportacions automàtiques cada hora, cada sis hores, diàries o en iniciar el sistema.
- Detecció d'extensions del GNOME.
- Autenticació o muntatge directe de recursos SMB.
- Inventaris complets d'aplicacions per a macOS o per a distribucions Linux més enllà de les fonts de paquets compatibles actualment.

## Descàrregues

La versió actual conté un únic executable per a Linux x86-64:

- `AppInventoryExporter` — només per a Linux x86-64.

Els usuaris de Windows i macOS no haurien de descarregar aquest fitxer. Les versions natives per a Windows i macOS estan previstes, però encara no estan disponibles.

## Execució des del codi font

Requisits:

- Python 3.10 o posterior.
- Tkinter.

Execució:

```bash
python3 app_inventory.py
```

Cal prémer el botó **Desar configuració** per desar la configuració. El selector de freqüència actualment només desa una preferència, però encara no executa exportacions automàticament.
