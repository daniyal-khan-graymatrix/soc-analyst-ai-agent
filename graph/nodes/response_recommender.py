import os
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()

# Setup LangChain LLM
llm = ChatOpenAI(model="gpt-4.1", temperature=0.3, api_key=os.getenv("OPENAI_API_KEY"))

# Define prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a cybersecurity response advisor. Based on each incident, generate actionable and SOC-relevant mitigation steps with concise threat-specific justifications."),
    ("user", """
Below is a list of security incident reports. For these incidents:

1. Provide up to 5 recommended actions (bullet points, concise)
2. Provide a **one-sentence justification** for these actions, focused on threat pattern, severity, and context (like IP reputation, rate of access, OWASP mapping, etc.)

Return JSON:
{{
  "recommended_actions": [...],
  "why_these_recommendations": "Short explanation: threat pattern, evidence, and impact."
}}

Incidents:
{incidents}
    """)
])


def response_recommender_agent(state):
    """
    ResponseRecommenderAgent (LLM-Based per-incident): Uses GPT-4.1 to generate
    tailored response playbooks for each incident individually.

    Output:
    - Each incident in 'incident_reports' will contain unique recommended actions and explanation.
    """
    reports = state.get("logs", [])

    if not reports:
        state["recommended_actions"] = []
        state["why_these_recommendations"] = "No incident reports available."
        return state

    if not state.get("rbac_passed", True):
        state["recommended_actions"] = []
        state["why_these_recommendations"] = "Access denied due to insufficient RBAC permissions."
        return state

    chain = prompt | llm
    all_actions = []
    reasoning_pool = []

    for incident in reports:
        try:
            response = chain.invoke({"incidents": json.dumps([incident])})
            content = response.content.strip()

            if content.startswith("```json"):
                content = content[7:].strip()
            if content.endswith("```"):
                content = content[:-3].strip()

            parsed = json.loads(content)

            actions = parsed.get("recommended_actions", [])
            reasoning = parsed.get("why_these_recommendations", "No reasoning provided.")

            if reasoning.startswith("Short explanation: "):
                reasoning = reasoning[19:].strip()

            incident["recommended_actions"] = actions
            incident["why_these_recommendations"] = reasoning

            all_actions.extend(actions)
            reasoning_pool.append(reasoning)

        except Exception as e:
            print(f"[LLM Response Recommender] Error for {incident.get('incident_id')}: {e}")
            fallback_actions = ["Escalate to human analyst", "Log and review in audit"]
            fallback_reason = "Fallback recommendation: LLM analysis failed."

            incident["recommended_actions"] = fallback_actions
            incident["why_these_recommendations"] = fallback_reason
            all_actions.extend(fallback_actions)
            reasoning_pool.append(fallback_reason)

    # Save the incidents recommendations in the report
    state["logs"] = reports

    return state
