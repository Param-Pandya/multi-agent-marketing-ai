"""
demo_runner.py
Run a local end-to-end demonstration: classify leads, prepare/send outreach, evaluate campaigns.
Usage:
    python demo_runner.py
Ensure CSVs are placed in ./data (or set env var MM_DATA_DIR to folder path).
"""

import os
import json
from mcp_local import MCPLocal
from agents import LeadTriageAgent, EngagementAgent, CampaignOptimizationAgent
from datetime import datetime

OUT_LOG = "./run_log.json"

def main():
    data_dir = os.environ.get("MM_DATA_DIR", "./data")
    print("Using data dir:", data_dir)
    mcp = MCPLocal(data_dir)
    print("Available tables:", mcp.list_tables())

    # instantiate agents
    triage = LeadTriageAgent("LeadTriage", mcp)
    engage = EngagementAgent("Engagement", mcp)
    opt = CampaignOptimizationAgent("CampaignOpt", mcp)

    # load semantic triples into agents' semantic memory if available
    if "semantic_kg_triples" in mcp.list_tables():
        sm_rows = mcp.query("semantic_kg_triples").to_dict(orient="records")
        for a in (triage, engage, opt):
            a.sm.load_triples(sm_rows)

    # choose up to 5 sample leads
    leads_df = mcp.query("leads")
    if leads_df is None or len(leads_df) == 0:
        print("No leads table or it's empty.")
        return

    # find lead id column
    lid_col = None
    for c in leads_df.columns:
        if 'lead' in c.lower() and 'id' in c.lower():
            lid_col = c; break
    if lid_col is None:
        lid_col = leads_df.columns[0]

    sample_leads = leads_df[lid_col].dropna().unique().tolist()[:5]
    print("Sample leads:", sample_leads)

    actions = []
    for lid in sample_leads:
        # classify
        req = {"method": "classify_lead", "params": {"lead_id": lid}}
        res1 = triage.handle(req)
        actions.append({"agent":"triage","lead":lid,"result":res1})

        # prepare outreach
        req2 = {"method":"prepare_outreach","params": {"lead_id": lid}}
        plan = engage.handle(req2)
        actions.append({"agent":"engagement","lead":lid,"plan":plan})

        # send outreach
        req3 = {"method":"send_outreach","params": {"lead_id": lid, "message": plan["message"]}}
        sent = engage.handle(req3)
        actions.append({"agent":"engagement","lead":lid,"sent":sent})

    # evaluate campaigns
    req4 = {"method":"evaluate_campaigns","params":{"top_n":3}}
    eval_res = opt.handle(req4)
    actions.append({"agent":"campaign_opt","result":eval_res})

    # save log
    out = {"time": datetime.now().isoformat(), "actions": actions}
    with open(OUT_LOG, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"Demo complete. Log saved to {OUT_LOG}")

if __name__ == "__main__":
    main()
