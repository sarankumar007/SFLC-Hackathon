from typing import Dict, Any
import json
import yaml
import os
from langchain_ollama import OllamaLLM

# -------- Force CPU Mode for Ollama --------
os.environ["OLLAMA_NO_GPU"] = "1"


# -------- YAML Loader --------
def load_prompts(yaml_path: str = "prompts.yaml") -> Dict[str, Any]:
    """Load agents and task prompts from YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {
        "agents": data.get("agents", {}),
        "tasks": data.get("tasks", {})
    }


# -------- Create Agents from YAML --------
def make_agents_from_yaml(prompts: Dict[str, Any]) -> Dict[str, OllamaLLM]:
    agents_config = prompts.get("agents", {})
    agents = {}
    for role, cfg in agents_config.items():
        model_name = cfg.get("model", "smollm:1.7b")
        system_prompt = cfg.get("system", "")
        agents[role] = OllamaLLM(model=model_name, system=system_prompt)
    return agents


# -------- Simple Keyword-Based Data Retriever --------
def retrieve_relevant(query: str, mock_db_str: str, top_k: int = 3):
    """Naive keyword-based retriever that scans mock DB JSON and returns matching reports."""
    try:
        data = json.loads(mock_db_str)
        reports = data.get("reports", [])
    except Exception:
        reports = []

    query_lower = query.lower()
    matched = []
    for r in reports:
        text = json.dumps(r).lower()
        if any(word in text for word in query_lower.split()):
            matched.append(r)
        if len(matched) >= top_k:
            break

    if not matched:
        matched = reports[:top_k]

    results = [{"text": json.dumps(r), "metadata": r} for r in matched]
    return results


# -------- Main Orchestration Logic --------
def run_orchestration(user_query: str, mock_db_str: str, agents: Dict[str, Any], task_prompts: Dict[str, str]):
    """
    Requirement Analyst: interprets query and defines what to look for
    Database Manager: retrieves relevant data
    Internet Scroller: provides external-like context
    Requirement Analyst again: synthesizes everything into the final report
    """

    # Step 1: Analyst interprets query
    analyst = agents["requirement_analyst"]
    req_prompt = task_prompts["interpret_query"].format(user_query=user_query)
    req_output = analyst.invoke(req_prompt)

    # Step 2: Database Manager retrieves and summarizes relevant data
    db_agent = agents["database_manager"]
    retrieved = retrieve_relevant(req_output, mock_db_str, top_k=5)
    retrieved_text = "\n".join([f"- {r['text']}" for r in retrieved]) or "No matching records found."
    db_prompt = task_prompts["summarize_db"].format(analysis=req_output, retrieved_data=retrieved_text)
    db_summary = db_agent.invoke(db_prompt)

    # Step 3: Internet Scroller simulates social/public context
    scroller = agents["internet_scroller"]
    scroll_prompt = task_prompts["scroll_context"].format(user_query=user_query, db_summary=db_summary)
    scroller_context = scroller.invoke(scroll_prompt)

    # Step 4: Analyst synthesizes everything into final report
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


# -------- Main Entry Point --------
if __name__ == "__main__":
    # Step 1: Load prompts
    prompts = load_prompts("prompts.yaml")

    # Step 2: Mock database
    mock_db_str = json.dumps({
        "reports": [
            {
                "id": 1,
                "host": "bsnl.co.in",
                "probe_time": "2025-10-31T10:30:00",
                "packets_sent": 10,
                "packets_received": 2,
                "packet_loss": 80.0,
                "rtt_min_ms": 120.5,
                "rtt_max_ms": 450.3,
                "rtt_avg_ms": 300.2,
                "confirmed_shutdown": True,
                "confirmed_shutdown_time": "2025-10-31T10:45:00+05:30",
                "restored_time": "2025-10-31T14:30:00+05:30",
                "signal_strength": 1,
                "signal_quality": "POOR",
                "network_type": "4G",
                "status": "Degraded",
                "district": "Jaipur",
                "state": "Rajasthan",
                "latitude": 26.9124,
                "longitude": 75.7873
            },
            {
                "id": 2,
                "host": "airtel.in",
                "probe_time": "2025-10-28T18:15:00",
                "packets_sent": 10,
                "packets_received": 0,
                "packet_loss": 100.0,
                "rtt_min_ms": None,
                "rtt_max_ms": None,
                "rtt_avg_ms": None,
                "confirmed_shutdown": True,
                "confirmed_shutdown_time": "2025-10-28T18:20:00+05:30",
                "restored_time": "2025-10-29T12:00:00+05:30",
                "signal_strength": 0,
                "signal_quality": "NONE",
                "network_type": "5G",
                "status": "Shutdown",
                "district": "Imphal",
                "state": "Manipur",
                "latitude": 24.8170,
                "longitude": 93.9368
            },
            {
                "id": 3,
                "host": "jio.com",
                "probe_time": "2025-11-01T09:20:00",
                "packets_sent": 10,
                "packets_received": 8,
                "packet_loss": 20.0,
                "rtt_min_ms": 90.4,
                "rtt_max_ms": 200.1,
                "rtt_avg_ms": 150.6,
                "confirmed_shutdown": False,
                "signal_strength": 4,
                "signal_quality": "GOOD",
                "network_type": "5G",
                "status": "Active",
                "district": "Bangalore Urban",
                "state": "Karnataka",
                "latitude": 12.9716,
                "longitude": 77.5946
            }
        ]
    })

    # Step 3: Define user query
    user_query = "Show me all regions where confirmed shutdowns happened recently and lasted more than 2 hours."

    # Step 4: Initialize agents
    agents = make_agents_from_yaml(prompts)

    # Step 5: Run orchestration
    print("\n🧠 Running Smart Internet Shutdown Multi-Agent System (3 Agents)...\n")
    result = run_orchestration(user_query, mock_db_str, agents, prompts["tasks"])

    # Step 6: Display structured output
    print("=== 🧩 Requirement Analyst (Interpretation) ===")
    print(result["analysis"], "\n")

    print("=== 🗃️ Database Summary ===")
    print(result["db_summary"], "\n")

    print("=== 🌐 Internet Scroller Context ===")
    print(result["scroller"], "\n")

    print("=== 🧭 Final Integrated Insight (from Analyst) ===")
    print(result["final"], "\n")

    print("=== 📑 Retrieved Records ===")
    for r in result["retrieved"]:
        meta = r["metadata"]
        print(f"- {meta.get('state', 'Unknown')}, {meta.get('district', 'Unknown')} | "
              f"Status: {meta.get('status', '')}, Loss: {meta.get('packet_loss', '')}%")
