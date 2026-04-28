import requests 
from api_keys import tavily_api_key

TAVILY_API_KEY = tavily_api_key 

def tavily_search(query): 
    url="https://api.tavily.com/search" 

    payload = {
        "api_key" : TAVILY_API_KEY, 
        "query" : query, 
        "search_depth" : "advanced", 
        "include_answer": True
    } 

    response = requests.post(url, json=payload) 
    data = response.json() 

    if "answer" in data: 
        return data["answer"] 
    
    return str(data)