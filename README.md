# SDE Address Update and Backup

Python/ArcPy utilities to manage address point updates between a staging file geodatabase (FGDB) and a production enterprise geodatabase (EGDB). The main flow disconnects users, optionally truncates the production feature class, then appends from staging with retry logic. Includes a helper to copy/replace a geodatabase for backups.

## Key Scripts

- `SDE_ScriptRPC/AppendTruncateAddr.py`: Orchestrates disconnect → optional truncate → append. Provides utilities:
  - `TruncOrTreat(prod_egdb, prod_table_name)`: Returns True if table has more than 1 row (used to decide truncation).
  - `appendTruncate(stage_gdb, prod_gdb, stage_table_name, prod_table_name, max_retries, truncate)`
  - `copy_geodatabase(source_gdb, destination_gdb)`: Copies a GDB to a destination, deleting any existing target first.
  - `tableRowCounts(gdb, table_name, field_name)`: Quick counts per value.

## Requirements

- Windows + ArcGIS Pro (3.x recommended)
- ArcGIS Pro Python environment (`arcgispro-py3`) with `arcpy`
- `python-dotenv` for loading `.env`

Install `python-dotenv` into the ArcGIS Pro environment if needed:

```powershell
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" -m pip install python-dotenv
```

## Configuration (.env)

Create a `.env` file in `SDE_ScriptRPC/` (same folder as the script) with entries like:

```
ERROR_LOG_NAME=C:\Logs\SDE_Addr_Update.log
PROD_EGDB=C:\Path\To\ProdConnection.sde
PROD_FEATURE_CLASS_1=schema.AddressPoints
LOCAL_FGDB=C:\Path\To\Staging.gdb
STAGE_FEATURE_CLASS=AddressPoints
XL_TEMPLET=C:\Path\To\Template.xlsx
MONTHLY_GDB=C:\Backups\AddrUpdate\2026-01\TIPS_Update.gdb
MONTHLY_FC=AddressPoints
```

Notes:
- `PROD_EGDB` should point to your .sde connection file with sufficient privileges to disconnect users and edit.
- `LOCAL_FGDB` is your staging file geodatabase path.
- Update paths to match your environment.

## Running

Run the main script with ArcGIS Pro's Python:

```powershell
"C:/Program Files/ArcGIS/Pro/bin/Python/envs/arcgispro-py3/python.exe" C:/Python/testingArcpy/SDE_ScriptRPC/AppendTruncateAddr.py
```

What it does:
- Checks `TruncOrTreat` to decide if truncate is needed.
- Disconnects all users from `PROD_EGDB`.
- Optionally truncates the production feature class.
- Appends features from `LOCAL_FGDB`:`STAGE_FEATURE_CLASS` into `PROD_EGDB`:`PROD_FEATURE_CLASS_1`.
- Retries each operation up to the configured attempts.

## Backing up a Geodatabase

Use the helper to copy and replace a GDB (parent folders are created if missing):

```python
from SDE_ScriptRPC.AppendTruncateAddr import copy_geodatabase

# Example: back up the staging FGDB before append
copy_geodatabase(os.getenv("LOCAL_FGDB"), r"C:\Backups\AddrUpdate\AddressPoints.gdb")

# Or use a path from your .env
copy_geodatabase(os.getenv("LOCAL_FGDB"), os.getenv("MONTHLY_GDB"))
```

If the destination exists, it is deleted first and replaced with a fresh copy.

## GitHub Tips

- Avoid committing large or proprietary data. Consider ignoring these in a `.gitignore`:

```
# Secrets
.env
*.key

# ArcGIS
*.sde
*.gdb/
*.gdb.zip
*.apr
*.mxd
*.lyrx
```

Commit and push changes:

```powershell
cd C:\Python\testingArcpy
git add .
git commit -m "Update scripts and README"
git push
```

## Troubleshooting

- Ensure the `.sde` connection has permissions to disconnect users and edit the target feature class.
- Close any applications or map documents locking the FGDB before copying or appending.
- Check the error log at `ERROR_LOG_NAME` for stack traces if something fails.
