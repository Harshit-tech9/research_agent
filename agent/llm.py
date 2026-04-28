import os 
from groq import Groq 
from api_keys import groq_api_key

client = Groq(api_key=groq_api_key)  

print(client)

def call_llm(prompt): 
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[{"role":"user", "content":prompt}], 
        temperature=0.2
    ) 

    return response.choices[0].message.content

