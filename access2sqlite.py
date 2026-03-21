#!/usr/bin/env python3
"""
Access to SQLite Converter

A utility to convert Microsoft Access databases (.accdb, .mdb) to SQLite format.
"""

import argparse
import sys
import logging

from access2sqlite_core import AccessToSQLite

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
