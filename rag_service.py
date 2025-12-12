from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.tavily_search import TavilySearchResults
from structures import *

class RagService():
    def __init__(self, qdrant_client, patch_collection, encoder, llm_model):
        self.client = qdrant_client
        self.encoder = encoder
        self.patch_collection = patch_collection

        self.llm = llm_model
        @tool
        def search_patch_notes(query: str):
            """Utilise cet outil pour trouver des changements techniques précis sur les champions, 
            les objets ou les sorts dans les patch notes officiels (buffs, nerfs, ajustements)."""
            
            # (Ta logique Qdrant existante)
            vector = self.encoder.encode(query).tolist()
            results = self.client.query_points(
                collection_name=self.patch_collection,
                query=vector,
                limit=10,
                with_payload=True
            )
            
            # On formate le résultat pour l'Agent
            context = ""
            for point in results.points:
                payload = point.payload
                context += f"- Patch {payload.get('patch')}: {payload.get('raw_text')}\n"
            
            return context if context else "Aucune info trouvée dans les patch notes."
        
        # @tool
        # def search_web_data(query: str):
        #     """Utilise cet outil pour connaître la 'Meta' actuelle, les taux de victoire (winrates),
        #     les Tier Lists (God Tier, Tier S), ou les builds populaires sur U.gg/Lolalytics."""
        #     search = DuckDuckGoSearchRun()
        #     # On force la recherche sur des sites fiables de LoL
        #     targeted_query = f"{query} site:u.gg OR site:lolalytics.com OR site:op.gg OR site:deeplol.gg"
        #     return search.run(targeted_query)

        self.tavily = TavilySearchResults(
            max_results=3,
            include_domains=[
                "op.gg",            # Très bon pour les stats KR
                "deeplol.gg"
            ],
            exclude_domains=[
                "tftactics.gg", 
                "metatft.com",
                "tft.op.gg", 
                "tactics.tools"
            ])


        self.tools = [search_patch_notes, self.tavily]
        
        # Le Prompt Système qui guide le cerveau de l'Agent
# 3. LE CERVEAU DE L'AGENT (PROMPT SYSTEM AVANCÉ)
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un analyste expert et coach de League of Legends.
            
            TA MÉTHODOLOGIE OBLIGATOIRE :
            1. Pour la META : Utilise TOUJOURS 'tavily_search_results_json' pour avoir les données réelles (Winrate, Tier S, Tier A).
            2. Pour la TECHNIQUE : Utilise 'search_patch_notes'.
            
            RÈGLES CRITIQUES ANTI-HALLUCINATION :
            - NE LISTE JAMAIS de champions au hasard. Si l'outil Web ne te donne pas de noms précis, dis : "Je n'arrive pas à accéder aux données de la meta pour l'instant."
            - NE CITE QUE les champions explicitement mentionnés dans les résultats de recherche.
            - MÉFIE-TOI DES STATS DE NICHE : Si un champion a un winrate énorme (>53%) mais qu'il est un Support ou un Tank bizarre au Mid (ex: Taric, Malphite), IGNORE-LE. Concentre-toi sur les champions "Meta" standards (Mages, Assassins).
             Un Champion "méta" est un champion qui a un bon winrate ET un gros pick rate.           
            FORMAT DE RÉPONSE :
            - Donne une liste courte (Top 3-5 champions).
            - Explique POURQUOI ils sont forts (grâce aux patch notes si possible).
            - Réponds en Français."""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        # Construction de l'agent
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    def get_answer(self, user_question: str):
        # Lancement de l'agent
        response = self.agent_executor.invoke({"input": user_question})
        return response["output"], []



