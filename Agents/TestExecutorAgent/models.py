from typing import Literal
from pydantic import BaseModel, Field

class NavigateInput(BaseModel):
    url: str = Field(..., description="The URL to navigate to. Value must include the protocol (http:// or https://).")
    timeout: int = Field(5, description="Additional time in seconds to wait after the initial load before considering the navigation successful. Default is 5 seconds.")

class ClickInput(BaseModel):
    selector: str = Field(..., description="The CSS selector of the element to click")

class InputTextInput(BaseModel):
    query_selector: str = Field(..., description="The CSS selector of the input field")
    text: str = Field(..., description="The text to be entered")

class PressKeyInput(BaseModel):
    selector: str = Field(..., description="The CSS selector of the element")
    key: str = Field(..., description="The key to be pressed (e.g., 'Enter', 'Tab')")

class TestResultInput(BaseModel):
    """Input model for the test result reporting tool."""
    output: str = Field(
        default="", 
        description="""
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
        """
    )