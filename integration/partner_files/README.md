# Files exchanged with partners

"""
This folder is for storing files exchanged with partner organizations (e.g., other banks, payment networks).

How to Implement:
- Place files received from or sent to partners here (e.g., settlement files, reconciliation data).
- Use subfolders for each partner if needed.

Schema Example:
- File naming: <partner>_<date>_<type>.csv
- Each file should include: transaction_id, partner_id, amount, status, timestamp.

**CSV Schema:**
- Columns: `transaction_id` (string/integer), `partner_id` (string), `amount` (float), `status` (string), `timestamp` (ISO 8601 string)

**Steps to Use the Schema in Python:**
1. Define a Python dataclass or dictionary matching the CSV columns.
2. Use the `csv` module to read/write files.
3. Parse and validate each row according to the schema.

**Python Example:**
```python
from dataclasses import dataclass
from typing import List
import csv

@dataclass
class PartnerFileEntry:
    transaction_id: str
    partner_id: str
    amount: float
    status: str
    timestamp: str

# Reading CSV
with open('partner_20250512_settlement.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    entries: List[PartnerFileEntry] = [
        PartnerFileEntry(
            transaction_id=row['transaction_id'],
            partner_id=row['partner_id'],
            amount=float(row['amount']),
            status=row['status'],
            timestamp=row['timestamp']
        )
        for row in reader
    ]
```

Sample CSV:
transaction_id,partner_id,amount,status,timestamp
12345,XYZBANK,1000.00,SUCCESS,2025-05-12T10:00:00Z
"""
