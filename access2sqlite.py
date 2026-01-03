#!/usr/bin/env python3
"""
Access to SQLite Converter

A utility to convert Microsoft Access databases (.accdb, .mdb) to SQLite format.
"""

import argparse
import os
import sys
import sqlite3
import pyodbc
import pandas as pd
from typing import List, Dict, Any
import logging

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
    
    def convert_table(self, table_name: str, chunk_size: int = 1000) -> None:
        """
        Convert a single table from Access to SQLite.
        
        Args:
            table_name (str): Name of the table to convert
            chunk_size (int): Number of rows to process at once
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
            
            access_conn.close()
            sqlite_conn.close()
            
            logger.info(f"Successfully converted table: {table_name}")
            
        except Exception as e:
            logger.error(f"Error converting table {table_name}: {e}")
            raise
    
    def convert_all_tables(self, chunk_size: int = 1000) -> None:
        """
        Convert all tables from Access to SQLite.
        
        Args:
            chunk_size (int): Number of rows to process at once
        """
        tables = self.get_table_names()
        logger.info(f"Found {len(tables)} tables to convert")
        
        for table_name in tables:
            try:
                self.convert_table(table_name, chunk_size)
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


def main():
    """Main function to handle command-line interface."""
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
    
    parser.add_argument('access_db', help='Path to Access database file (.accdb or .mdb)')
    parser.add_argument('--output', '-o', help='Output SQLite database path (default: same as input with .sqlite extension)')
    parser.add_argument('--chunk-size', '-c', type=int, default=1000, help='Number of rows to process at once (default: 1000)')
    parser.add_argument('--info', '-i', action='store_true', help='Show database information without converting')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
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
