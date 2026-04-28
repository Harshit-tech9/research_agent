from llm import call_llm 
from tavily_tool import tavily_search   
from calculator_tool import calculator 

SYSTEM_PROMPT = """
You are an AI agent that can reason and use tools. 

Available tools: 
- tavily_search[query] 
- calculator[expression]

Follow this format: 
Thought: what to do 
Action: tool[input]
Observation: result
... repeat ...

Final Answer: result
"""  

def execute_agent(query, memory): 
    for step in range(5): 
        prompt = SYSTEM_PROMPT + "\n\n" 
        prompt += memory.get_context()
        prompt += f"\nUSER: {query} \n"  

        response = call_llm(prompt) 
        print("\n Agent: \n", response) 

        memory.add(response) 

        if "Action:" in response: 
            action_line = response.split("Action:")[1].strip() 

            if "tavily_search" in action_line: 
                q = action_line.split("[")[1].split("]")[0] 
                result = tavily_search(q)  

            elif "calculator" in action_line:
                expr = action_line.split("[")[1].split("]")[0] 
                result = calculator(expr) 
            
            else: 
                result = "Unknown tool" 

            observation = f"Observation: {result}" 
            print("\n Tool Result: \n", observation) 

            memory.add(observation)  

        if "Final Answer:" in response: 
            break


