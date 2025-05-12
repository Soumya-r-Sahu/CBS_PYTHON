"""
Temporary test script for analyzing database structure and relationships
Created: May 13, 2025
"""
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import get_db_session
from sqlalchemy import text
import json

def analyze_table_relationships():
    """Analyze database tables and their relationships"""
    print("🔍 Analyzing database relationships...")
    
    session = None
    try:
        session = get_db_session()
        
        # Get database name
        db_name = session.execute(text("SELECT DATABASE()")).scalar()
        print(f"Connected to database: {db_name}")
        
        # Get all tables
        tables = session.execute(text("SHOW TABLES")).fetchall()
        table_names = [table[0] for table in tables]
        print(f"Found {len(tables)} tables")
        
        # Dictionary to store table relationships
        relationships = {}
        
        # Find foreign key relationships
        for table in table_names:
            # Get create table statement to parse foreign keys
            create_stmt = session.execute(text(f"SHOW CREATE TABLE `{table}`")).fetchone()[1]
            
            # Extract foreign key information
            fk_lines = [line.strip() for line in create_stmt.split('\n') 
                      if 'FOREIGN KEY' in line]
            
            if fk_lines:
                relationships[table] = []
                for fk_line in fk_lines:
                    # Extract referenced table
                    ref_table_start = fk_line.find('REFERENCES `') + 12
                    ref_table_end = fk_line.find('`', ref_table_start)
                    ref_table = fk_line[ref_table_start:ref_table_end]
                    
                    # Extract column names
                    fk_col_start = fk_line.find('FOREIGN KEY (`') + 13
                    fk_col_end = fk_line.find('`)', fk_col_start)
                    fk_col = fk_line[fk_col_start:fk_col_end]
                    
                    ref_col_start = fk_line.find('(`', ref_table_end) + 2
                    ref_col_end = fk_line.find('`)', ref_col_start)
                    ref_col = fk_line[ref_col_start:ref_col_end]
                    
                    relationships[table].append({
                        'referenced_table': ref_table,
                        'foreign_key': fk_col,
                        'referenced_column': ref_col
                    })
        
        # Write relationships to file
        with open(os.path.join(os.path.dirname(__file__), 'db_relationships.json'), 'w') as f:
            json.dump(relationships, f, indent=2)
        
        # Print summary of relationships
        print("\n🔗 Table Relationships:")
        for table, relations in relationships.items():
            print(f"\n📋 {table}:")
            for rel in relations:
                print(f"  • References {rel['referenced_table']}.{rel['referenced_column']} via {rel['foreign_key']}")
        
        # Tables with no relationships
        isolated_tables = [t for t in table_names if t not in relationships]
        print(f"\n🔒 Tables with no foreign key relationships ({len(isolated_tables)}):")
        for table in isolated_tables:
            print(f"  • {table}")
        
        # Generate simple ER diagram representation
        generate_er_diagram_markdown(table_names, relationships)
            
    except Exception as e:
        print(f"❌ Error analyzing relationships: {e}")
    finally:
        if session:
            session.close()

def generate_er_diagram_markdown(tables, relationships):
    """Generate a simple ER diagram in Markdown format"""
    try:
        # Create the Markdown file
        with open(os.path.join(os.path.dirname(__file__), 'db_diagram.md'), 'w') as f:
            f.write("# Database Entity Relationship Diagram\n\n")
            f.write("```mermaid\nerDiagram\n")
            
            # Add all tables
            for table in tables:
                f.write(f"    {table} {{\n")
                
                # Try to get table columns
                try:
                    session = get_db_session()
                    columns = session.execute(text(f"DESCRIBE {table}")).fetchall()
                    
                    for col in columns:
                        col_name = col[0]
                        col_type = col[1]
                        pk_indicator = "PK" if col[3] == 'PRI' else ""
                        
                        f.write(f"        {col_type} {col_name} {pk_indicator}\n")
                    
                    session.close()
                except Exception:
                    f.write("        -- Column info unavailable --\n")
                
                f.write("    }\n")
            
            # Add relationships
            for table, relations in relationships.items():
                for rel in relations:
                    ref_table = rel['referenced_table']
                    f.write(f"    {table} ||--o{{ {ref_table} : references\n")
            
            f.write("```\n")
            
            print(f"ER diagram Markdown saved to {os.path.join(os.path.dirname(__file__), 'db_diagram.md')}")
    
    except Exception as e:
        print(f"❌ Error generating ER diagram: {e}")

if __name__ == "__main__":
    analyze_table_relationships()
