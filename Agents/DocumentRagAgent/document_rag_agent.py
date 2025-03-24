from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from Agents.DocumentRagAgent.PineconeService import PineconeService

system_message = """
    You are a test case generator pro capable of generating functional test cases in BDD format based on user queries by extracting the context of the product documentation PDF. Use the context only from the tools provided. Do not use context from other sources.
"""

class DocumentRagAgent:
    def __init__(self, path=None):
        self.pinecone = PineconeService()
        if(path is not None):
            self.pinecone.insert_records(path)
        self.primary_agent_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_message
                ),
                ("human", "{messages}"),
            ]
        )
        self.llm = self.primary_agent_prompt | ChatGoogleGenerativeAI(model="gemini-2.0-flash")

        pdf_context_tool = Tool(
            name="Application Context Fetcher",
            func=self.pinecone.pinecone_data_tool,
            description="""
                This tool is used to extract the conext of the functionality of the and scope of the application.
                Returns:
                    json: A Json containing the top 5 results for context.
            """
        )

        self.agent_executor = initialize_agent(
            tools=[pdf_context_tool],
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
            handle_parsing_errors=True
        )
    
    def run(self, query):
        return self.agent_executor.invoke({"input": query})
