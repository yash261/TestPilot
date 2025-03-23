from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
# import google.generativeai as genai
from langchain_core.prompts import ChatPromptTemplate
import Pinecone

system_message = """
    You are a test case generator pro capable of generating functional test cases in BDD format based on user queries by extracting the context of the product documentation PDF. Use the context only from the tools provided. Do not use context from other sources.
"""


# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key="AIzaSyDTDqUs6-fFszxnr3rpSbzy50KFXYs6TR0",
)


primary_agent_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            system_message
        ),
        ("human", "{messages}"),
    ])

llm_main = primary_agent_prompt | llm

pdf_context_tool = Tool(
    name="Application Context Fetcher",
    func=Pinecone.pinecone_data_tool,
    description="""
        This tool is used to extract the conext of the functionality of the and scope of the application.
        Returns:
            json: A Json containing the top 5 results for context.
    """
)

agent = initialize_agent(
    tools=[pdf_context_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True
)

def main():
    
    # Interactive loop
    print("Ask me anything! (Type 'quit' to exit)")
    while True:
        user_input = input("> ")
        if user_input.lower() == 'quit':
            break
            
        response = agent.invoke(user_input)
        print(response.get("output"))
        # print(f"Agent: {response}\n")

if __name__ == "__main__":
    main()
    # Pinecone.insert_records("Data/Demo.pdf")