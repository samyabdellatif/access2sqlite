#!/usr/bin/env python3
"""
Access to SQLite Converter - Lightweight Core Module

Lightweight version without pandas dependency for smaller executable size.
"""

import os
import sqlite3
import pyodbc
from typing import List, Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class AccessToSQLite:
    """Convert Microsoft Access databases to SQLite format (lightweight version)."""
    
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
        
        # Check if Access ODBC driver is available
        self._check_access_driver()
    
    def _generate_sqlite_path(self, access_path: str) -> str:
        """Generate SQLite database path based on Access database path."""
        base_name = os.path.splitext(access_path)[0]
        return f"{base_name}.sqlite"
    
    def _check_access_driver(self) -> None:
        """Check if Microsoft Access ODBC driver is available."""
        try:
            drivers = pyodbc.drivers()
            access_drivers = [d for d in drivers if 'access' in d.lower()]
            
            if not access_drivers:
                error_msg = (
                    "Microsoft Access ODBC driver not found.\n\n"
                    "To use this tool, you need to install the Microsoft Access Database Engine.\n\n"
                    "Download from: https://www.microsoft.com/en-us/download/details.aspx?id=54920\n\n"
                    "Available ODBC drivers on your system:\n"
                )
                for driver in drivers:
                    error_msg += f"  - {driver}\n"
                raise RuntimeError(error_msg)
            
            logger.debug(f"Found Access drivers: {access_drivers}")
        except Exception as e:
            if "Microsoft Access ODBC driver not found" in str(e):
                raise
            logger.warning(f"Could not verify Access driver availability: {e}")
    
    def _get_connection_string(self) -> str:
        """Generate ODBC connection string for Access database."""
        if self.access_db_path.lower().endswith('.accdb'):
            # Access 2007 and later
            driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'
        else:
            # Access 2003 and earlier
            driver = '{Microsoft Access Driver (*.mdb)}'
        
        return f'DRIVER={driver};DBQ={self.access_db_path};'
    
    def _access_type_to_sqlite(self, access_type: str) -> str:
        """Map Access data types to SQLite types."""
        access_type_upper = access_type.upper()
        
        # SQLite type mapping
        if 'INT' in access_type_upper or 'LONG' in access_type_upper or 'COUNTER' in access_type_upper:
            return 'INTEGER'
        elif 'REAL' in access_type_upper or 'DOUBLE' in access_type_upper or 'FLOAT' in access_type_upper:
            return 'REAL'
        elif 'CURRENCY' in access_type_upper or 'MONEY' in access_type_upper or 'DECIMAL' in access_type_upper:
            return 'REAL'
        elif 'DATE' in access_type_upper or 'TIME' in access_type_upper:
            return 'TEXT'
        elif 'BIT' in access_type_upper or 'YESNO' in access_type_upper or 'LOGICAL' in access_type_upper:
            return 'INTEGER'
        elif 'MEMO' in access_type_upper or 'TEXT' in access_type_upper or 'VARCHAR' in access_type_upper:
            return 'TEXT'
        elif 'BLOB' in access_type_upper or 'BINARY' in access_type_upper or 'IMAGE' in access_type_upper:
            return 'BLOB'
        else:
            return 'TEXT'  # Default to TEXT for unknown types
    
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
                except Exception:
                    # Fallback to explicit TABLE type if above fails
                    for row in cursor.tables(tableType='TABLE'):
                        tables.append(row.table_name)
                
                # Remove duplicates and sort
                tables = sorted(list(set(tables)))
                return tables
        except Exception as e:
            logger.error(f"Error getting table names: {e}")
            raise
    
    def convert_table(self, table_name: str, chunk_size: int = 1000, 
                     progress_callback: Optional[Callable[[str, int, int, int], None]] = None,
                     total_tables: int = 1, current_table: int = 1) -> None:
        """
        Convert a single table from Access to SQLite using direct cursor operations (no pandas).
        
        Args:
            table_name (str): Name of the table to convert
            chunk_size (int): Number of rows to process at once
            progress_callback: Optional callback function to report progress
            total_tables: Total number of tables
            current_table: Current table number
        """
        access_conn = None
        sqlite_conn = None
        
        try:
            # Connect to databases
            conn_str = self._get_connection_string()
            access_conn = pyodbc.connect(conn_str)
            sqlite_conn = sqlite3.connect(self.sqlite_db_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            logger.info(f"Converting table: {table_name}")
            
            # Get table structure
            access_cursor = access_conn.cursor()
            access_cursor.execute(f"SELECT TOP 1 * FROM [{table_name}]")
            
            columns = [column[0] for column in access_cursor.description]
            
            # Create SQLite table
            col_defs = ', '.join([f'[{col}] TEXT' for col in columns])  # Use TEXT for simplicity
            sqlite_cursor.execute(f"DROP TABLE IF EXISTS [{table_name}]")
            sqlite_cursor.execute(f"CREATE TABLE [{table_name}] ({col_defs})")
            
            # Look for ID column for efficient chunking
            id_column = None
            for col in columns:
                if col.upper() == 'ID':
                    id_column = col
                    break
            
            # Transfer data in chunks
            total_rows = 0
            last_id = 0
            first_chunk = True
            
            while True:
                # Build query
                if id_column and not first_chunk:
                    query = f"SELECT TOP {chunk_size} * FROM [{table_name}] WHERE [{id_column}] > {last_id} ORDER BY [{id_column}]"
                elif first_chunk:
                    query = f"SELECT TOP {chunk_size} * FROM [{table_name}]"
                else:
                    break
                
                access_cursor.execute(query)
                rows = access_cursor.fetchall()
                
                if not rows:
                    break
                
                # Insert into SQLite
                placeholders = ','.join(['?' for _ in columns])
                insert_sql = f"INSERT INTO [{table_name}] VALUES ({placeholders})"
                
                # Convert rows to list of tuples
                rows_data = [tuple(row) for row in rows]
                sqlite_cursor.executemany(insert_sql, rows_data)
                sqlite_conn.commit()
                
                total_rows += len(rows)
                logger.info(f"  Processed {total_rows} rows")
                
                if progress_callback:
                    progress_callback(table_name, total_rows, total_tables, current_table)
                
                # Check if we should continue
                if id_column:
                    last_id = max(row[columns.index(id_column)] for row in rows if row[columns.index(id_column)] is not None)
                    if len(rows) < chunk_size:
                        break
                    first_chunk = False
                else:
                    # No ID column - check if we got all data
                    if first_chunk and len(rows) == chunk_size:
                        # Might be more data, read rest
                        logger.info(f"  Table has no ID column, reading remaining data...")
                        access_cursor.execute(f"SELECT * FROM [{table_name}]")
                        all_rows = access_cursor.fetchall()
                        if len(all_rows) > chunk_size:
                            remaining_rows = [tuple(row) for row in all_rows[chunk_size:]]
                            sqlite_cursor.executemany(insert_sql, remaining_rows)
                            sqlite_conn.commit()
                            total_rows = len(all_rows)
                            logger.info(f"  Processed {total_rows} rows")
                            if progress_callback:
                                progress_callback(table_name, total_rows, total_tables, current_table)
                    break
            
            logger.info(f"Successfully converted table: {table_name} ({total_rows} rows)")
            
        except Exception as e:
            logger.error(f"Error converting table {table_name}: {e}")
            raise
        finally:
            # Ensure connections are closed
            if access_conn:
                try:
                    access_conn.close()
                except Exception:
                    pass
            if sqlite_conn:
                try:
                    sqlite_conn.close()
                except Exception:
                    pass
    
    def convert_all_tables(self, chunk_size: int = 1000, 
                          progress_callback: Optional[Callable[[str, int, int, int], None]] = None) -> None:
        """
        Convert all tables from Access to SQLite.
        
        Args:
            chunk_size (int): Number of rows to process at once
            progress_callback: Optional callback function to report progress
        """
        tables = self.get_table_names()
        logger.info(f"Found {len(tables)} tables to convert")
        
        successful_tables = []
        failed_tables = []
        
        for i, table_name in enumerate(tables, 1):
            try:
                self.convert_table(table_name, chunk_size, progress_callback, len(tables), i)
                successful_tables.append(table_name)
            except Exception as e:
                logger.error(f"Failed to convert table {table_name}: {e}")
                failed_tables.append((table_name, str(e)))
                continue
        
        # Log summary
        logger.info(f"\nConversion Summary:")
        logger.info(f"  Successfully converted: {len(successful_tables)}/{len(tables)} tables")
        if successful_tables:
            logger.info(f"  Success: {', '.join(successful_tables)}")
        if failed_tables:
            logger.warning(f"  Failed: {len(failed_tables)} tables")
            for table_name, error in failed_tables:
                logger.warning(f"    - {table_name}: {error}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the Access database."""
        try:
            tables = self.get_table_names()
            
            info = {
                'tables': tables,
                'total_records': 0
            }
            
            # Get record counts
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
