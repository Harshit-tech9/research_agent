class Memory: 
    def __init__(self): 
        self.history = [] 

    def add(self, content): 
        self.history.append(content) 

    def get_context(self): 
        return "\n".join(self.history)