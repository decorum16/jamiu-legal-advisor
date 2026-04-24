#!/usr/bin/env python
import os
from dotenv import load_dotenv
from sqlalchemy import inspect, create_engine, text

# Load environment variables
load_dotenv()

database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/jamiu')
engine = create_engine(database_url)

# Check if table exists
inspector = inspect(engine)
tables = inspector.get_table_names()

if 'legal_case_chunks' not in tables:
    print("❌ Table 'legal_case_chunks' does not exist")
else:
    print("✅ Table 'legal_case_chunks' exists")
    
    columns = inspector.get_columns('legal_case_chunks')
    print("\nColumns:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
    
    # Check if embedding column exists
    col_names = [col['name'] for col in columns]
    if 'embedding' in col_names:
        print("\n✅ 'embedding' column EXISTS")
    else:
        print("\n❌ 'embedding' column MISSING")
