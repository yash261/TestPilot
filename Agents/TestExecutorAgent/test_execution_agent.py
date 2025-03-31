import asyncio
from functools import wraps
import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import StructuredTool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from Agents.TestExecutorAgent.playwright_executor import PlaywrightExecutor
from Agents.TestExecutorAgent.models import NavigateInput, ClickInput, InputTextInput, PressKeyInput, TestResultInput
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import MessagesState
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import MessagesState

from Agents.TestExecutorAgent.utils import report_test_result


load_dotenv()


system_prompt = """
    <agent_role>
    You are an AI-powered test automation agent designed to execute Behavior-Driven Development (BDD) scripts using browser automation tools. 
    Your primary responsibility is to interpret BDD scenarios and steps, convert them into executable actions, and interact with web applications to validate expected behaviors.
    </agent_role>

    <bdd_parsing>
    1. Carefully analyze each BDD scenario and its steps to understand the intended test flow
    2. Break down complex Gherkin statements (Given/When/Then) into actionable browser operations
    3. Map natural language instructions to specific tool calls
    4. Maintain context between steps to ensure proper test execution
    5. Identify test data embedded within BDD steps and use it for interactions
    </bdd_parsing>

    <execution_strategy>
    1. Execute each BDD step sequentially, mapping to appropriate tool actions
    2. For "Given" steps: perform setup actions like navigation and initial state configuration
    3. For "When" steps: execute user interactions like clicking, text entry, or form submission
    4. For "Then" steps: verify expectations by checking DOM content or page state
    5. If a step fails, retry up to 2 times with alternative selectors or approaches
    6. Maintain session state between steps to ensure proper test continuity
    6. Before interacting with any element, first call get_dom_field_func to obtain valid selectors.
    7. If an element cannot be found, re-fetch the DOM and try using alternative attributes (aria-label, name, placeholder).
    8. Never assume element selectors—verify all selections against extracted DOM data.
    </execution_strategy>   

    <selector_intelligence>
    1. Always extract actual selectors from the DOM, never invent them
    2. Use smart element selection strategies to find the most appropriate elements
    3. Use text content, aria labels, and other attributes to identify elements when IDs aren't available
    4. Always extract actual selectors from the DOM, never invent them
    5. Always validate selectors against extracted DOM elements before performing actions.
    6. If an element is not found, attempt to retrieve new selectors.

    </selector_intelligence>

    <tool_usage>
    1. Navigate to pages using open_url_tool
    2. Identify page elements using get_dom_field_func and get_dom_text_func
    3. Interact with elements using click_tool and enter_text_tool
    4. Use press_key_combination_tool for keyboard shortcuts and form submissions
    5. Extract information using DOM inspection tools to validate expectations
    6. Use only the provided tools to accomplish tasks - find creative solutions if direct tools aren't available
    </tool_usage>

    <output_reporting>
    1. Report the execution status of the BDD script (Pass/Fail).
    2. Provide clear explanations for any failed steps, including possible reasons and debugging suggestions.
    3. After execution, generate the final A JSON-stringified object representing the test execution flow, containing step definitions for executed steps.
    4. Format the output using a structured template so users can directly use the generated json in their test suite.
    </output_reporting>
"""

class AITestAutomationAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2, google_api_key=os.environ["GOOGLE_API_KEY"])
        self.memory = ConversationBufferMemory(memory_key="history", return_messages=True)
        self.executor = PlaywrightExecutor()

        # Create structured tools
        self.tools = [
            StructuredTool.from_function(
                coroutine=self.executor.navigate,
                func=lambda url, timeout=5: self.sync_wrapper(self.executor.navigate(url, timeout)),
                name="navigate",
                description="""
                Opens a specified URL in the active browser instance. Waits for an initial load event, then waits for either
                the 'domcontentloaded' event or a configurable timeout, whichever comes first.
                
                Parameters:
                - url: The URL to navigate to.
                - timeout: Additional time in seconds to wait after the initial load before considering the navigation successful.
                
                """,
                args_schema=NavigateInput
            ),
            StructuredTool.from_function(
                coroutine=self.executor.click,
                func=lambda selector: self.sync_wrapper(self.executor.click(selector)),
                name="click",
                description="""            
                Executes a click action on the element matching the given query selector string within the currently open web page.
                
                Parameters:
                - selector: The query selector string to identify the element for the click action
                
                Returns:
                - A message indicating success or failure of the click action 
                """,
                args_schema=ClickInput
            ),
            StructuredTool.from_function(
                coroutine=self.executor.get_dom_texts_func,
                func=lambda: self.sync_wrapper(self.executor.get_dom_texts_func()),
                name="get_dom_texts_func",
                description="""    
                Retrieves the text content of the active page's DOM.
                """
            ),
            StructuredTool.from_function(
                coroutine=self.executor.input_text,
                func=lambda query_selector, text: self.sync_wrapper(self.executor.input_text(query_selector, text)),
                name="input_text",
                description=
                """
                Enters text into a DOM element identified by a CSS selector.

                This function enters the specified text into a DOM element identified by the given CSS selector.
                It uses the Playwright library to interact with the browser and perform the text entry operation.
                The function supports both direct setting of the 'value' property and simulating keyboard typing.

                Args:
                    'query_selector' (DOM selector query using mmid attribute)
                    'text' (text to enter on the element).

                Returns:
                    str: Explanation of the outcome of this operation.

                Note:
                    - The 'query_selector' should be a valid CSS selector that uniquely identifies the target element.
                    - The 'text' parameter specifies the text to be entered into the element.
                    - The function uses the PlaywrightManager to manage the browser instance.
                    - If no active page is found, an error message is returned.
                    - The function internally calls the 'do_entertext' function to perform the text entry operation.
                    - The 'do_entertext' function applies a pulsating border effect to the target element during the operation.
                    - The 'use_keyboard_fill' parameter in 'do_entertext' determines whether to simulate keyboard typing or not.
                    - If 'use_keyboard_fill' is set to True, the function uses the 'page.keyboard.type' method to enter the text.
                    - If 'use_keyboard_fill' is set to False, the function uses the 'custom_fill_element' method to enter the text.
                """,
                args_schema=InputTextInput
            ),
            StructuredTool.from_function(
                coroutine=self.executor.press_key,
                func=lambda selector, key: self.sync_wrapper(self.executor.press_key(selector, key)),
                name="press_key",
                description="Simulate a key press on an element identified by a CSS selector",
                args_schema=PressKeyInput
            ),
            StructuredTool.from_function(
                coroutine=self.executor.get_dom_field_func,
                func=lambda: self.sync_wrapper(self.executor.get_dom_field_func()),
                name="get_dom_field_func",
                description="Retrieve all interactive fields from the active page's DOM."
            ),
            StructuredTool.from_function(
                coroutine=self.executor.geturl,
                func=lambda: self.sync_wrapper(self.executor.geturl()),
                name="geturl",
                description="Get the current URL of the page"
            ),
            StructuredTool.from_function(
                func=lambda output: self.sync_wrapper(self.close_and_report(output)),
                coroutine=self.close_and_report,
                name="report_test_result",
                description="""
                A tool to report the final test execution result.
                
                Parameters:
                - output: A JSON-stringified object representing the test execution flow with the following structure:
                    {
                    "scenario": "User Login",
                    "message": "Optional detailed explanation of the result",
                    "status": "Overall test execution status ('pass' or 'fail')"
                    "steps": [
                        {
                        "action": "navigate",
                        "params": {
                            "url": "https://example.com/login"
                        }
                        },
                        {
                        "action": "input_text",
                        "params": {
                            "selector": "#username",
                            "text": "testuser"
                        }
                        },
                        {
                        "action": "click",
                        "params": {
                            "selector": "#login-button"
                        }
                        }
                    ]
                    }
                
                This tool helps in:
                1. Logging test execution results
                2. Storing generated test scripts
                3. Providing a summary of the test run
                """,
                args_schema=TestResultInput
            )
        ]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    async def close_and_report(self,output):
        await self.executor.close()
        report_test_result(output)

    def sync_wrapper(self,async_func):
        """
        Wrapper to run async functions synchronously with proper event loop handling
        """
        @wraps(async_func)
        def wrapper(*args, **kwargs):
            time.sleep(1)
            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # If no event loop exists, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            try:
                # Run the async function synchronously
                return loop.run_until_complete(async_func(*args, **kwargs))
            except Exception as e:
                print(f"Error in async function execution: {e}")
                raise
        return wrapper


    def assistant(self,state: MessagesState):
        return {"messages": [self.llm_with_tools.invoke([SystemMessage(content=system_prompt)] + state["messages"])]}
    
    async def create_graph(self):

        time.sleep(1)

        # Graph
        builder = StateGraph(MessagesState)

        # Define nodes: these do the work
        builder.add_node("assistant", self.assistant)
        builder.add_node("tools", ToolNode(self.tools))

        # Define edges: these determine the control flow
        builder.add_edge(START, "assistant")
        builder.add_conditional_edges(
            "assistant",
            tools_condition,
        )
        builder.add_edge("tools", "assistant")
        graph = builder.compile()
        return graph
        
    async def close(self):
        await self.executor.close()
