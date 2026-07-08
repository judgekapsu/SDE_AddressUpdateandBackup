# SDE Address Update and Backup

Python/ArcPy utilities to manage address point updates between a local file geodatabase (FGDB) and a production enterprise geodatabase (EGDB). The current workflow creates a temporary staging feature class from local address points, disconnects users, optionally truncates production, then appends with retry logic. Includes a helper to copy/replace a geodatabase for backups.

## Key Scripts

- `SDE_ScriptAddresses/AppendTruncateAddr.py`: Orchestrates backup copy → temp stage creation → disconnect → optional truncate → append for both address points and centerlines. Provides utilities:
  - `makeStage(local_fgdb, localFeatureClass, stage_FeatureClass, where_clause="(structype<>9000)")`: Builds a temporary staging feature class from the configured source feature class.
  - `TruncOrTreat(prod_egdb, prod_table_name)`: Returns True if the target table has more than 1 row (used to decide truncation).
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

### Setup Instructions

1. Copy `template.env` to `.env` in the `SDE_ScriptAddresses/` folder (same folder as the script):
   ```powershell
   Copy-Item template.env .env
   ```

2. Open `.env` in your text editor and fill in the paths for your environment

3. Each variable is documented in `template.env` with examples and descriptions

### Environment Variables

| Variable | Purpose | Notes |
|----------|---------|-------|
| `ERROR_LOG_NAME` | Log file path for errors | Directory or file path where logs are written |
| `PROD_EGDB` | Production SDE connection file | Must have privileges to disconnect users and edit |
| `PROD_FEATURE_CLASS_1` | Production feature class | Format: `schema.sde.FeatureClassName` |
| `LOCAL_FGDB` | Staging file geodatabase | Contains the staged data to append |
| `local_FEATURE_CLASS` | Source local address points feature class | Input class used to build temp stage (filtered where `structype<>9000`) |
| `STAGE_FEATURE_CLASS` | Staging feature class name | Table within LOCAL_FGDB to append from |
| `ADDRESS_WHERE_CLAUSE` | Optional address filter | Default is `(structype<>9000)` |
| `CENTERLINE_LOCAL_FEATURE_CLASS` | Centerline source feature class | Feature class inside LOCAL_FGDB to stage from |
| `CENTERLINE_STAGE_FEATURE_CLASS` | Centerline staging feature class | Table within LOCAL_FGDB to append from |
| `CENTERLINE_PROD_FEATURE_CLASS` | Centerline production feature class | Format: `schema.sde.FeatureClassName` |
| `CENTERLINE_WHERE_CLAUSE` | Optional centerline filter | Leave blank for no filter |
| `XL_TEMPLET` | Excel template path | Optional, may be used for reporting |
| `MONTHLY_GDB` | Monthly backup directory | Optional, for archival purposes |
| `MONTHLY_FC` | Monthly shapefile name | Optional, for archival purposes |
| `SAFE_FGDB` | Safe copy/backup geodatabase | Where LOCAL_FGDB is copied for safety |

### Important Notes

- Use **`template.env`** as a reference—do not commit your actual `.env` file to version control
- All paths should be UNC paths (`\\\\server\share`) or local absolute paths (e.g., `C:\path\to\gdb`)
- Ensure the account running the script has read/write access to all specified paths

## Running

Run the main script with ArcGIS Pro's Python:

```powershell
"C:/Program Files/ArcGIS/Pro/bin/Python/envs/arcgispro-py3/python.exe" "\\APNSDS4\Projects\MontCo_E911\Scripts\SDE_ScriptAddresses\AppendTruncateAddr.py"
```

What it does:
- Copies `LOCAL_FGDB` to `SAFE_FGDB` as a safety backup.
- Builds/refreshes temp staging data by creating `STAGE_FEATURE_CLASS` from the address source feature class.
- If centerline settings are present, it runs the same workflow for the centerline dataset as well.
- Checks `TruncOrTreat` to decide if truncate is needed.
- Disconnects all users from `PROD_EGDB`.
- Optionally truncates the production feature class.
- Appends features from `LOCAL_FGDB` into production using the configured staging and production feature classes.
- Retries each operation up to the configured attempts.

## Backing up a Geodatabase

Use the helper to copy and replace a GDB (parent folders are created if missing):

```python
from SDE_ScriptAddresses.AppendTruncateAddr import copy_geodatabase

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
