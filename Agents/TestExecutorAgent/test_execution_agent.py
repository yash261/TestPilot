import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import StructuredTool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from Agents.TestExecutorAgent.playwright_executor import PlaywrightExecutor
from Agents.TestExecutorAgent.models import NavigateInput, ClickInput, InputTextInput, PressKeyInput

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
    3. After execution, generate the final Python test automation script containing step definitions for all executed BDD steps.
    4. Ensure the generated code follows the Gherkin structure with step definitions mapped to actual browser automation actions.
    5. Format the output using a structured template so users can directly use the generated code in their test suite.
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
                name="get_dom_texts_func",
                description="""    
                Retrieves the text content of the active page's DOM.
                """
            ),
            StructuredTool.from_function(
                coroutine=self.executor.input_text,
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
                name="press_key",
                description="Simulate a key press on an element identified by a CSS selector",
                args_schema=PressKeyInput
            ),
            StructuredTool.from_function(
                coroutine=self.executor.get_dom_field_func,
                name="get_dom_field_func",
                description="Retrieve all interactive fields from the active page's DOM."
            ),
            StructuredTool.from_function(
                coroutine=self.executor.geturl,
                name="geturl",
                description="Get the current URL of the page"
            ),
        ]
        
        # Change agent type to STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            # memory=self.memory,
            agent_kwargs={
                "system_message": system_prompt
            }
        )

    async def run_tests(self,bdd_script):
        prompt = f"""
        BDD Script 
        ```
        {bdd_script}
        ```
        """
        await self.agent.ainvoke({"input" : prompt})

    async def close(self):
        await self.executor.close()
