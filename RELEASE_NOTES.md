# Access2SQLite Release Notes

## v1.1 - Bug Fixes and Improvements (March 2026)

### 🐛 Critical Bug Fixes

- **Fixed SQL Syntax Compatibility**: Replaced unsupported `LIMIT` clause with Access-compatible `TOP` syntax
- **Fixed OFFSET/FETCH Issues**: Removed SQL Server-specific syntax that caused errors with Access databases
- **Fixed ID-Based Chunking**: Corrected pagination logic to track actual ID values instead of row counts
- **Fixed Resource Leaks**: Added proper try-finally blocks to ensure database connections are always closed

### ✨ New Features

- **Automatic Driver Detection**: Tool now checks for Microsoft Access ODBC driver on startup
  - Provides helpful error message with download link if driver is missing
  - Lists available ODBC drivers to assist troubleshooting
- **Partial Conversion Support**: Failed table conversions no longer stop the entire process
  - Tool continues converting remaining tables
  - Keeps partial SQLite database with successful conversions
  - Logs detailed summary of successful and failed tables
- **Thread-Safe GUI Cancellation**: Improved stop button functionality
  - Uses `threading.Event()` for proper thread synchronization
  - Prevents corruption when cancelling conversions

### 🔧 Code Quality Improvements

- **Eliminated Code Duplication**: Extracted shared converter logic to `access2sqlite_core.py`
  - Both CLI and GUI versions now import from single source
  - Easier maintenance and updates
- **Better Exception Handling**: Replaced bare `except:` clauses with specific exception types
- **Enhanced Logging**: Added detailed conversion summaries showing which tables succeeded/failed
- **Improved Error Messages**: More descriptive error messages for troubleshooting

### 📝 Technical Changes

- SQL queries now use Access-compatible syntax throughout
- ID-based pagination properly tracks maximum ID value
- Tables without ID columns read all data at once (more reliable)
- All database connections properly cleaned up even on errors
- Thread-safe cancellation mechanism in GUI mode

---

# Access2SQLite GUI v1.0 - Initial Release

## 🚀 Overview
Access2SQLite GUI is a user-friendly desktop application that converts Microsoft Access databases (.accdb, .mdb) to SQLite format with a simple drag-and-drop interface. No Python installation required!

## ✨ Key Features

### 🖱️ Drag & Drop Interface
- Simply drag your Access database file (.accdb or .mdb) onto the application window
- Automatic detection and processing of the database file
- No command-line knowledge required

### 🔄 Seamless Conversion
- Converts Access databases to SQLite format in seconds
- Preserves table structure, data types, and relationships
- Handles both Access 2003 (.mdb) and Access 2007+ (.accdb) formats

### 📊 Progress Tracking
- Real-time progress indicators during conversion
- Shows number of records processed
- Clear success/failure notifications

### 🛡️ Robust Error Handling
- Comprehensive error messages for missing files or invalid formats
- Database connection issue detection
- Graceful handling of large databases

## 🖥️ System Requirements

- **Operating System**: Windows (Windows 7, 8, 10, 11)
- **Dependencies**: Microsoft Access Database Engine (usually pre-installed)
- **File Formats**: Supports .accdb (Access 2007+) and .mdb (Access 2003 and earlier)

## 📁 Output
- Creates SQLite database file (.sqlite) in the same directory as the source file
- Maintains original database name with .sqlite extension
- Preserves all table structures and data integrity

## 🔧 Technical Details

- **Chunked Processing**: Handles large databases efficiently by processing data in chunks
- **Memory Optimized**: Prevents memory issues with large datasets
- **Data Integrity**: Maintains data types and table relationships during conversion
- **Cross-Platform SQLite**: Creates SQLite databases compatible with any SQLite-compatible application

## 🚨 Important Notes

- Requires Microsoft Access Database Engine for Windows
- Large databases may take several minutes to process depending on size
- Always backup your original Access database before conversion
- The application creates a new SQLite file - original Access file remains unchanged

## 📋 Usage Instructions

1. Download and extract the Access2SQLite GUI executable
2. Drag your Access database file (.accdb or .mdb) onto the application window
3. Wait for the conversion to complete (progress will be displayed)
4. Find your new SQLite database file in the same location as the original

## 🐛 Known Issues

- Requires Windows operating system (no macOS/Linux support in this release)
- Very large databases (>1GB) may require significant processing time
- Some complex Access-specific features may not translate to SQLite

## 📞 Support

For issues, questions, or feature requests:
- Create an issue on GitHub: https://github.com/samyabdellatif/access2sqlite/issues
- Check the documentation in the main repository

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Download**: [Access2SQLite GUI v1.0](https://github.com/samyabdellatif/access2sqlite/raw/main/dist/access2sqlite_gui.exe)

**Repository**: https://github.com/samyabdellatif/access2sqlite
