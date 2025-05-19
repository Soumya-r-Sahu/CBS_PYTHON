# database/python/utilities/compare_tools.py
"""
Database comparison utilities for Core Banking System.

These utilities allow for comparison between two databases, generating 
schema difference reports, and help identify inconsistencies.
"""

import logging
import os
import datetime
import sqlalchemy as sa
from sqlalchemy import inspect, MetaData
from typing import Dict, List, Tuple, Any, Optional

# Import from database module
from database.python.connection.connection_manager import engine, Base
from database.python.connection.db_connection import DatabaseConnection

# Set up logger
logger = logging.getLogger(__name__)

def compare_databases(source_connection_string: str, target_connection_string: str) -> Dict[str, Any]:
    """
    Compare two databases and return a report of differences.
    
    Args:
        source_connection_string: Connection string for the source database
        target_connection_string: Connection string for the target database
        
    Returns:
        A dictionary containing comparison results
    """
    logger.info(f"Comparing databases: source vs target")
    
    # Create engines for both databases
    source_engine = sa.create_engine(source_connection_string)
    target_engine = sa.create_engine(target_connection_string)
    
    # Get metadata from both databases
    source_meta = MetaData()
    source_meta.reflect(bind=source_engine)
    
    target_meta = MetaData()
    target_meta.reflect(bind=target_engine)
    
    # Compare table structures
    source_tables = set(source_meta.tables.keys())
    target_tables = set(target_meta.tables.keys())
    
    # Find differences
    tables_only_in_source = source_tables - target_tables
    tables_only_in_target = target_tables - source_tables
    common_tables = source_tables.intersection(target_tables)
    
    # Compare schema of common tables
    schema_differences = {}
    for table_name in common_tables:
        source_table = source_meta.tables[table_name]
        target_table = target_meta.tables[table_name]
        
        # Compare columns
        source_columns = {col.name: col for col in source_table.columns}
        target_columns = {col.name: col for col in target_table.columns}
        
        columns_only_in_source = set(source_columns.keys()) - set(target_columns.keys())
        columns_only_in_target = set(target_columns.keys()) - set(source_columns.keys())
        
        column_type_differences = {}
        for col_name in set(source_columns.keys()).intersection(set(target_columns.keys())):
            source_col = source_columns[col_name]
            target_col = target_columns[col_name]
            
            # Compare column types and attributes
            if str(source_col.type) != str(target_col.type):
                column_type_differences[col_name] = {
                    'source_type': str(source_col.type),
                    'target_type': str(target_col.type),
                }
        
        if columns_only_in_source or columns_only_in_target or column_type_differences:
            schema_differences[table_name] = {
                'columns_only_in_source': list(columns_only_in_source),
                'columns_only_in_target': list(columns_only_in_target),
                'column_type_differences': column_type_differences
            }
    
    # Generate the report
    report = {
        'timestamp': datetime.datetime.now().isoformat(),
        'tables_only_in_source': list(tables_only_in_source),
        'tables_only_in_target': list(tables_only_in_target),
        'schema_differences': schema_differences
    }
    
    return report

def generate_schema_report(output_file: Optional[str] = None) -> str:
    """
    Generate a database schema report.
    
    Args:
        output_file: Optional path to save the report. If not provided,
                    the report will be returned as a string.
    
    Returns:
        The report content as a string
    """
    inspector = inspect(engine)
    schema_name = 'public'  # Default schema for PostgreSQL, use None for SQLite, MySQL
    
    # Get all tables
    tables = inspector.get_table_names(schema=schema_name)
    
    # Build the report
    report_lines = [
        "# Database Schema Report",
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Total tables: {len(tables)}",
        ""
    ]
    
    # Process each table
    for table_name in sorted(tables):
        report_lines.append(f"## Table: {table_name}")
        
        # Get columns
        columns = inspector.get_columns(table_name, schema=schema_name)
        report_lines.append("\n### Columns")
        report_lines.append("| Name | Type | Nullable | Default | Primary Key |")
        report_lines.append("|------|------|----------|---------|-------------|")
        
        for column in columns:
            nullable = "Yes" if column.get('nullable', True) else "No"
            default = column.get('default', '')
            primary_key = "Yes" if column.get('primary_key', False) else "No"
            
            report_lines.append(
                f"| {column['name']} | {column['type']} | {nullable} | {default} | {primary_key} |"
            )
        
        # Get foreign keys
        foreign_keys = inspector.get_foreign_keys(table_name, schema=schema_name)
        if foreign_keys:
            report_lines.append("\n### Foreign Keys")
            report_lines.append("| Name | Referred Table | Local Columns | Referred Columns |")
            report_lines.append("|------|----------------|---------------|------------------|")
            
            for fk in foreign_keys:
                name = fk.get('name', 'Unnamed')
                referred_table = fk.get('referred_table', '')
                local_cols = ', '.join(fk.get('constrained_columns', []))
                referred_cols = ', '.join(fk.get('referred_columns', []))
                
                report_lines.append(
                    f"| {name} | {referred_table} | {local_cols} | {referred_cols} |"
                )
        
        # Get indexes
        indexes = inspector.get_indexes(table_name, schema=schema_name)
        if indexes:
            report_lines.append("\n### Indexes")
            report_lines.append("| Name | Columns | Unique |")
            report_lines.append("|------|---------|--------|")
            
            for idx in indexes:
                name = idx.get('name', 'Unnamed')
                columns = ', '.join(idx.get('column_names', []))
                unique = "Yes" if idx.get('unique', False) else "No"
                
                report_lines.append(f"| {name} | {columns} | {unique} |")
        
        report_lines.append("\n")
    
    # Join all lines into a single string
    report_content = "\n".join(report_lines)
    
    # Write to file if requested
    if output_file:
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(report_content)
        logger.info(f"Schema report written to: {output_file}")
    
    return report_content
