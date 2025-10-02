"""
mcp_local.py
Lightweight MCP-like interface for local use (no network).
Loads CSVs from ./data and exposes query functions.
"""

import os
import pandas as pd
from typing import Dict, Any

DATA_DIR = os.environ.get("MM_DATA_DIR", "./data")  # set to path where you unzipped CSVs

class MCPLocal:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir
        self.tables = {}
        self._load_tables()

    def _load_tables(self):
        if not os.path.isdir(self.data_dir):
            raise FileNotFoundError(f"Data dir not found: {self.data_dir}")
        for fname in os.listdir(self.data_dir):
            if fname.endswith(".csv"):
                name = fname[:-4]
                path = os.path.join(self.data_dir, fname)
                try:
                    self.tables[name] = pd.read_csv(path)
                except Exception as e:
                    print(f"Warning: failed to read {path}: {e}")

    def list_tables(self):
        return list(self.tables.keys())

    def query(self, table: str, filters: Dict[str, Any] = None):
        if table not in self.tables:
            raise KeyError(f"table {table} not found")
        df = self.tables[table].copy()
        if filters:
            for k, v in filters.items():
                if k in df.columns:
                    df = df[df[k] == v]
        return df

# quick self-test
if __name__ == "__main__":
    m = MCPLocal()
    print("Loaded tables:", m.list_tables())
    if "leads" in m.list_tables():
        print("leads sample:")
        print(m.query("leads").head().to_dict(orient="records"))
