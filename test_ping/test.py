from typing import Dict, Any, List
import json
import yaml
import os
from langchain_ollama import OllamaLLM
from sqlalchemy.orm import Session
from test_ping.database import SessionLocal
from test_ping import models

# -------- Force CPU Mode for Ollama --------
os.environ["OLLAMA_NO_GPU"] = "1"



def load_prompts(filename):
    base_dir = os.path.dirname(__file__)
    yaml_path = os.path.join(base_dir, filename)
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# -------- Create Agents from YAML --------
def make_agents_from_yaml(prompts: Dict[str, Any]) -> Dict[str, OllamaLLM]:
    agents_config = prompts.get("agents", {})
    agents = {}
    for role, cfg in agents_config.items():
        model_name = cfg.get("model", "smollm2:135m")
        system_prompt = cfg.get("system", "")
        agents[role] = OllamaLLM(model=model_name, system=system_prompt)
    return agents


# -------- Dynamic DB Fetcher --------
def fetch_relevant_from_db(requirement_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Dynamically query PingProbe table based on interpreted requirement text.
    """
    session: Session = SessionLocal()
    try:
        query = session.query(models.PingProbe)

        text = requirement_text.lower()

        # --- Simple keyword-based logic ---
        if "confirmed shutdown" in text:
            query = query.filter(models.PingProbe.confirmed_shutdown == True)
        elif "suspected" in text:
            query = query.filter(models.PingProbe.status.ilike("%suspected%"))
        elif "degraded" in text:
            query = query.filter(models.PingProbe.status.ilike("%degraded%"))
        elif "active" in text:
            query = query.filter(models.PingProbe.status.ilike("%active%"))
        else:
            query = query

        results = query.limit(top_k).all()

        # Convert ORM to dict
        output = []
        for r in results:
            output.append({
                "id": r.id,
                "host": r.host,
                "district": getattr(r, "district", None),
                "state": getattr(r, "state", None),
                "packet_loss": getattr(r, "packet_loss", None),
                "signal_strength": getattr(r, "signal_strength", None),
                "signal_quality": getattr(r, "signal_quality", None),
                "confirmed_shutdown": getattr(r, "confirmed_shutdown", None),
                "confirmed_shutdown_time": str(getattr(r, "confirmed_shutdown_time", None)),
                "restored_time": str(getattr(r, "restored_time", None)),
                "status": getattr(r, "status", None),
                "network_type": getattr(r, "network_type", None),
            })
        return output

    finally:
        session.close()


# -------- Core Orchestration --------
def run_orchestration(user_query: str, agents: Dict[str, Any], task_prompts: Dict[str, str]):
    """Multi-agent reasoning pipeline."""
    # Step 1 — Analyst interprets query
    analyst = agents["requirement_analyst"]
    req_prompt = task_prompts["interpret_query"].format(user_query=user_query)
    req_output = analyst.invoke(req_prompt)

    # Step 2 — Database Manager fetches from DB
    db_agent = agents["database_manager"]
    retrieved = fetch_relevant_from_db(req_output, top_k=5)
    retrieved_text = json.dumps(retrieved, indent=2, default=str) or "No matching records found."

    db_prompt = task_prompts["summarize_db"].format(
        analysis=req_output,
        retrieved_data=retrieved_text
    )
    db_summary = db_agent.invoke(db_prompt)

    # Step 3 — Internet Scroller adds context
    scroller = agents["internet_scroller"]
    scroll_prompt = task_prompts["scroll_context"].format(
        user_query=user_query,
        db_summary=db_summary
    )
    scroller_context = scroller.invoke(scroll_prompt)

    # Step 4 — Analyst final synthesis
    final_prompt = task_prompts["final_synthesis"].format(
        user_query=user_query,
        analysis=req_output,
        db_summary=db_summary,
        scroller_context=scroller_context
    )
    final_output = analyst.invoke(final_prompt)

    return {
        "analysis": req_output,
        "db_summary": db_summary,
        "scroller": scroller_context,
        "final": final_output,
        "retrieved": retrieved
    }


# -------- Public Function for FastAPI --------
def analyze_query(user_query: str) -> Dict[str, Any]:
    """
    FastAPI-friendly wrapper that takes a natural language query,
    runs the multi-agent orchestration, and returns the structured output.
    """
    prompts = load_prompts("prompts.yaml")
    agents = make_agents_from_yaml(prompts)
    result = run_orchestration(user_query, agents, prompts["tasks"])
    return result


# -------- Optional: Run standalone for testing --------
if __name__ == "__main__":
    query = " Tell me the only the list of district names where there is confirmed shutdowns happened recently and lasted more than 2 hours nothing else"
    output = analyze_query(query)
    # print(json.dumps(output, indent=2, default=str))
    print(output.get("final") or "No result found.")
