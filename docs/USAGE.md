# Cryovault – Usage Guide

## 1) Select Source
Choose the folder you want to organize. Optionally tick **Include Subdirectories**.

## 2) Scan File Types
Click **Scan File Types** to list extensions found under the source.

## 3) Build Categories
Use **Add Category** to create a new bucket (e.g., Documents, Photos).  
Define extensions (comma‑separated) and choose a **Destination Folder**.

- The built‑in `other_files` category acts as a catch‑all (can be empty).

## 4) Preview
Click **Preview Organization** to export a CSV showing:
- Current Path → Destination Path → Category

Default filename: `cryovault_preview.csv`

## 5) Organize
Click **Organize Files** to move items into their destinations.  
A summary appears in the Activity panel. You can save the log CSV (default `cryovault_log.csv`).

## Tips
- Duplicate filenames are auto‑de‑conflicted by appending `_1`, `_2`, etc.
- Categories and destinations are saved in `cryovault_config.json`.
- Application logs are written to `cryovault.log`.
