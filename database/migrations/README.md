"""
This folder is for storing database migration scripts and utilities.

How to Implement:
- Place SQL migration scripts here (e.g., 001_create_tables.sql, 002_add_column.sql).
- Use the provided `migration_utils.py` to list, apply, or rollback migrations.
- Example usage:

```python
from database.migrations.migration_utils import list_migrations, apply_migration
import mysql.connector

conn = mysql.connector.connect(...)
for migration in list_migrations('database/migrations'):
    apply_migration(f'database/migrations/{migration}', conn)
```

## Migration Script Schema

Each migration script should follow this structure:

- **File Naming:** Use a sequential and descriptive naming convention, e.g., `001_create_users_table.sql`, `002_add_index_to_transactions.sql`.
- **Sections:** Scripts should be divided into `-- Up` and `-- Down` sections.
    - `-- Up`: Contains SQL statements to apply the migration (e.g., create tables, add columns).
    - `-- Down`: Contains SQL statements to rollback the migration (e.g., drop tables, remove columns).

### Example Migration Script

```sql
-- Up
CREATE TABLE example (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL
);

-- Down
DROP TABLE example;
```
"""
