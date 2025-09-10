import os
import pandas as pd
import glob
import shutil
import json
import tkinter as tk
from tkinter import filedialog, Toplevel, Label, Button, messagebox
import logging
from pathlib import Path
import time
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    USING_BOOTSTRAP = True
except ImportError:
    import tkinter.ttk as ttk
    USING_BOOTSTRAP = False

# Setup logging
logging.basicConfig(
    filename='cryovault.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FileOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cryovault File Organizer")
        self.root.geometry("900x750")
        self.root.minsize(700, 550)
        self.root.configure(bg='#ffffff')
        try:
            self.style = ttk.Style(theme='flatly')
        except Exception:
            self.style = ttk.Style()
        self.style.configure('TButton', padding=5, font=('Helvetica', 12))
        self.style.configure('TLabel', font=('Helvetica', 12))
        self.style.configure('TEntry', padding=5)
        self.style.configure('TCheckbutton', font=('Helvetica', 11))
        # Rounded-ish button style (theme-dependent)
        try:
            self.style.configure('Rounded.TButton', padding=8, relief='flat')
        except Exception:
            pass

        # --- Default configuration ---
        self.config_file = 'cryovault_config.json'
        self.config = {
            'documents': ['.pdf', '.docx', '.doc', '.txt'],
            'image': ['.jpeg', '.jpg', '.webp', '.svg', '.png', '.PNG'],
            'music': ['.mp3'],
            'video': ['.mp4'],
            'setup_files': ['.exe', '.msi'],
            'compressed_files': ['.zip'],
            'other_files': ['.psd', '.ai', '.eps'],
            'documents_location': os.path.expanduser("~/Downloads/PDF"),
            'image_location': os.path.expanduser("~/Downloads/Image"),
            'music_location': os.path.expanduser("~/Downloads/Music"),
            'video_location': os.path.expanduser("~/Downloads/Video"),
            'setup_files_location': os.path.expanduser("~/Downloads/EXE"),
            'compressed_files_location': os.path.expanduser("~/Downloads/ZIP"),
            'other_files_location': os.path.expanduser("~/Downloads/Other")
        }
        self.load_config()

        # Derive current category list from config (keys with list values)
        self.categories = [k for k, v in self.config.items() if isinstance(v, list)]
        if 'other_files' not in self.categories:
            self.categories.append('other_files')

        # UI state stores
        self.file_type_vars = {}
        self.entries = {}          # category -> entry widget for extensions
        self.dest_entries = {}     # category -> entry widget for path
        self.category_rows = {}    # category -> frame row container

        # Last log dataframe for save button
        self.last_log_df = None

        # Build UI
        self.create_ui()

    # ------------------ UI BUILDERS ------------------
    def create_ui(self):
        # Source Folder
        ttk.Label(self.root, text="Source Folder:").grid(row=0, column=0, sticky="e", pady=5, padx=10)
        source_frame = ttk.Frame(self.root)
        source_frame.grid(row=0, column=1, columnspan=3, sticky="ew", pady=5, padx=10)
        self.source_entry = ttk.Entry(source_frame)
        self.source_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(source_frame, text="Browse", command=self.browse_source).grid(row=0, column=1, padx=6)
        ttk.Button(source_frame, text="Scan File Types", command=self.scan_file_types).grid(row=0, column=2, padx=6)
        source_frame.grid_columnconfigure(0, weight=1)

        # Scanned File Types
        ttk.Label(self.root, text="Scanned File Types:").grid(row=1, column=0, columnspan=4, sticky="w", pady=(6, 2), padx=10)
        self.file_types_frame = ttk.Frame(self.root)
        self.file_types_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=5, padx=10)
        self.update_file_types_frame()

        # Add to Category
        ttk.Label(self.root, text="Add selected types to category:").grid(row=3, column=0, sticky="e", pady=5, padx=10)
        self.category_var = tk.StringVar(value=(self.categories[0] if self.categories else ''))
        self.category_combobox = ttk.Combobox(self.root, textvariable=self.category_var, values=self.categories, state="readonly", width=22)
        self.category_combobox.grid(row=3, column=1, sticky="w", padx=5)
        ttk.Button(self.root, text="Add Selected", command=self.add_to_category).grid(row=3, column=2, padx=5, sticky='w')

        # Category Manager (dynamic)
        ttk.Label(self.root, text="Categories & Destinations:").grid(row=4, column=0, columnspan=4, sticky="w", pady=(12, 6), padx=10)
        controls = ttk.Frame(self.root)
        controls.grid(row=5, column=0, columnspan=4, sticky='w', padx=10)
        ttk.Button(controls, text="Add Category", command=self.toggle_add_category_drawer, bootstyle='info', style='TButton').grid(row=0, column=0, padx=(0,8))
        ttk.Button(controls, text="Save Settings", command=self.update_config).grid(row=0, column=1)

        # Header row
        header = ttk.Frame(self.root)
        header.grid(row=6, column=0, columnspan=4, sticky='ew', padx=10)
        ttk.Label(header, text="Category", width=16).grid(row=0, column=0, sticky='w')
        ttk.Label(header, text="Extensions (comma-separated)", width=34).grid(row=0, column=1, sticky='w')
        ttk.Label(header, text="Destination Folder", width=30).grid(row=0, column=2, sticky='w')
        ttk.Label(header, text="").grid(row=0, column=3)

        # Scrollable area for category rows
        outer = ttk.Frame(self.root)
        outer.grid(row=7, column=0, columnspan=4, sticky='nsew', padx=10)
        canvas = tk.Canvas(outer, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.categories_container = ttk.Frame(canvas)
        self.categories_container.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.categories_container, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set, height=260)
        canvas.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        self.rebuild_category_rows()

        # Options and Actions
        self.recursive_var = tk.BooleanVar()
        ttk.Checkbutton(self.root, text="Include Subdirectories", variable=self.recursive_var).grid(row=8, column=0, columnspan=4, sticky="w", pady=10, padx=10)
        action_frame = ttk.Frame(self.root)
        action_frame.grid(row=9, column=0, columnspan=4, sticky='w', padx=10)
        ttk.Button(action_frame, text="Preview Organization", command=self.preview_organization, bootstyle='secondary', style='TButton').grid(row=0, column=0, pady=5, padx=(0,10))
        ttk.Button(action_frame, text="Organize Files", command=self.organize_files, bootstyle='success', style='TButton').grid(row=0, column=1, pady=5)

        # Progress
        self.progress = ttk.Progressbar(self.root, length=400, mode='determinate')
        self.progress.grid(row=10, column=0, columnspan=3, sticky="ew", pady=5, padx=10)
        self.progress_label = ttk.Label(self.root, text="0%")
        self.progress_label.grid(row=10, column=3, pady=5, padx=5, sticky='e')

        # Bottom panel: Add-category drawer + notifications
        self.bottom_panel = ttk.Frame(self.root)
        self.bottom_panel.grid(row=11, column=0, columnspan=4, sticky='nsew', padx=10, pady=(8,12))
        self.root.grid_rowconfigure(11, weight=1)

        # Add Category Drawer (hidden by default)
        self.addcat_drawer = ttk.Labelframe(self.bottom_panel, text='Add Category')
        self.addcat_drawer.grid(row=0, column=0, sticky='ew', pady=(0,8))
        self.addcat_drawer.grid_remove()
        self.addcat_name = tk.StringVar()
        self.addcat_exts = tk.StringVar()
        self.addcat_dest = tk.StringVar()
        ttk.Label(self.addcat_drawer, text='Name (e.g. 3D Models):').grid(row=0, column=0, sticky='e', padx=8, pady=(10,6))
        ttk.Entry(self.addcat_drawer, textvariable=self.addcat_name, width=28).grid(row=0, column=1, sticky='w', padx=6, pady=(10,6))
        ttk.Label(self.addcat_drawer, text='Extensions (comma-separated):').grid(row=1, column=0, sticky='e', padx=8, pady=6)
        ttk.Entry(self.addcat_drawer, textvariable=self.addcat_exts, width=28).grid(row=1, column=1, sticky='w', padx=6, pady=6)
        ttk.Label(self.addcat_drawer, text='Destination folder:').grid(row=2, column=0, sticky='e', padx=8, pady=6)
        dest_row = ttk.Frame(self.addcat_drawer)
        dest_row.grid(row=2, column=1, sticky='ew', padx=6, pady=6)
        dest_entry = ttk.Entry(dest_row, textvariable=self.addcat_dest, width=32)
        dest_entry.grid(row=0, column=0, sticky='ew')
        ttk.Button(dest_row, text='Browse', command=self._drawer_browse_dest, bootstyle='info', style='TButton').grid(row=0, column=1, padx=6)
        btns = ttk.Frame(self.addcat_drawer)
        btns.grid(row=3, column=1, sticky='e', padx=6, pady=(4,10))
        ttk.Button(btns, text='Add', command=self.add_category_from_drawer, bootstyle='success', style='TButton').grid(row=0, column=0, padx=4)
        ttk.Button(btns, text='Cancel', command=self.cancel_add_category, bootstyle='secondary', style='TButton').grid(row=0, column=1, padx=4)

        # Notifications / results section
        self.notifications_section = ttk.Labelframe(self.bottom_panel, text='Activity & Results')
        self.notifications_section.grid(row=1, column=0, sticky='nsew')
        self.bottom_panel.grid_rowconfigure(1, weight=1)
        self.bottom_panel.grid_columnconfigure(0, weight=1)

        notif_frame = ttk.Frame(self.notifications_section)
        notif_frame.grid(row=0, column=0, sticky='nsew')
        self.notifications_text = tk.Text(notif_frame, height=10, wrap='word', state='disabled')
        vs = ttk.Scrollbar(notif_frame, orient='vertical', command=self.notifications_text.yview)
        self.notifications_text.configure(yscrollcommand=vs.set)
        self.notifications_text.grid(row=0, column=0, sticky='nsew')
        vs.grid(row=0, column=1, sticky='ns')
        notif_frame.grid_rowconfigure(0, weight=1)
        notif_frame.grid_columnconfigure(0, weight=1)
        # Color tags
        self.notifications_text.tag_config('info', foreground='#0d6efd')
        self.notifications_text.tag_config('success', foreground='#198754')
        self.notifications_text.tag_config('warning', foreground='#fd7e14')
        self.notifications_text.tag_config('danger', foreground='#dc3545')

        # Notification actions
        notif_actions = ttk.Frame(self.notifications_section)
        notif_actions.grid(row=1, column=0, sticky='e', pady=(6,0))
        self.save_log_btn = ttk.Button(notif_actions, text='Save Last Log Report', command=self.save_last_log_report, state='disabled', bootstyle='secondary', style='TButton')
        self.save_log_btn.grid(row=0, column=0, padx=(0,6))
        ttk.Button(notif_actions, text='Clear Messages', command=self.clear_notifications, bootstyle='light', style='TButton').grid(row=0, column=1)

        # Layout elasticity
        for r in range(0, 11):
            self.root.grid_rowconfigure(r, weight=0)
        self.root.grid_rowconfigure(7, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
    def update_file_types_frame(self):
        """Render (or clear) the scanned file types area.
        Called at startup to show a helpful hint, and can be reused later
        if we ever want to re-render from self.file_type_vars.
        """
        # Clear previous widgets
        for widget in self.file_types_frame.winfo_children():
            widget.destroy()

        # If nothing has been scanned yet, show a hint
        if not self.file_type_vars:
            ttk.Label(self.file_types_frame, text="(Scan a source folder to list file types)").grid(row=0, column=0, sticky="w", padx=5, pady=2)
            for i in range(5):
                self.file_types_frame.grid_columnconfigure(i, weight=1)
            return

        # Otherwise render checkboxes based on current vars
        for i, (ext, var) in enumerate(sorted(self.file_type_vars.items())):
            chk = ttk.Checkbutton(self.file_types_frame, text=ext, variable=var)
            chk.grid(row=i // 5, column=i % 5, sticky="w", padx=5, pady=2)
        for i in range(5):
            self.file_types_frame.grid_columnconfigure(i, weight=1)
    # ------------------ DRAWER & NOTIFICATIONS ------------------
    def toggle_add_category_drawer(self):
        if self.addcat_drawer.winfo_ismapped():
            self.addcat_drawer.grid_remove()
        else:
            # reset fields and show
            self.addcat_name.set("")
            self.addcat_exts.set("")
            self.addcat_dest.set("")
            self.addcat_drawer.grid()

    def _drawer_browse_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.addcat_dest.set(folder)

    def add_category_from_drawer(self):
        raw = self.addcat_name.get().strip()
        if not raw:
            self.notify("Please enter a category name.", level='warning')
            return
        name = raw.lower().replace(' ', '_')
        if name == 'other_files':
            self.notify("'other_files' is reserved as a catch-all.", level='danger')
            return
        if name in self.categories:
            self.notify(f"Category '{name}' already exists.", level='danger')
            return
        dest = self.addcat_dest.get().strip() or os.path.expanduser(f"~/Downloads/{raw.title()}")
        exts = [e.strip() for e in self.addcat_exts.get().split(',') if e.strip()]
        exts = [e if e.startswith('.') else f'.{e}' for e in exts]
        # update
        self.categories.append(name)
        self.config[name] = exts
        self.config[f"{name}_location"] = dest
        self.rebuild_category_rows()
        self.update_config()
        self.notify(f"Added category '{name}'.", level='success')
        self.addcat_drawer.grid_remove()

    def cancel_add_category(self):
        self.addcat_drawer.grid_remove()

    def notify(self, message, level='info'):
        """Append a status line to the Activity panel with optional color tag."""
        ts = time.strftime('%H:%M:%S')
        line = f"[{ts}] {message}\n"
        self.notifications_text.configure(state='normal')
        try:
            self.notifications_text.insert('end', line, (level,))
        except Exception:
            self.notifications_text.insert('end', line)
        self.notifications_text.see('end')
        self.notifications_text.configure(state='disabled')


    def clear_notifications(self):
        self.notifications_text.configure(state='normal')
        self.notifications_text.delete('1.0', 'end')
        self.notifications_text.configure(state='disabled')

    def save_last_log_report(self):
        if self.last_log_df is None:
            self.notify('No log to save yet.', level='warning')
            return
        save_path = filedialog.asksaveasfilename(
            initialfile="cryovault_log.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if save_path:
            try:
                self.last_log_df.to_csv(save_path, index=False)
                self.notify(f"Log report saved to: {save_path}", level='success')
            except Exception as e:
                self.notify(f"Could not save log: {e}", level='danger')

    def render_organize_summary(self, log_data):
        # Build a summary and render into notifications
        import pandas as pd
        total_files = len(log_data)
        total_size_bytes = sum(os.path.getsize(item["New Path"].replace("\\", "/")) for item in log_data if os.path.exists(item["New Path"].replace("\\", "/")))
        total_size_gb = round(total_size_bytes / (1024**3), 2)
        df = pd.DataFrame(log_data)
        self.last_log_df = df
        counts = df['Category'].value_counts().to_dict()
        lines = [
            f"Files Organized Successfully",
            f"Total Files Moved: {total_files}",
            f"Total Size: {total_size_gb} GB",
            "Breakdown by Category:" 
        ] + [f" - {k}: {v}" for k, v in counts.items()]
        for line in lines:
            self.notify(line, level='success')
        # enable save button
        try:
            self.save_log_btn['state'] = 'normal'
        except Exception:
            pass





    def rebuild_category_rows(self):
        # clear
        for child in self.categories_container.winfo_children():
            child.destroy()
        self.entries.clear()
        self.dest_entries.clear()
        self.category_rows.clear()

        row = 0
        for cat in self.categories:
            frame = ttk.Frame(self.categories_container)
            frame.grid(row=row, column=0, sticky='ew', pady=4)
            self.categories_container.grid_columnconfigure(0, weight=1)

            # Category label
            ttk.Label(frame, text=cat.replace('_', ' ').title(), width=16).grid(row=0, column=0, sticky='w')

            # Extensions entry
            ext_entry = ttk.Entry(frame, width=42)
            ext_entry.grid(row=0, column=1, sticky='ew', padx=(6,6))
            ext_entry.insert(0, ', '.join(self.config.get(cat, [])))
            self.entries[cat] = ext_entry

            # Destination path chooser
            dest_frame = ttk.Frame(frame)
            dest_frame.grid(row=0, column=2, sticky='ew')
            dest_entry = ttk.Entry(dest_frame, width=32)
            dest_entry.grid(row=0, column=0, sticky='ew')
            default_loc = self.config.get(f"{cat}_location", os.path.expanduser(f"~/Downloads/{cat.title()}"))
            dest_entry.insert(0, default_loc)
            ttk.Button(dest_frame, text="Browse", command=lambda c=cat: self.browse_destination(c)).grid(row=0, column=1, padx=6)
            self.dest_entries[cat] = dest_entry

            # Delete button (protect other_files as the catch‑all)
            can_delete = cat != 'other_files'
            del_btn = ttk.Button(frame, text="Remove", state=("normal" if can_delete else "disabled"), command=lambda c=cat: self.delete_category(c))
            del_btn.grid(row=0, column=3, padx=(6,0))

            row += 1

        # refresh dropdown
        self.category_combobox['values'] = self.categories
        if self.category_var.get() not in self.categories and self.categories:
            self.category_var.set(self.categories[0])

    # ------------------ CONFIG ------------------
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # merge while keeping unknown keys harmlessly
                    self.config.update(loaded)
        except Exception as e:
            logging.error(f"Failed to load config: {e}")

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def update_config(self):
        # rebuild config strictly from current rows
        new_cfg = {}
        for cat, entry in self.entries.items():
            exts = [ext.strip() for ext in entry.get().split(',') if ext.strip()]
            # normalize to lower for match behavior
            exts = [e if e.startswith('.') else f'.{e}' for e in exts]
            new_cfg[cat] = exts
            new_cfg[f"{cat}_location"] = self.dest_entries[cat].get()
        # Ensure other_files exists as a catch‑all bucket (can be empty list)
        if 'other_files' not in new_cfg:
            new_cfg['other_files'] = []
            new_cfg['other_files_location'] = os.path.expanduser('~/Downloads/Other')
        self.config = new_cfg
        self.save_config()
        self.notify("Category settings saved.", level='success')

    # ------------------ CATEGORY MGMT ------------------
    def add_category_dialog(self):
        dlg = Toplevel(self.root)
        dlg.title("Add Category")
        dlg.geometry("420x220")
        ttk.Label(dlg, text="Name (e.g. 3D Models):").grid(row=0, column=0, sticky='e', padx=8, pady=(12,6))
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dlg, textvariable=name_var, width=28)
        name_entry.grid(row=0, column=1, sticky='w', padx=8, pady=(12,6))

        ttk.Label(dlg, text="Extensions (comma-separated):").grid(row=1, column=0, sticky='e', padx=8, pady=6)
        ext_var = tk.StringVar()
        ext_entry = ttk.Entry(dlg, textvariable=ext_var, width=28)
        ext_entry.grid(row=1, column=1, sticky='w', padx=8, pady=6)

        ttk.Label(dlg, text="Destination folder:").grid(row=2, column=0, sticky='e', padx=8, pady=6)
        dest_var = tk.StringVar()
        dest_entry = ttk.Entry(dlg, textvariable=dest_var, width=28)
        dest_entry.grid(row=2, column=1, sticky='w', padx=8, pady=6)

        def browse_dest():
            folder = filedialog.askdirectory()
            if folder:
                dest_var.set(folder)
        ttk.Button(dlg, text="Browse", command=browse_dest).grid(row=2, column=2, padx=6)

        def on_ok():
            raw = name_var.get().strip()
            if not raw:
                messagebox.showerror("Missing name", "Please enter a category name.")
                return
            name = raw.lower().replace(' ', '_')
            if name == 'other_files':
                messagebox.showerror("Reserved name", "'other_files' is reserved as a catch-all.")
                return
            if name in self.categories:
                messagebox.showerror("Duplicate", f"Category '{name}' already exists.")
                return
            dest = dest_var.get().strip() or os.path.expanduser(f"~/Downloads/{raw.title()}")
            exts = [e.strip() for e in ext_var.get().split(',') if e.strip()]
            exts = [e if e.startswith('.') else f'.{e}' for e in exts]

            # update in-memory
            self.categories.append(name)
            self.config[name] = exts
            self.config[f"{name}_location"] = dest

            # rebuild rows & save
            self.rebuild_category_rows()
            self.update_config()
            dlg.destroy()

        ttk.Button(dlg, text="Add", command=on_ok).grid(row=3, column=1, sticky='e', pady=12)
        ttk.Button(dlg, text="Cancel", command=dlg.destroy).grid(row=3, column=2, sticky='w', pady=12)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.focus_set()
        name_entry.focus()

    def delete_category(self, cat):
        if cat == 'other_files':
            return
        if messagebox.askyesno("Remove Category", f"Remove '{cat}'? This won't move files; only the rule."):
            # remove from data structures
            if cat in self.categories:
                self.categories.remove(cat)
            self.config.pop(cat, None)
            self.config.pop(f"{cat}_location", None)
            self.rebuild_category_rows()
            self.update_config()

    # ------------------ FILE TYPE SCAN & ASSIGN ------------------
    def browse_source(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, folder)

    def browse_destination(self, category):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_entries[category].delete(0, tk.END)
            self.dest_entries[category].insert(0, folder)

    def scan_file_types(self):
        source_folder = self.source_entry.get()
        if not source_folder or not os.path.exists(source_folder):
            self.notify("Invalid Folder: please select a valid source folder.", level='danger')
            return

        for widget in self.file_types_frame.winfo_children():
            widget.destroy()
        self.file_type_vars.clear()

        files = []
        if self.recursive_var.get():
            for root, _, filenames in os.walk(source_folder):
                files.extend(os.path.join(root, f) for f in filenames)
        else:
            files = glob.glob(os.path.join(source_folder, '*'))

        extensions = set()
        for file_path in files:
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext:
                    extensions.add(ext)

        # grid nicely 5 columns
        for i, ext in enumerate(sorted(extensions)):
            var = tk.BooleanVar()
            self.file_type_vars[ext] = var
            chk = ttk.Checkbutton(self.file_types_frame, text=ext, variable=var)
            chk.grid(row=i // 5, column=i % 5, sticky="w", padx=5, pady=2)

        for i in range(5):
            self.file_types_frame.grid_columnconfigure(i, weight=1)

    def add_to_category(self):
        selected_category = self.category_var.get()
        if not selected_category:
            messagebox.showerror("No category", "Please pick a category.")
            return
        entry = self.entries[selected_category]
        current_extensions = [ext.strip() for ext in entry.get().split(',') if ext.strip()]
        selected_extensions = [ext for ext, var in self.file_type_vars.items() if var.get()]
        for ext in selected_extensions:
            if ext not in current_extensions:
                current_extensions.append(ext)
        entry.delete(0, tk.END)
        entry.insert(0, ', '.join(current_extensions))

    # ------------------ PREVIEW & ORGANIZE ------------------
    def _iter_files(self, source_folder):
        files = []
        if self.recursive_var.get():
            for root, _, filenames in os.walk(source_folder):
                files.extend(os.path.join(root, f) for f in filenames)
        else:
            files = glob.glob(os.path.join(source_folder, '*'))
        return files

    def _match_category_and_destination(self, file_extension, base_filename):
        destination = None
        category_tag = "Other"
        # iterate dynamic categories in order; other_files has no special meaning except catch-all UI
        for category in self.entries.keys():
            if file_extension in [e.lower() for e in self.config.get(category, [])]:
                category_tag = category
                if category == "other_files":
                    subfolder = file_extension.lstrip(".").upper() or "UNKNOWN"
                    destination = os.path.join(self.config.get("other_files_location", os.path.expanduser('~/Downloads/Other')), subfolder)
                else:
                    destination = self.config.get(f"{category}_location")
                break
        return destination, category_tag

    def preview_organization(self):
        from datetime import datetime
        self.update_config()
        source_folder = self.source_entry.get()
        if not source_folder or not os.path.exists(source_folder):
            self.notify("Invalid Folder: please select a valid source folder.", level='danger')
            return

        files = self._iter_files(source_folder)
        if not files:
            self.notify("No files found to preview.", level='warning')
            return

        preview_data = []
        for file_path in files:
            if not os.path.isfile(file_path):
                continue
            base_filename = os.path.basename(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()
            destination, category_tag = self._match_category_and_destination(file_extension, base_filename)
            if not destination:
                continue
            new_path = os.path.join(destination, base_filename)
            if os.path.exists(new_path):
                root, ext = os.path.splitext(base_filename)
                count = 1
                while os.path.exists(os.path.join(destination, f"{root}_{count}{ext}")):
                    count += 1
                new_path = os.path.join(destination, f"{root}_{count}{ext}")
            preview_data.append({
                "Current Path": file_path.replace("/", "\\"),
                "Destination Path": new_path.replace("/", "\\"),
                "Category": category_tag
            })

        if not preview_data:
            self.notify("No previewable file operations were detected.", level='warning')
            return

        save_path = filedialog.asksaveasfilename(
            initialfile="cryovault_preview.csv",
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")]
        )
        if not save_path:
            return
        try:
            df = pd.DataFrame(preview_data)
            df.to_csv(save_path, index=False)
            self.notify(f"Preview saved to: {save_path}", level='info')
        except Exception as e:
            self.notify(f"Failed to export preview: {e}", level='danger')

    def organize_files(self):
        from datetime import datetime
        self.update_config()
        source_folder = self.source_entry.get()
        if not source_folder or not os.path.exists(source_folder):
            self.notify("Invalid Folder: please select a valid source folder.", level='danger')
            return

        files = self._iter_files(source_folder)
        if not files:
            self.notify("No files found to organize.", level='warning')
            return

        log_data = []
        total_files = len(files)
        self.progress["maximum"] = total_files
        self.progress["value"] = 0

        for i, file_path in enumerate(files):
            if not os.path.isfile(file_path):
                continue
            base_filename = os.path.basename(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()
            destination, category_tag = self._match_category_and_destination(file_extension, base_filename)
            if not destination:
                # skip unmatched types
                self.progress["value"] = i + 1
                self.progress_label.config(text=f"{int((i + 1) / total_files * 100)}%")
                self.root.update()
                continue
            try:
                if not os.path.exists(destination):
                    os.makedirs(destination)
                new_path = os.path.join(destination, base_filename)
                if os.path.exists(new_path):
                    root, ext = os.path.splitext(base_filename)
                    count = 1
                    while os.path.exists(os.path.join(destination, f"{root}_{count}{ext}")):
                        count += 1
                    new_path = os.path.join(destination, f"{root}_{count}{ext}")
                shutil.move(file_path, new_path)
                log_data.append({
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Original Path": file_path.replace("/", "\\"),
                    "New Path": new_path.replace("/", "\\"),
                    "Category": category_tag
                })
            except Exception as e:
                logging.error(f"Error moving {file_path}: {e}")

            self.progress["value"] = i + 1
            self.progress_label.config(text=f"{int((i + 1) / total_files * 100)}%")
            self.root.update()

        if log_data:
            self.render_organize_summary(log_data)
        else:
            self.notify("No files were moved.", level='warning')

    # ------------------ SUMMARY POPUP ------------------
    def show_organize_summary_popup(self, log_data):
        total_files = len(log_data)
        total_size_bytes = sum(os.path.getsize(item["New Path"].replace("\\", "/")) for item in log_data if os.path.exists(item["New Path"].replace("\\", "/")))
        total_size_gb = round(total_size_bytes / (1024**3), 2)

        df = pd.DataFrame(log_data)
        category_counts = df['Category'].value_counts().to_dict()

        popup = Toplevel(self.root)
        popup.title("Organization Summary")
        popup.geometry("420x360")

        Label(popup, text="Files Organized Successfully", font=("Helvetica", 14, "bold")).pack(pady=10)
        Label(popup, text=f"Total Files Moved: {total_files}", font=("Helvetica", 12)).pack()
        Label(popup, text=f"Total Size: {total_size_gb} GB", font=("Helvetica", 12)).pack(pady=5)

        Label(popup, text="Breakdown by Category:", font=("Helvetica", 12, "underline")).pack()
        for cat, count in category_counts.items():
            Label(popup, text=f"{cat}: {count}").pack()

        def save_log():
            save_path = filedialog.asksaveasfilename(
                initialfile="cryovault_log.csv",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")]
            )
            if save_path:
                try:
                    df.to_csv(save_path, index=False)
                    messagebox.showinfo("Saved", f"Log report saved to:\n{save_path}")
                except Exception as e:
                    messagebox.showerror("Save Error", f"Could not save log:\n{e}")

        Button(popup, text="Save Log Report of Files Organized", command=save_log).pack(pady=10)
        Button(popup, text="Close", command=popup.destroy).pack(pady=5)

        popup.transient(self.root)
        popup.grab_set()
        self.root.wait_window(popup)


if __name__ == "__main__":
    print("Starting Cryovault...")
    try:
        import tkinter
        print("Tkinter is available, launching GUI...")
        if USING_BOOTSTRAP:
            root = ttk.Window(themename="flatly")
        else:
            root = tk.Tk()
            root.configure(bg='#ffffff')
        app = FileOrganizerApp(root)
        root.mainloop()
    except ImportError as e:
        print(f"Error: Tkinter is not available. Please ensure Tkinter is installed. Details: {e}")
        logging.error(f"Tkinter import failed: {e}")
    except Exception as e:
        print(f"Error starting application: {e}")
        logging.error(f"Application failed to start: {e}")
