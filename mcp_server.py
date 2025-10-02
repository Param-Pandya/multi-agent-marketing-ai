"""
mcp_server.py
FastAPI MCP server exposing CSV tables and a simple WebSocket JSON-RPC relay.
Run with: python mcp_server.py
"""

import os
import asyncio
import json
from typing import Dict, Any
import pandas as pd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

DATA_DIR = os.environ.get("MM_DATA_DIR", "./data")

app = FastAPI(title="MCP Server (Prototype)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# load tables at startup
TABLES: Dict[str, pd.DataFrame] = {}
for fname in os.listdir(DATA_DIR) if os.path.isdir(DATA_DIR) else []:
    if fname.endswith(".csv"):
        key = fname[:-4]
        TABLES[key] = pd.read_csv(os.path.join(DATA_DIR, fname))

@app.get("/tables")
def list_tables():
    return {"tables": list(TABLES.keys())}

@app.post("/query")
def query_table(payload: Dict[str, Any]):
    table = payload.get("table")
    filters = payload.get("filters", {})
    if table not in TABLES:
        raise HTTPException(status_code=404, detail="Table not found")
    df = TABLES[table]
    # apply simple equality filters
    for k, v in filters.items():
        if k in df.columns:
            df = df[df[k] == v]
    # return records
    return {"count": len(df), "records": df.to_dict(orient="records")}

# Simple WebSocket relay for JSON-RPC messages: broadcast to all connected clients
clients = set()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            data = await ws.receive_text()
            # naive broadcast
            for c in clients.copy():
                try:
                    await c.send_text(data)
                except Exception:
                    pass
    except WebSocketDisconnect:
        clients.remove(ws)

if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host="127.0.0.1", port=8000, reload=False)
