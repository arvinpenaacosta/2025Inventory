
from langchain_ollama import OllamaLLM
from warnings import filterwarnings
# Suppress specific deprecation warning
filterwarnings("ignore", category=DeprecationWarning)
# Create Ollama LLM instance
llm = OllamaLLM(model="llama3.2:3b")
# Invoke the model
response = llm.invoke("How many legs squid has")
print(response)






