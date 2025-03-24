from typing import TypedDict, Annotated, Sequence
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, AnyMessage
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langgraph.prebuilt import ToolNode, tools_condition
import tools.pdf_context_fetcher_tool as pdf_context
import codegen_agent as code_context
from langgraph.graph.message import add_messages

DATA_PATH = "/Data"
PINECONE_API_KEY = "pcsk_2HnqHd_MuZHH8s6PNsFc2w6cdGJm9xk8jhJt73WMWkEJW2cq996HsdmtrXsJJ1WQUXJh81"
PINECONE_ENV = "us-east-1"
INDEX_NAME = "nn"
PDF_PATH = "PDF_Context_Code/Data/Demo.pdf"

# Define the PDF context tool
def pdf_context_tool(query):
    """Extracts context and scope of the application from its PDF documentation."""
    result = pdf_context.pdf_context_extractor(query)
    return result  # Ensure this matches the expected return type (tuple or JSON)

pdf_context_tool = Tool(
    name="Application_Documentation_Context_Fetcher",
    func=pdf_context_tool,
    description="""
    Extracts context and scope of the application from its PDF documentation based on a query.
    Args:
        query (str): The query to extract context for.
    Returns:
        tuple: A serialized string of the top 5 results and the retrieved documents.
    """
)

# Combine tools into a ToolNode
tools_node = ToolNode([pdf_context_tool])

# Define the state
class GraphState(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    scenario_count: int  # Track the number of scenarios generated

# Define Agent 1 (BDD Generator)
def bdd_generator_agent_node(state: GraphState) -> GraphState:
    messages = state["messages"]
    scenario_count = state.get("scenario_count", 0)

    # Get the initial user input
    input_text = next((m.content for m in messages if isinstance(m, HumanMessage) and "Generate BDD test cases" in m.content), "")

    # Extract previously generated scenarios
    previous_scenarios = [
        m.content for m in messages 
        if isinstance(m, AIMessage) and m.content not in ["Done", "Pass"] and not hasattr(m, "tool_calls")
    ]
    previous_scenarios_text = "\n\n".join(previous_scenarios) if previous_scenarios else "None yet."

    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro-latest",
        google_api_key="AIzaSyDTDqUs6-fFszxnr3rpSbzy50KFXYs6TR0",
        temperature=0.2,
        verbose=True
    ).bind_tools([pdf_context_tool])

    # Define system prompt with stronger tool encouragement
    system_prompt = PromptTemplate(
        input_variables=["input", "tools", "count", "previous_scenarios"],
        template="""You are an assistant that generates functional test cases in BDD format using context from the application's PDF documentation.
        Generate one unique BDD scenario test case at a time for the given input. Do not repeat scenarios already generated.
        Proceed with the next one only when you get "Pass" from the user.
        **You must use the 'Application_Documentation_Context_Fetcher' tool** to fetch relevant context from the PDF documentation for each scenario.
        Pass the input '{input}' as the query to the tool to ensure the scenario is based on the documentation.
        If {count} scenarios have been generated, return "Done".
        
        Input: {input}
        Tools available: {tools}
        Previously generated scenarios:
        {previous_scenarios}
        
        Return only the BDD scenario or "Done" without additional text."""
    )

    # Format the prompt
    formatted_prompt = system_prompt.format(
        input=input_text,
        tools=[t.name for t in [pdf_context_tool]],
        count=10,  # Max scenarios
        previous_scenarios=previous_scenarios_text
    )
    system_message = SystemMessage(content=formatted_prompt)

    # Filter messages to avoid redundant system prompts, but keep history
    filtered_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    response = llm.invoke([system_message] + filtered_messages)

    # Update scenario count if a new scenario is generated
    if response.content != "Done" and response.content != "Pass" and not hasattr(response, "tool_calls"):
        scenario_count += 1

    return {"messages": [response], "scenario_count": scenario_count}

# Define Agent 2 (BDD Executor)
def bdd_executor_agent_node(state: GraphState) -> GraphState:
    bdd_file = state["messages"][-1].content
    print("\nBDD File:", bdd_file)
    return {"messages": [HumanMessage(content="Pass")]}

# Conditional routing from Agent 1
def routing_condition(state: GraphState) -> str:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.content == "Done":
        return "stop"
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tools"
    return "continue"

# Main function
def main():
    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("agent1", bdd_generator_agent_node)
    workflow.add_node("agent2", bdd_executor_agent_node)
    workflow.add_node("tools", tools_node)

    # Add edges
    workflow.add_edge(START, "agent1")
    workflow.add_conditional_edges(
        "agent1",
        routing_condition,
        {"tools": "tools", "continue": "agent2", "stop": END}
    )
    workflow.add_edge("tools", "agent1")
    workflow.add_edge("agent2", "agent1")

    # Compile the graph
    app = workflow.compile()

    # Initial state
    initial_state = {
        "messages": [HumanMessage(content="Generate BDD test cases for the Login functionality of the application.")],
        "scenario_count": 0
    }

    # Run the graph with invoke
    try:
        final_state = app.invoke(initial_state)
        print("\nFinal State Messages:")
        for msg in final_state["messages"]:
            print(msg.content)
    except Exception as e:
        print(f"Error during execution: {e}")

    print("\nWorkflow Complete!")

if __name__ == "__main__":
    print("Running the code\n")
    main()