"""
Partner File Processor - Handles file exchanges with partner organizations
"""
import csv
from dataclasses import dataclass
from typing import List
import os
from datetime import datetime

@dataclass
class PartnerFileEntry:
    transaction_id: str
    partner_id: str
    amount: float
    status: str
    timestamp: str

class PartnerFileProcessor:
    def __init__(self, files_dir="integration/partner_files"):
        self.files_dir = files_dir
        os.makedirs(files_dir, exist_ok=True)
    
    def read_partner_file(self, filename: str) -> List[PartnerFileEntry]:
        """Read and parse a partner CSV file"""
        file_path = os.path.join(self.files_dir, filename)
        
        entries = []
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            entries = [
                PartnerFileEntry(
                    transaction_id=row['transaction_id'],
                    partner_id=row['partner_id'],
                    amount=float(row['amount']),
                    status=row['status'],
                    timestamp=row['timestamp']
                )
                for row in reader
            ]
        
        return entries
    
    def create_partner_file(self, partner_id: str, entries: List[PartnerFileEntry]) -> str:
        """Create a new partner file with provided entries"""
        current_date = datetime.utcnow().strftime("%Y%m%d")
        filename = f"{partner_id}_{current_date}_settlement.csv"
        file_path = os.path.join(self.files_dir, filename)
        
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(['transaction_id', 'partner_id', 'amount', 'status', 'timestamp'])
            
            # Write data
            for entry in entries:
                writer.writerow([
                    entry.transaction_id,
                    entry.partner_id,
                    entry.amount,
                    entry.status,
                    entry.timestamp
                ])
        
        return filename

if __name__ == "__main__":
    # Example usage
    processor = PartnerFileProcessor()
    
    # Example entries
    entries = [
        PartnerFileEntry(
            transaction_id="12345",
            partner_id="XYZBANK",
            amount=1000.00,
            status="SUCCESS",
            timestamp="2025-05-12T10:00:00Z"
        ),
        PartnerFileEntry(
            transaction_id="12346",
            partner_id="XYZBANK",
            amount=2500.00,
            status="SUCCESS",
            timestamp="2025-05-12T10:15:00Z"
        )
    ]
    
    # Create a sample file
    filename = processor.create_partner_file("XYZBANK", entries)
    print(f"Created partner file: {filename}")
    
    # Read the file back
    read_entries = processor.read_partner_file(filename)
    print(f"Read {len(read_entries)} entries from file")
