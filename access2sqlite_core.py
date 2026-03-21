#!/usr/bin/env python3
"""
Access to SQLite Converter - Core Module

Shared converter class for both CLI and GUI versions.
"""

import os
import sqlite3
import pyodbc
import pandas as pd
from typing import List, Dict, Any, Optional, Callable
import logging

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
        Convert a single table from Access to SQLite.
        
        Args:
            table_name (str): Name of the table to convert
            chunk_size (int): Number of rows to process at once
            progress_callback: Optional callback function to report progress (table_name, rows_processed, total_tables, current_table)
            total_tables: Total number of tables (for progress calculation)
            current_table: Current table number (for progress calculation)
        """
        access_conn = None
        sqlite_conn = None
        
        try:
            # Connect to Access database
            conn_str = self._get_connection_string()
            access_conn = pyodbc.connect(conn_str)
            
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(self.sqlite_db_path)
            
            logger.info(f"Converting table: {table_name}")
            
            # Check if table has an ID column for efficient chunking
            cursor = access_conn.cursor()
            cursor.execute(f"SELECT TOP 1 * FROM [{table_name}]")
            columns = [column[0] for column in cursor.description]
            
            # Look for ID column (case-insensitive)
            id_column = None
            for col in columns:
                if col.upper() == 'ID':
                    id_column = col
                    break
            
            # Read data from Access in chunks
            total_rows = 0
            first_chunk = True
            last_id = 0
            
            while True:
                # Build query based on whether we have an ID column
                if id_column and not first_chunk:
                    # Use ID-based pagination for tables with ID column (most efficient for Access)
                    query = f"SELECT TOP {chunk_size} * FROM [{table_name}] WHERE [{id_column}] > {last_id} ORDER BY [{id_column}]"
                elif first_chunk:
                    # First chunk - try to read with TOP to enable chunking
                    # If table is small, this will get everything
                    query = f"SELECT TOP {chunk_size} * FROM [{table_name}]"
                else:
                    # No ID column and not first chunk - can't paginate efficiently in Access
                    # This means we got all data in first chunk or table has no ID
                    break
                
                df = pd.read_sql(query, access_conn)
                
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
                
                total_rows += len(df)
                logger.info(f"  Processed {total_rows} rows")
                
                # Update progress if callback provided
                if progress_callback:
                    progress_callback(table_name, total_rows, total_tables, current_table)
                
                # Update last_id for next iteration if we have an ID column
                if id_column and id_column in df.columns:
                    last_id = df[id_column].max()
                    # If we got fewer rows than chunk_size, we're done
                    if len(df) < chunk_size:
                        break
                else:
                    # No ID column - we need to read all data at once
                    if first_chunk and len(df) == chunk_size:
                        # There might be more data, try to read the rest
                        logger.info(f"  Table has no ID column, reading all remaining data...")
                        query = f"SELECT * FROM [{table_name}]"
                        df_all = pd.read_sql(query, access_conn)
                        # Skip the rows we already have
                        df_remaining = df_all.iloc[chunk_size:]
                        if not df_remaining.empty:
                            df_remaining.to_sql(table_name, sqlite_conn, if_exists='append', index=False)
                            total_rows += len(df_remaining)
                            logger.info(f"  Processed {total_rows} rows")
                            if progress_callback:
                                progress_callback(table_name, total_rows, total_tables, current_table)
                    break
            
            logger.info(f"Successfully converted table: {table_name} ({total_rows} rows)")
            
        except Exception as e:
            logger.error(f"Error converting table {table_name}: {e}")
            raise
        finally:
            # Ensure connections are closed even if an error occurs
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
                # Continue with other tables
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
