from llm import call_llm 

PLANNER_PROMPT = """
You are a planning agent. 
Break the user query into step-by-step tasks. 
Return ONLY steps like: 
1. ... 
2. ...
3. ...
"""

def create_plan(query): 
    prompt = PLANNER_PROMPT + f"\nUSER Query: {query}" 
    return call_llm(prompt)