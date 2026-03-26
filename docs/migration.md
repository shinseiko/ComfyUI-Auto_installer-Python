# Migrating from the PowerShell Version

If you're currently using the **PowerShell version** (`ComfyUI-Auto_installer-PS`), you can
migrate to the Python version with a single command.

## What's Preserved

All your user data is **fully preserved**:

- ✅ All models (checkpoints, LoRA, VAE, etc.)
- ✅ All generated outputs
- ✅ ComfyUI source code
- ✅ All custom nodes (bundled + user-installed)
- ✅ ComfyUI user settings

## What's Replaced

Only the installer infrastructure is replaced:

- ❌ PowerShell scripts (`scripts/*.ps1`, `*.psm1`)
- ❌ Old Python environment (Conda `UmeAiRT` or old `venv`)
- ❌ Old `.bat` launchers
- ❌ `custom_nodes.csv`, old `dependencies.json`, `snapshot.json`

## Migration Steps

### Option A: One-Liner (Recommended)

Open PowerShell **in your installation directory** and run:

```powershell
irm https://get.umeai.art/migrate.ps1 | iex
```

The script will:

1. Auto-detect your PowerShell installation (current directory, parent, or common paths)
2. Show a summary of what will be preserved / removed
3. Ask for confirmation with a backup suggestion
4. Clean up PS-specific files
5. Bootstrap the new Python environment (`uv` + `venv`)
6. Run the Python installer (reuses existing ComfyUI and all custom nodes)
7. Reinstall Python dependencies for **every** custom node

!!! warning "Irreversible Operation"
    The migration permanently deletes the old PowerShell scripts and Python environment.
    Back up your installation folder before proceeding:

    ```powershell
    Copy-Item -Recurse "C:\Path\To\ComfyUI" "C:\Path\To\ComfyUI_backup"
    ```

### Option B: Manual Migration

If you prefer to migrate manually:

1. **Back up** your installation folder
2. Delete the old PS infrastructure:
    - `scripts/*.ps1`, `scripts/*.psm1`
    - `scripts/venv/` (old Python environment)
    - `scripts/custom_nodes.csv`, `scripts/dependencies.json`, `scripts/snapshot.json`
    - `scripts/environment.yml`, `scripts/install_type`
    - Old `.bat` launchers (`UmeAiRT-Install-ComfyUI.bat`, etc.)
3. Download the [Python installer](https://github.com/UmeAiRT/ComfyUI-Auto_installer-Python)
4. Run `Install.bat` and point it to the **same directory** — it will detect existing ComfyUI and custom nodes

## Troubleshooting

### A custom node fails to load after migration

Some user-installed nodes may not properly declare their Python dependencies in `requirements.txt`.
Install the missing package manually:

```powershell
& "path\to\scripts\venv\Scripts\python.exe" -m pip install <missing-package>
```

### The script can't find my installation

If auto-detection fails, the script will prompt you to enter the path manually.
Point it to the root folder that contains `ComfyUI/`, `models/`, and `scripts/`.
