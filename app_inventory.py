import os
import sys
import platform
import subprocess
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime

from inventory_collectors import (
    collect_macos_applications,
    collect_windows_applications,
)

CONFIG_FILE = os.path.expanduser("~/.app_inventory_config.json")

# Diccionario de traducciones
TRANSLATIONS = {
    "Català": {
        "title": "Exportador d'Aplicacions Instal·lades a Markdown",
        "freq_title": " Configuració de Freqüència ",
        "freq_label": "Freqüència d'actualització:",
        "dest_title": " Destins d'Exportació .md (Fins a 5) ",
        "active": "Actiu",
        "dir_label": "Directori de Destí",
        "file_label": "Nom del fitxer (.md)",
        "browse": "Examinar...",
        "save_btn": "Desar Configuració",
        "run_btn": "Generar Markdown Ara",
        "saved_msg": "Configuració desada correctament!",
        "success_msg": "S'han generat {count} fitxer(s) Markdown amb èxit!",
        "warning_msg": "No s'ha definit cap destí actiu o vàlid.",
        "lang_label": "Idioma / Language:",
        "freq_options": ["Manual", "Cada hora", "Cada 6 hores", "Diari", "En iniciar el sistema"]
    },
    "English": {
        "title": "Installed Applications Exporter to Markdown",
        "freq_title": " Frequency Settings ",
        "freq_label": "Update frequency:",
        "dest_title": " Export Destinations .md (Up to 5) ",
        "active": "Active",
        "dir_label": "Destination Directory",
        "file_label": "File Name (.md)",
        "browse": "Browse...",
        "save_btn": "Save Settings",
        "run_btn": "Generate Markdown Now",
        "saved_msg": "Settings saved successfully!",
        "success_msg": "Successfully generated {count} Markdown file(s)!",
        "warning_msg": "No active or valid destination defined.",
        "lang_label": "Language / Idioma:",
        "freq_options": ["Manual", "Every hour", "Every 6 hours", "Daily", "On system startup"]
    },
    "Español": {
        "title": "Exportador de Aplicaciones Instaladas a Markdown",
        "freq_title": " Configuración de Frecuencia ",
        "freq_label": "Frecuencia de actualización:",
        "dest_title": " Destinos de Exportación .md (Hasta 5) ",
        "active": "Activo",
        "dir_label": "Directorio de Destino",
        "file_label": "Nombre del archivo (.md)",
        "browse": "Examinar...",
        "save_btn": "Guardar Configuración",
        "run_btn": "Generar Markdown Ahora",
        "saved_msg": "¡Configuración guardada correctamente!",
        "success_msg": "¡Se han generado {count} archivo(s) Markdown con éxito!",
        "warning_msg": "No se ha definido ningún destino activo o válido.",
        "lang_label": "Idioma / Language:",
        "freq_options": ["Manual", "Cada hora", "Cada 6 horas", "Diario", "Al iniciar el sistema"]
    }
}

class AppInventoryGUI:
    def __init__(self, root):
        self.root = root
        self.load_config_data()
        
        # Idioma por defecto
        self.current_lang = self.saved_config.get("language", "Català")
        if self.current_lang not in TRANSLATIONS:
            self.current_lang = "Català"

        self.root.title(TRANSLATIONS[self.current_lang]["title"])
        self.root.geometry("720x580")
        self.root.resizable(True, True)

        self.create_widgets()

    def create_widgets(self):
        t = TRANSLATIONS[self.current_lang]

        # --- Frame Superior (Selector de Idioma) ---
        lang_frame = ttk.Frame(self.root, padding=5)
        lang_frame.pack(fill="x", padx=10, pady=2)
        
        ttk.Label(lang_frame, text=t["lang_label"]).pack(side="right", padx=5)
        self.lang_var = tk.StringVar(value=self.current_lang)
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, state="readonly", 
                                  values=["Català", "English", "Español"], width=10)
        lang_combo.pack(side="right")
        lang_combo.bind("<<ComboboxSelected>>", self.change_language)

        # --- Frame de Frecuencia ---
        self.freq_frame = ttk.LabelFrame(self.root, text=t["freq_title"], padding=10)
        self.freq_frame.pack(fill="x", padx=10, pady=5)

        self.lbl_freq = ttk.Label(self.freq_frame, text=t["freq_label"])
        self.lbl_freq.grid(row=0, column=0, sticky="w", padx=5)
        
        self.freq_var = tk.StringVar(value=self.saved_config.get("frequency", t["freq_options"][0]))
        self.freq_combo = ttk.Combobox(self.freq_frame, textvariable=self.freq_var, state="readonly", 
                                       values=t["freq_options"])
        self.freq_combo.grid(row=0, column=1, sticky="w", padx=5)

        # --- Frame de Destinos (Hasta 5) ---
        self.dest_frame = ttk.LabelFrame(self.root, text=t["dest_title"], padding=10)
        self.dest_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.lbl_act = ttk.Label(self.dest_frame, text=t["active"])
        self.lbl_act.grid(row=0, column=0, padx=2, pady=2)
        self.lbl_dir = ttk.Label(self.dest_frame, text=t["dir_label"])
        self.lbl_dir.grid(row=0, column=1, padx=5, pady=2)
        self.lbl_file = ttk.Label(self.dest_frame, text=t["file_label"])
        self.lbl_file.grid(row=0, column=3, padx=5, pady=2)

        self.dest_entries = []
        self.browse_buttons = []
        saved_dests = self.saved_config.get("destinations", [])

        for i in range(5):
            enabled_var = tk.BooleanVar(value=saved_dests[i]["active"] if i < len(saved_dests) else (i == 0))
            dir_var = tk.StringVar(value=saved_dests[i]["dir"] if i < len(saved_dests) else "")
            file_var = tk.StringVar(value=saved_dests[i]["file"] if i < len(saved_dests) else f"apps_instalades_{i+1}.md")

            chk = ttk.Checkbutton(self.dest_frame, variable=enabled_var)
            chk.grid(row=i+1, column=0, padx=2, pady=5)

            entry_dir = ttk.Entry(self.dest_frame, textvariable=dir_var, width=35)
            entry_dir.grid(row=i+1, column=1, padx=5, pady=5)

            btn_browse = ttk.Button(self.dest_frame, text=t["browse"], command=lambda v=dir_var: self.browse_directory(v))
            btn_browse.grid(row=i+1, column=2, padx=2, pady=5)
            self.browse_buttons.append(btn_browse)

            entry_file = ttk.Entry(self.dest_frame, textvariable=file_var, width=20)
            entry_file.grid(row=i+1, column=3, padx=5, pady=5)

            self.dest_entries.append({
                "active": enabled_var,
                "dir": dir_var,
                "file": file_var
            })

        # --- Botones inferiores ---
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x", side="bottom")

        self.btn_save = ttk.Button(btn_frame, text=t["save_btn"], command=self.save_config)
        self.btn_save.pack(side="left", padx=5)

        self.btn_run = ttk.Button(btn_frame, text=t["run_btn"], command=self.run_export)
        self.btn_run.pack(side="right", padx=5)

    def change_language(self, event=None):
        self.current_lang = self.lang_var.get()
        t = TRANSLATIONS[self.current_lang]

        self.root.title(t["title"])
        self.freq_frame.config(text=t["freq_title"])
        self.lbl_freq.config(text=t["freq_label"])
        self.freq_combo.config(values=t["freq_options"])
        
        self.dest_frame.config(text=t["dest_title"])
        self.lbl_act.config(text=t["active"])
        self.lbl_dir.config(text=t["dir_label"])
        self.lbl_file.config(text=t["file_label"])

        for btn in self.browse_buttons:
            btn.config(text=t["browse"])

        self.btn_save.config(text=t["save_btn"])
        self.btn_run.config(text=t["run_btn"])

    def browse_directory(self, var):
        directory = filedialog.askdirectory()
        if directory:
            var.set(directory)

    def load_config_data(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.saved_config = json.load(f)
            except Exception:
                self.saved_config = {}
        else:
            self.saved_config = {}

    def save_config(self):
        config_data = {
            "language": self.current_lang,
            "frequency": self.freq_var.get(),
            "destinations": [
                {
                    "active": item["active"].get(),
                    "dir": item["dir"].get(),
                    "file": item["file"].get()
                }
                for item in self.dest_entries
            ]
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        
        t = TRANSLATIONS[self.current_lang]
        messagebox.showinfo(t["title"], t["saved_msg"])

    def generate_markdown_content(self):
        system = platform.system()
        md_lines = ["# Llistat d'aplicacions i extensions instal·lades", "", "| Tipus | Data / Font | Nom | Descripció |", "| --- | --- | --- | --- |"]

        if system == "Linux":
            try:
                apt_out = subprocess.check_output("apt-mark showmanual", shell=True, text=True)
                for pkg in apt_out.splitlines():
                    if not pkg or any(k in pkg for k in ["language-pack", "gnome-user-docs", "gdm", "ubuntu-desktop", "linux-", "casper"]):
                        continue
                    desc_out = subprocess.run(f"dpkg-query -W -f='${{Description}}' {pkg}", shell=True, capture_output=True, text=True).stdout
                    desc = desc_out.splitlines()[0].replace("|", "-") if desc_out else "Sense descripció"
                    md_lines.append(f"| APT | Sistema/Inicial | {pkg} | {desc} |")
            except Exception as e:
                md_lines.append(f"| APT | Error | Error en obtenir paquets APT: {e} | - |")

            try:
                snap_out = subprocess.check_output("snap list", shell=True, text=True)
                for line in snap_out.splitlines()[1:]:
                    parts = line.split()
                    if parts and parts[0] not in ["bare", "gtk-common-themes", "snapd"] and not parts[0].startswith(("core", "gnome-")):
                        s_name = parts[0]
                        desc_out = subprocess.run(f"snap info {s_name}", shell=True, capture_output=True, text=True).stdout
                        desc = "Sense descripció"
                        for d_line in desc_out.splitlines():
                            if d_line.startswith("summary:"):
                                desc = d_line.replace("summary:", "").strip().replace("|", "-")
                                break
                        md_lines.append(f"| Snap | Sistema/Inicial | {s_name} | {desc} |")
            except Exception:
                pass

        elif system == "Darwin":
            macos_applications = collect_macos_applications()

            if not macos_applications:
                md_lines.append(
                    "| App macOS | Sistema | No s'han trobat aplicacions | - |"
                )
            else:
                for application in macos_applications:
                    name = application["name"].replace("|", "-")
                    version = application["version"].replace("|", "-")
                    location = application["install_location"].replace("|", "-")
                    bundle_identifier = application[
                        "bundle_identifier"
                    ].replace("|", "-")

                    description_parts = []

                    if version:
                        description_parts.append(f"Versió: {version}")

                    if bundle_identifier:
                        description_parts.append(
                            f"Identificador: {bundle_identifier}"
                        )

                    description_parts.append(f"Ubicació: {location}")
                    description = "; ".join(description_parts)

                    md_lines.append(
                        f"| App macOS | Application Bundle | {name} | "
                        f"{description} |"
                    )

        elif system == "Windows":
            windows_applications = collect_windows_applications()

            if not windows_applications:
                md_lines.append(
                    "| Windows | Registry | No s'han trobat aplicacions | - |"
                )
            else:
                for application in windows_applications:
                    name = application["name"].replace("|", "-")
                    version = application["version"].replace("|", "-")
                    publisher = application["publisher"].replace("|", "-")
                    description_parts = []

                    if version:
                        description_parts.append(f"Versió: {version}")

                    if publisher:
                        description_parts.append(f"Editor: {publisher}")

                    if application["install_location"]:
                        description_parts.append(
                            f"Ubicació: {application['install_location']}"
                        )

                    description = "; ".join(description_parts) or "-"
                    description = description.replace("|", "-")

                    md_lines.append(
                        f"| Windows | Registry | {name} | "
                        f"{description} |"
                    )

        return "\n".join(md_lines)

    def run_export(self):
        t = TRANSLATIONS[self.current_lang]
        content = self.generate_markdown_content()
        count = 0
        for item in self.dest_entries:
            if item["active"].get():
                target_dir = item["dir"].get()
                filename = item["file"].get()
                if target_dir and filename:
                    if not os.path.exists(target_dir):
                        try:
                            os.makedirs(target_dir, exist_ok=True)
                        except Exception as e:
                            print(f"Error: {e}")
                            continue
                    full_path = os.path.join(target_dir, filename)
                    try:
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(content)
                        count += 1
                    except Exception as e:
                        print(f"Error: {e}")

        if count > 0:
            messagebox.showinfo(t["title"], t["success_msg"].format(count=count))
        else:
            messagebox.showwarning(t["title"], t["warning_msg"])

if __name__ == "__main__":
    root = tk.Tk()
    app = AppInventoryGUI(root)
    root.mainloop()
