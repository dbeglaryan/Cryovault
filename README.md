# 🧊 FrostNode | File Organizer Pro ⚡

<!-- Add a banner or screenshot named intro.png in the repo root to display it here -->
<!-- ![Intro](intro.png) -->

A professional **file organizer** that stays **simple** but packs **practical power**.  
Built with 🐍 **Python + Tkinter**, with optional 🎨 **ttkbootstrap** themes.

Organize messy folders in minutes with an intuitive UI and quick exports. 🔥

---

## ✨ Features
- 📁 **Select source folder** → scan files for organizing
- 🗂️ **Category buckets** → create/rename categories on the fly
- 🔀 **Move or Copy** → send files into per‑category subfolders
- 📝 **CSV export** → save a summary of file placements
- 🎛️ **Clean styling** → standard `'TButton'` (no version‑sensitive hacks)
- 🧩 **Optional themes** → uses `ttkbootstrap` if installed; falls back gracefully

---

## 🚀 Run locally
```bash
# create & activate venv
python -m venv .venv
# Windows: .venv\Scriptsctivate
# macOS/Linux: source .venv/bin/activate

# install deps (pandas is used for CSV export)
pip install -r requirements.txt

# (optional) nicer themes
pip install ttkbootstrap

# launch the app
python main.py
```

## 🧭 Quick Start
1) Open the app and choose your **source folder**.  
2) Add a few **categories** (e.g., Invoices, Photos, PDFs).  
3) Select files and choose **Move** or **Copy** into category subfolders.  
4) Optional: **Export CSV** of results for your records.

## 🛠️ Options & Notes
- Uses default ttk style: `style='TButton'` for reliability.  
- If `ttkbootstrap` is present, you can pass `bootstyle='primary' | 'success' | 'info' | ...` to buttons in code.

## 🐞 Troubleshooting
- **`type object 'StyleBuilderTTK' has no attribute 'create_round_button_style'`**  
  Older/newer `ttkbootstrap` builds may not include the helper used by rounded buttons.  
  This app **does not** request `Rounded.TButton`, so it **runs without error**.
- **`bootstyle` not recognized** (plain Tk only)  
  If `ttkbootstrap` isn’t installed, ttk ignores `bootstyle`; the app still works with standard styling.

## 📦 Packaging (optional)
Create a single-file build with PyInstaller:
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed main.py
```
Builds appear in `dist/`.

## 🧑‍💻 Tech
- Python 3.9+
- Tkinter/ttk (standard library)
- pandas (CSV export)
- ttkbootstrap (optional)

## 📜 License
MIT — see [LICENSE](LICENSE).

## 🤝 Contributing
PRs welcome! Keep changes focused and include before/after notes or screenshots for UI tweaks.
