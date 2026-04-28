def calculator(expression): 
    try: 
        return str(eval(expression)) 
    except Exception as e:
        return  f"Error: {str(e)}"