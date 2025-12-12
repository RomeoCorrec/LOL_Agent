# --- AJOUTEZ CE BLOC EN PREMIER ---
import warnings
# On ignore les messages rouges spécifiques à Windows/Numpy
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", module="numpy")
# ----------------------------------

import os
from dotenv import load_dotenv

# Imports LangChain
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# 1. Le Modèle
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0
)

# 2. Les Outils
tools = [TavilySearchResults(max_results=3)]

# 3. Le Prompt
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Tu es un expert League of Legends. Utilise la recherche pour trouver des infos précises."
    ),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 4. Création de l'agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 5. Exécution
query = "Quels sont les items mythiques supprimés dans League of Legends en 2024 ?"

print(f"--- Recherche : {query} ---")
try:
    response = agent_executor.invoke({"input": query})
    print("\n--- RÉPONSE FINALE ---")
    print(response["output"])
except Exception as e:
    print(f"Erreur : {e}")