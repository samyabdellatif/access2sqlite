# Access to SQLite Converter

A Python utility to convert Microsoft Access databases (.accdb, .mdb) to SQLite format on MS Windows systems.

<img width="1024" height="1024" alt="access2sqlite" src="https://github.com/user-attachments/assets/2d03141c-bba1-4b66-a17f-7112a003eaa4" />

## Features

- Converts Microsoft Access databases (.accdb, .mdb) to SQLite format
- Handles both Access 2003 (.mdb) and Access 2007+ (.accdb) formats
- Processes tables in chunks to handle large databases efficiently
- Preserves table structure and data types
- Command-line interface with multiple options

## Installation

Install the required dependencies:

```bash
pip install pyodbc pandas
```

## GUI Version

A graphical user interface version is available as an executable file for easy use without Python installation:

<img width="626" height="548" alt="Screenshot 2026-01-04 011609" src="https://github.com/user-attachments/assets/fd590efd-2092-4cfa-9dfc-4e902b40edd5" />


## Download

[Download Executable](https://github.com/samyabdellatif/access2sqlite/raw/main/dist/access2sqlite_gui.exe)

The GUI version provides the same functionality with a user-friendly interface for drag-and-drop conversion.

## Usage

### Basic Conversion

```bash
python access2sqlite.py database.accdb
```

This will create `database.sqlite` in the same directory.

### Custom Output Path

```bash
python access2sqlite.py database.accdb --output converted.sqlite
```

### Memory-Efficient Conversion for Large Databases

```bash
python access2sqlite.py database.accdb --chunk-size 500
```

### Show Database Information

```bash
python access2sqlite.py database.accdb --info
```

This displays table names and record counts without converting.

### Verbose Logging

```bash
python access2sqlite.py database.accdb --verbose
```

## Command-Line Options

- `--output, -o` - Specify output SQLite file path (default: same as input with .sqlite extension)
- `--chunk-size, -c` - Number of rows to process at once (default: 1000)
- `--info, -i` - Show database information without converting
- `--verbose, -v` - Enable verbose logging

## Requirements

- Python 3.6+
- pyodbc (for Access database connectivity)
- pandas (for data processing)
- sqlite3 (built into Python)


## Error Handling

The converter includes comprehensive error handling for:
- Missing Access database files
- Invalid file formats
- Database connection issues
- Table conversion failures

## Notes

- The converter requires Microsoft Access Database Engine to be installed on Windows for pyodbc to work with Access files
- Large databases are processed in chunks to prevent memory issues
- All tables in the Access database are converted automatically
- The converter preserves data types and table structure as much as possible

safer Ultra-Minimal Service PowerShell script, with:
	•	✅ Clear tiers
	•	✅ Optional EXTREME mode (toggleable)
	•	✅ Guards for critical services
	•	✅ Idempotent behavior
	•	✅ Verbose output
	•	✅ Easier rollback planning

This is the version you’d actually keep in a repo.

⸻

🔧 Ultra-Minimal Service Profile – UPDATED

🔹 What’s new vs previous
	•	Tier separation baked into the script
	•	-Extreme switch (opt-in)
	•	Skips non-existent services cleanly
	•	Won’t touch Tier-0 critical services
	•	More predictable on Windows 11 Pro builds

⸻

⚠️ Usage

# Safe ultra-minimal (recommended first)
.\ultra-minimal.ps1

# Extreme / appliance mode
.\ultra-minimal.ps1 -Extreme

Run PowerShell as Administrator.

⸻

🧠 Design assumptions
	•	Isolated or restricted firewall
	•	No Store / Xbox / consumer features
	•	Desktop or remote-desktop usage
	•	Explorer still enabled (not kiosk yet)

⸻

🧾 UPDATED SCRIPT

param (
    [switch]$Extreme
)

Write-Host "Applying Ultra-Minimal Windows 11 Service Profile" -ForegroundColor Cyan
Write-Host "Extreme mode: $Extreme" -ForegroundColor Yellow

# -------------------------------------------------
# Tier 0 – Never touch (documented, not used)
# -------------------------------------------------
$neverDisable = @(
    "RpcSs","DcomLaunch","LSM","Winmgmt","EventLog",
    "PlugPlay","Power","CryptSvc","SamSs","BFE"
)

# -------------------------------------------------
# Tier 2 – Ultra-minimal (safe)
# -------------------------------------------------
$ultraMinimal = @(
    # Performance / UX
    "SysMain",              # Superfetch
    "WSearch",              # Search indexing
    "FontCache",
    "TabletInputService",
    "SensrSvc",
    "lfsvc",                # Location
    "MapsBroker",

    # Telemetry / consumer
    "DiagTrack",
    "dmwappushservice",
    "WerSvc",
    "RetailDemo",
    "OneSyncSvc",
    "UserDataSvc",
    "UnistoreSvc",
    "CDPUserSvc",

    # Gaming
    "XboxGipSvc",
    "XboxNetApiSvc",
    "XblAuthManager",
    "XblGameSave",

    # Devices (only if unused)
    "Spooler",
    "Fax",
    "BluetoothUserService",
    "bthserv",
    "WiaRpc"
)

# -------------------------------------------------
# Tier 3 – EXTREME (appliance mode)
# -------------------------------------------------
$extremeOnly = @(
    "AppXSvc",      # AppX / UWP
    "ClipSVC",      # Licensing
    "LicenseManager",
    "DoSvc",        # Delivery Optimization
    "UsoSvc",       # Update Orchestrator
    "wuauserv"      # Windows Update
)

# -------------------------------------------------
# Helper: disable service safely
# -------------------------------------------------
function Disable-ServiceSafe {
    param ($Name)

    $svc = Get-Service -Name $Name -ErrorAction SilentlyContinue
    if ($null -eq $svc) {
        Write-Host "[-] $Name not found" -ForegroundColor DarkGray
        return
    }

    if ($neverDisable -contains $Name) {
        Write-Host "[!] Skipping critical service: $Name" -ForegroundColor Red
        return
    }

    if ($svc.Status -ne "Stopped") {
        Stop-Service $Name -Force -ErrorAction SilentlyContinue
    }

    Set-Service $Name -StartupType Disabled -ErrorAction SilentlyContinue
    Write-Host "[✓] Disabled: $Name" -ForegroundColor Green
}

# -------------------------------------------------
# Apply Ultra-Minimal Tier
# -------------------------------------------------
Write-Host "`nApplying ultra-minimal services..." -ForegroundColor Cyan
foreach ($svc in $ultraMinimal) {
    Disable-ServiceSafe $svc
}

# -------------------------------------------------
# Apply Extreme Tier (optional)
# -------------------------------------------------
if ($Extreme) {
    Write-Host "`nApplying EXTREME appliance services..." -ForegroundColor Magenta
    foreach ($svc in $extremeOnly) {
        Disable-ServiceSafe $svc
    }
}

# -------------------------------------------------
# Post tweaks (safe)
# -------------------------------------------------
Write-Host "`nApplying post-service optimizations..." -ForegroundColor Cyan

# Disable hibernation
powercfg /h off | Out-Null

# Disable background app execution
New-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" -Force | Out-Null
Set-ItemProperty `
    -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" `
    -Name "GlobalUserDisabled" -Type DWord -Value 1

Write-Host "`nUltra-minimal profile applied. Reboot REQUIRED." -ForegroundColor Green


⸻

📊 Expected states

Normal Ultra-Minimal
	•	🧠 Idle RAM: 1.2–1.4 GB
	•	🔧 Services: ~80
	•	🌐 No cloud retries
	•	🔄 Windows Update still possible (manual)

Extreme Mode
	•	🧠 Idle RAM: ~1.0–1.2 GB
	•	🔧 Services: ~65
	•	❌ No Store, no UWP, no updates
	•	✅ Appliance-style stability

⸻

🔄 Rollback (important)

Before running:

Get-Service | Select Name,StartType | Export-Csv services_backup.csv -NoTypeInformation

Manual restore example:

Import-Csv services_backup.csv | ForEach-Object {
    Set-Service -Name $_.Name -StartupType $_.StartType -ErrorAction SilentlyContinue
}


⸻

🧩 Next logical steps (if you want to go further)

Based on your past focus on remote desktop / lightweight systems, the next real upgrades are:

1️⃣ Explorer replacement (custom shell)
2️⃣ RDP-only / headless Windows
3️⃣ LTSC-style servicing lockdown
4️⃣ Single-app kiosk with auto-login

Say the word and I’ll give you the next script, not theory.

Less aggressive script

# ===============================
# Ultra-Minimal Service Profile
# Windows 11 Pro
# ===============================

Write-Host "Applying ultra-minimal service profile..." -ForegroundColor Cyan

$disableServices = @(
    # Performance / UX
    "SysMain",
    "WSearch",
    "FontCache",
    "TabletInputService",
    "SensrSvc",
    "lfsvc",
    "MapsBroker",

    # Cloud / Consumer
    "DiagTrack",
    "dmwappushservice",
    "WerSvc",
    "RetailDemo",
    "OneSyncSvc",
    "UserDataSvc",
    "UnistoreSvc",
    "CDPUserSvc",

    # Gaming
    "XboxGipSvc",
    "XboxNetApiSvc",
    "XblAuthManager",
    "XblGameSave",

    # Devices (optional)
    "Spooler",
    "Fax",
    "BluetoothUserService",
    "bthserv",
    "WiaRpc"
)

foreach ($svc in $disableServices) {
    Stop-Service $svc -ErrorAction SilentlyContinue
    Set-Service $svc -StartupType Disabled -ErrorAction SilentlyContinue
}

Write-Host "Ultra-minimal profile applied. Reboot required." -ForegroundColor Green