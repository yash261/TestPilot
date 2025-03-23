import asyncio
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from tools.ask_knowledge_graph_queries_tool import KnowledgeGraphQueryTool
from tools.get_code_from_knowledge_graph_tool import GetCodeFromNodeIdTool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import hub

load_dotenv()


# Define the prompt template for the ReAct agent
react_prompt = PromptTemplate.from_template("""
You are an assistant helping with codebase analysis. 
You have access to a knowledge graph containing information about the entire codebase.
Think step-by-step about what information you need and how to get it.

TOOLS:
------

Assistant has access to the following tools:

{tools}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```


Question: {input}
{agent_scratchpad}
""")


# Setup the LangChain agent
def create_knowledge_graph_agent(llm):
    tools = [KnowledgeGraphQueryTool,GetCodeFromNodeIdTool]
    agent = create_react_agent(llm, tools, react_prompt)
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    return agent_executor


llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
knowledge_agent = create_knowledge_graph_agent(llm)
response = knowledge_agent.invoke({"input": "Give me code for fetch_graph function"})
