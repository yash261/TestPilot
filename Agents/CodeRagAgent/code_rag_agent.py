from langchain.prompts import PromptTemplate
from Agents.CodeRagAgent.tools.get_code_from_knowledge_graph_tool import GetCodeFromNodeIdTool
from Agents.CodeRagAgent.tools.ask_knowledge_graph_queries_tool import KnowledgeGraphQueryTool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_google_genai import ChatGoogleGenerativeAI


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

class CodeRagAgent:

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        self.agent_executor = self.create_knowledge_graph_agent()

    def create_knowledge_graph_agent(self):
        tools = [KnowledgeGraphQueryTool,GetCodeFromNodeIdTool]
        agent = create_react_agent(self.llm, tools, react_prompt)
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )
        return agent_executor

    def run(self, query):
        """Executes the agent with the given query."""
        return self.agent_executor.invoke({"input": query})
    