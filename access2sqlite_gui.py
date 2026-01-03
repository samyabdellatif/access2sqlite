#!/usr/bin/env python3
"""
Access to SQLite Converter - GUI Version

A utility to convert Microsoft Access databases (.accdb, .mdb) to SQLite format with a GUI interface.
"""

import argparse
import os
import sys
import sqlite3
import pyodbc
import pandas as pd
from typing import List, Dict, Any
import logging
import time
import threading
from tkinter import Tk, ttk, messagebox, filedialog, StringVar, IntVar, Text, Scrollbar, END, DISABLED, NORMAL
import tkinter as tk

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AccessToSQLite:
    """Convert Microsoft Access databases to SQLite format."""
    
    def __init__(self, access_db_path: str, sqlite_db_path: str = None):
        """
        Initialize the converter.
        
        Args:
            access_db_path (str): Path to the Access database file (.accdb or .mdb)
            sqlite_db_path (str): Path where SQLite database will be created
        """
        self.access_db_path = access_db_path
        self.sqlite_db_path = sqlite_db_path or self._generate_sqlite_path(access_db_path)
        
        # Validate input file
        if not os.path.exists(access_db_path):
            raise FileNotFoundError(f"Access database file not found: {access_db_path}")
        
        # Check file extension
        if not access_db_path.lower().endswith(('.accdb', '.mdb')):
            raise ValueError("Input file must be an Access database (.accdb or .mdb)")
    
    def _generate_sqlite_path(self, access_path: str) -> str:
        """Generate SQLite database path based on Access database path."""
        base_name = os.path.splitext(access_path)[0]
        return f"{base_name}.sqlite"
    
    def _get_connection_string(self) -> str:
        """Generate ODBC connection string for Access database."""
        if self.access_db_path.lower().endswith('.accdb'):
            # Access 2007 and later
            driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'
        else:
            # Access 2003 and earlier
            driver = '{Microsoft Access Driver (*.mdb)}'
        
        return f'DRIVER={driver};DBQ={self.access_db_path};'
    
    def get_table_names(self) -> List[str]:
        """Get list of table names from Access database."""
        try:
            conn_str = self._get_connection_string()
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                tables = []
                
                # Try to get all tables without filtering by type first
                try:
                    for row in cursor.tables():
                        if row.table_type in ['TABLE', 'VIEW'] and not row.table_name.startswith('MSys'):
                            tables.append(row.table_name)
                except:
                    # Fallback to explicit TABLE type if above fails
                    for row in cursor.tables(tableType='TABLE'):
                        tables.append(row.table_name)
                
                # Remove duplicates and sort
                tables = sorted(list(set(tables)))
                return tables
        except Exception as e:
            logger.error(f"Error getting table names: {e}")
            raise
    
    def convert_table(self, table_name: str, chunk_size: int = 1000, progress_callback=None, total_tables=1, current_table=1) -> None:
        """
        Convert a single table from Access to SQLite.
        
        Args:
            table_name (str): Name of the table to convert
            chunk_size (int): Number of rows to process at once
            progress_callback: Callback function to report progress
            total_tables: Total number of tables
            current_table: Current table number
        """
        try:
            # Connect to Access database
            conn_str = self._get_connection_string()
            access_conn = pyodbc.connect(conn_str)
            
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(self.sqlite_db_path)
            
            logger.info(f"Converting table: {table_name}")
            
            # First, check if table has an ID column for chunking
            cursor = access_conn.cursor()
            cursor.execute(f"SELECT TOP 1 * FROM [{table_name}]")
            columns = [column[0] for column in cursor.description]
            has_id_column = 'ID' in columns or 'id' in columns
            
            # Read data from Access in chunks
            offset = 0
            first_chunk = True
            
            while True:
                # Read chunk of data
                query = f"SELECT * FROM [{table_name}]"
                if not first_chunk:
                    if has_id_column:
                        # Use ID-based chunking for tables with ID column
                        query = f"SELECT * FROM [{table_name}] WHERE ID > {offset} ORDER BY ID LIMIT {chunk_size}"
                    else:
                        # Use OFFSET/FETCH for tables without ID column
                        query += f" OFFSET {offset} ROWS FETCH NEXT {chunk_size} ROWS ONLY"
                
                try:
                    df = pd.read_sql(query, access_conn)
                except Exception as e:
                    # Try alternative syntax if OFFSET/FETCH fails
                    if "OFFSET" in str(e) and not has_id_column:
                        # For tables without ID, try to get all data at once if chunking fails
                        if first_chunk:
                            query = f"SELECT * FROM [{table_name}]"
                            df = pd.read_sql(query, access_conn)
                        else:
                            break  # No more data to process
                    else:
                        raise
                
                if df.empty:
                    break
                
                # Write to SQLite
                if first_chunk:
                    # Create table with proper schema
                    df.to_sql(table_name, sqlite_conn, if_exists='replace', index=False)
                    first_chunk = False
                else:
                    # Append data
                    df.to_sql(table_name, sqlite_conn, if_exists='append', index=False)
                
                offset += len(df)
                logger.info(f"  Processed {offset} rows")
                
                # Update progress
                if progress_callback:
                    progress_callback(table_name, offset, total_tables, current_table)
            
            access_conn.close()
            sqlite_conn.close()
            
            logger.info(f"Successfully converted table: {table_name}")
            
        except Exception as e:
            logger.error(f"Error converting table {table_name}: {e}")
            raise
    
    def convert_all_tables(self, chunk_size: int = 1000, progress_callback=None) -> None:
        """
        Convert all tables from Access to SQLite.
        
        Args:
            chunk_size (int): Number of rows to process at once
            progress_callback: Callback function to report progress
        """
        tables = self.get_table_names()
        logger.info(f"Found {len(tables)} tables to convert")
        
        for i, table_name in enumerate(tables, 1):
            try:
                self.convert_table(table_name, chunk_size, progress_callback, len(tables), i)
            except Exception as e:
                logger.error(f"Failed to convert table {table_name}: {e}")
                # Continue with other tables
                continue
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the Access database."""
        try:
            # Use the improved table detection method
            tables = self.get_table_names()
            
            info = {
                'tables': tables,
                'total_records': 0
            }
            
            # Get record counts for each table
            conn_str = self._get_connection_string()
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                
                for table_name in tables:
                    try:
                        count_query = f"SELECT COUNT(*) FROM [{table_name}]"
                        count_result = cursor.execute(count_query).fetchone()
                        record_count = count_result[0] if count_result else 0
                        info['total_records'] += record_count
                    except Exception as e:
                        logger.warning(f"Could not get record count for {table_name}: {e}")
                
                return info
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            raise


class AccessConverterGUI:
    """GUI for Access to SQLite converter."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Access to SQLite Converter")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Variables
        self.access_file_var = StringVar()
        self.output_file_var = StringVar()
        self.chunk_size_var = IntVar(value=1000)
        self.progress_var = IntVar(value=0)
        self.status_var = StringVar(value="Ready")
        
        self.converter = None
        self.conversion_thread = None
        self.stop_conversion = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the GUI interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="Access Database:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        access_entry = ttk.Entry(file_frame, textvariable=self.access_file_var, width=50)
        access_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=2)
        
        browse_btn = ttk.Button(file_frame, text="Browse...", command=self.browse_access_file)
        browse_btn.grid(row=0, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(file_frame, text="Output SQLite:").grid(row=1, column=0, sticky=tk.W, pady=2)
        
        output_entry = ttk.Entry(file_frame, textvariable=self.output_file_var, width=50)
        output_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=2)
        
        output_browse_btn = ttk.Button(file_frame, text="Browse...", command=self.browse_output_file)
        output_browse_btn.grid(row=1, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(options_frame, text="Chunk size:").grid(row=0, column=0, sticky=tk.W, pady=2)
        chunk_spinbox = ttk.Spinbox(options_frame, from_=100, to=10000, textvariable=self.chunk_size_var, width=10)
        chunk_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Progress
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # Console output
        console_frame = ttk.LabelFrame(main_frame, text="Console Output", padding="10")
        console_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        
        self.console_text = Text(console_frame, height=10, width=50)
        self.console_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = Scrollbar(console_frame, orient="vertical", command=self.console_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.console_text.configure(yscrollcommand=scrollbar.set)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        self.convert_btn = ttk.Button(button_frame, text="Convert", command=self.start_conversion)
        self.convert_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_conversion_func, state=DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=(5, 5))
        
        self.info_btn = ttk.Button(button_frame, text="Show Info", command=self.show_info)
        self.info_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
    def browse_access_file(self):
        """Browse for Access database file."""
        file_path = filedialog.askopenfilename(
            title="Select Access Database",
            filetypes=[("Access Database", "*.accdb;*.mdb"), ("All Files", "*.*")]
        )
        if file_path:
            self.access_file_var.set(file_path)
            # Auto-generate output path
            base_name = os.path.splitext(file_path)[0]
            self.output_file_var.set(f"{base_name}.sqlite")
    
    def browse_output_file(self):
        """Browse for output SQLite file."""
        file_path = filedialog.asksaveasfilename(
            title="Save SQLite Database",
            defaultextension=".sqlite",
            filetypes=[("SQLite Database", "*.sqlite"), ("All Files", "*.*")]
        )
        if file_path:
            self.output_file_var.set(file_path)
    
    def log_message(self, message):
        """Add message to console output."""
        self.console_text.insert(END, message + "\n")
        self.console_text.see(END)
        self.root.update_idletasks()
    
    def update_progress(self, table_name, rows_processed, total_tables, current_table):
        """Update progress bar and status."""
        if self.stop_conversion:
            raise Exception("Conversion stopped by user")
        
        # Calculate overall progress
        table_progress = (current_table - 1) / total_tables * 100
        table_progress += (1 / total_tables) * (rows_processed / 1000)  # Rough estimate
        
        self.progress_var.set(min(100, int(table_progress)))
        self.status_var.set(f"Converting {table_name}... ({rows_processed} rows processed)")
        self.root.update_idletasks()
    
    def start_conversion(self):
        """Start the conversion process."""
        access_file = self.access_file_var.get()
        output_file = self.output_file_var.get()
        chunk_size = self.chunk_size_var.get()
        
        if not access_file:
            messagebox.showerror("Error", "Please select an Access database file")
            return
        
        if not output_file:
            messagebox.showerror("Error", "Please specify an output SQLite file")
            return
        
        try:
            # Create converter
            self.converter = AccessToSQLite(access_file, output_file)
            
            # Check if output file exists
            if os.path.exists(output_file):
                if not messagebox.askyesno("Warning", f"Output file {output_file} already exists. Overwrite?"):
                    return
            
            # Disable UI elements
            self.convert_btn.config(state=DISABLED)
            self.stop_btn.config(state=NORMAL)
            self.stop_conversion = False
            
            # Clear console
            self.console_text.delete(1.0, END)
            self.log_message(f"Starting conversion...")
            self.log_message(f"Input: {access_file}")
            self.log_message(f"Output: {output_file}")
            
            # Start conversion in a separate thread
            self.conversion_thread = threading.Thread(target=self.run_conversion, args=(chunk_size,))
            self.conversion_thread.daemon = True
            self.conversion_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.convert_btn.config(state=NORMAL)
            self.stop_btn.config(state=DISABLED)
    
    def run_conversion(self, chunk_size):
        """Run the conversion in a separate thread."""
        try:
            # Show database info first
            info = self.converter.get_database_info()
            self.log_message(f"Found {len(info['tables'])} tables with {info['total_records']:,} total records")
            
            # Convert all tables
            self.converter.convert_all_tables(chunk_size, self.update_progress)
            
            # Success
            self.log_message("Conversion completed successfully!")
            self.log_message(f"SQLite database created: {self.converter.sqlite_db_path}")
            
            # Reset progress
            self.progress_var.set(100)
            self.status_var.set("Conversion completed!")
            
            # Re-enable UI
            self.root.after(0, self.enable_ui)
            
            # Show success message
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Conversion completed!\nSQLite database created: {self.converter.sqlite_db_path}"))
            
        except Exception as e:
            self.log_message(f"Error: {e}")
            self.status_var.set("Conversion failed!")
            self.root.after(0, self.enable_ui)
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    def stop_conversion_func(self):
        """Stop the conversion process."""
        self.stop_conversion = True
        self.status_var.set("Stopping conversion...")
        self.log_message("Stopping conversion...")
    
    def enable_ui(self):
        """Re-enable UI elements after conversion."""
        self.convert_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
    
    def show_info(self):
        """Show database information."""
        access_file = self.access_file_var.get()
        
        if not access_file:
            messagebox.showerror("Error", "Please select an Access database file")
            return
        
        try:
            converter = AccessToSQLite(access_file)
            info = converter.get_database_info()
            
            info_text = f"Database: {access_file}\n\n"
            info_text += f"Tables ({len(info['tables'])}):\n"
            for table in info['tables']:
                info_text += f"  - {table}\n"
            info_text += f"\nTotal records: {info['total_records']:,}"
            
            messagebox.showinfo("Database Information", info_text)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))


def main():
    """Main function to handle command-line interface and GUI."""
    parser = argparse.ArgumentParser(
        description='Convert Microsoft Access database to SQLite format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python access2sqlite.py database.accdb
  python access2sqlite.py database.accdb --output converted.sqlite
  python access2sqlite.py database.accdb --chunk-size 500
        """
    )
    
    parser.add_argument('access_db', nargs='?', help='Path to Access database file (.accdb or .mdb)')
    parser.add_argument('--output', '-o', help='Output SQLite database path (default: same as input with .sqlite extension)')
    parser.add_argument('--chunk-size', '-c', type=int, default=1000, help='Number of rows to process at once (default: 1000)')
    parser.add_argument('--info', '-i', action='store_true', help='Show database information without converting')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--gui', action='store_true', help='Launch GUI interface (default when no arguments provided)')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # If no arguments provided or --gui flag, launch GUI
    if not args.access_db or args.gui:
        root = Tk()
        app = AccessConverterGUI(root)
        root.mainloop()
        return
    
    try:
        # Create converter
        converter = AccessToSQLite(args.access_db, args.output)
        
        if args.info:
            # Show database information
            info = converter.get_database_info()
            print(f"Database: {args.access_db}")
            print(f"Tables ({len(info['tables'])}):")
            for table in info['tables']:
                print(f"  - {table}")
            print(f"Total records: {info['total_records']:,}")
        else:
            # Convert database
            print(f"Converting {args.access_db} to {converter.sqlite_db_path}")
            
            # Show database info first
            info = converter.get_database_info()
            print(f"Found {len(info['tables'])} tables with {info['total_records']:,} total records")
            
            # Convert all tables
            converter.convert_all_tables(args.chunk_size)
            
            print(f"Conversion completed successfully!")
            print(f"SQLite database created: {converter.sqlite_db_path}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
