# Access to SQLite Converter

A Python utility to convert Microsoft Access databases (.accdb, .mdb) to SQLite format.

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

[Download Access2SQLite GUI (.exe)](https://github.com/samyabdellatif/access2sqlite/dist/access2sqlite_gui.exe)

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
