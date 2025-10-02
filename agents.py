"""
agents.py
Defines three agents and memory stores.
Agents can be called via JSON-RPC style dicts (no network required).
"""

import json
from datetime import datetime
from typing import Dict, Any, List

# Memory implementations
class ShortTermMemory:
    def __init__(self):
        self.contexts = {}

    def set_context(self, lead_id, ctx: Dict[str,Any]):
        self.contexts[lead_id] = ctx

    def get_context(self, lead_id):
        return self.contexts.get(lead_id, {})

class LongTermMemory:
    def __init__(self):
        self.profiles = {}

    def upsert_profile(self, lead_id, profile: Dict[str,Any]):
        if lead_id in self.profiles:
            self.profiles[lead_id].update(profile)
        else:
            self.profiles[lead_id] = profile.copy()

    def get_profile(self, lead_id):
        return self.profiles.get(lead_id, {})

class EpisodicMemory:
    def __init__(self):
        self.episodes = []

    def add_episode(self, episode: Dict[str,Any]):
        self.episodes.append(episode)

    def recent(self, n=10) -> List[Dict[str,Any]]:
        return self.episodes[-n:]

class SemanticMemory:
    def __init__(self):
        self.triples = []
        self.adj = {}

    def load_triples(self, rows: List[Dict[str,Any]], head='head', rel='relation', tail='tail'):
        for r in rows:
            h = str(r.get(head, ""))
            relv = str(r.get(rel, ""))
            t = str(r.get(tail, ""))
            self.triples.append((h, relv, t))
            self.adj.setdefault(h, []).append((relv, t))

    def neighbors(self, head):
        return self.adj.get(head, [])

# Base Agent
class Agent:
    def __init__(self, name, mcp):
        self.name = name
        self.mcp = mcp
        self.stm = ShortTermMemory()
        self.ltm = LongTermMemory()
        self.epm = EpisodicMemory()
        self.sm = SemanticMemory()
        self.log = []

    def handle(self, request: Dict[str,Any]):
        method = request.get('method')
        params = request.get('params', {})
        handler = getattr(self, f"rpc_{method}", None)
        if handler is None:
            return {"error": f"method {method} not implemented"}
        result = handler(**params)
        self.epm.add_episode({"agent": self.name, "method": method, "params": params, "result": result, "time": datetime.now().isoformat()})
        return result

# Lead Triage Agent
class LeadTriageAgent(Agent):
    def rpc_classify_lead(self, lead_id=None):
        # query leads table
        df = self.mcp.query("leads")
        # df is pandas DataFrame if using MCPLocal; if network mode, it may be list of dicts
        # handle both cases
        row = None
        if hasattr(df, "iterrows"):
            # pandas
            # find lead id column heuristically
            lid_col = None
            for c in df.columns:
                if 'lead' in c.lower() and 'id' in c.lower():
                    lid_col = c; break
            if lid_col is None:
                lid_col = df.columns[0]
            sel = df[df[lid_col] == lead_id]
            if not sel.empty:
                row = sel.iloc[0].to_dict()
        else:
            # assume list of dicts
            for r in df:
                if r.get("lead_id") == lead_id or r.get("id") == lead_id:
                    row = r; break

        if row is None:
            return {"error": "lead not found"}

        score = 0
        if row.get("campaign_id"):
            score += 40
        if row.get("engagement_score"):
            try:
                score += int(row.get("engagement_score"))
            except:
                pass
        if row.get("email") and "@" in str(row.get("email")):
            score += 10

        if score >= 60:
            label = "Campaign Qualified"
        elif score >= 30:
            label = "General Inquiry"
        else:
            label = "Cold Lead"

        profile = {"lead_id": lead_id, "label": label, "score": score, "last_classified": datetime.now().isoformat()}
        self.ltm.upsert_profile(lead_id, profile)
        self.stm.set_context(lead_id, {"last_label": label, "last_score": score})
        self.log.append({"action": "classify", "lead_id": lead_id, "label": label, "score": score})
        return profile

# Engagement Agent
class EngagementAgent(Agent):
    def rpc_prepare_outreach(self, lead_id=None):
        profile = self.ltm.get_profile(lead_id)
        ctx = self.stm.get_context(lead_id)
        neighbors = self.sm.neighbors("email_marketing")
        hint = neighbors[0][1] if neighbors else "Product Intro"
        message = f"Hi! Personalized note about {hint}. (lead {lead_id})"
        action = {"lead_id": lead_id, "message": message, "channel": "email", "planned_at": datetime.now().isoformat()}
        self.log.append({"action": "prepare", "lead_id": lead_id})
        return action

    def rpc_send_outreach(self, lead_id=None, message=None):
        # simulated send
        result = {"lead_id": lead_id, "status": "sent", "time": datetime.now().isoformat()}
        self.stm.set_context(lead_id, {"last_message": message, "last_sent": datetime.now().isoformat()})
        self.epm.add_episode({"event":"sent","lead_id": lead_id, "message": message, "time": datetime.now().isoformat()})
        self.log.append({"action": "send", "lead_id": lead_id})
        return result

# Campaign Optimization Agent
class CampaignOptimizationAgent(Agent):
    def rpc_evaluate_campaigns(self, top_n: int = 3):
        df = self.mcp.query("campaign_daily")
        # compute simple conv_rate if possible
        if hasattr(df, "columns") and "impressions" in df.columns and "conversions" in df.columns:
            dfc = df.copy()
            dfc["conv_rate"] = dfc["conversions"] / dfc["impressions"].replace({0: None})
            top = dfc.groupby("campaign_id").agg({"conv_rate":"mean"}).reset_index().sort_values("conv_rate", ascending=False).head(top_n)
            recs = top.to_dict(orient="records")
        else:
            # fallback: return unique campaign ids
            if hasattr(df, "to_dict"):
                recs = [{"campaign_id": r.get("campaign_id")} for r in df.to_dict(orient="records")][:top_n]
            else:
                recs = df[:top_n] if isinstance(df, list) else []
        self.log.append({"action":"evaluate","top": recs})
        return {"top_campaigns": recs}
