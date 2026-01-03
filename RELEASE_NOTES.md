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

**Download**: [Access2SQLite GUI v1.0](https://github.com/samyabdellatif/access2sqlite/releases/latest/download/access2sqlite_gui.exe)

**Repository**: https://github.com/samyabdellatif/access2sqlite
