
import asyncio
from Agents.TestExecutorAgent.test_execution_agent import AITestAutomationAgent

async def main():
    
    bdd_script = """

Feature: Login Functionality

  Scenario: Successful login with valid credentials
    Given I am on the login page at http://localhost:3000/
    And I enter 'user' into the username field
    And I enter 'pass' into the password field
    When I click the 'Login' button
    Then I should be redirected to the dashboard page at http://localhost:3000/dashboard
    """

    agent=AITestAutomationAgent()
    graph = await agent.create_graph()
    async for event in graph.astream(
            {"messages": [{"role": "user", "content": bdd_script}]},
            stream_mode="values"
    ):
        if event and "messages" in event:
            event["messages"][-1].pretty_print()

if __name__ == "__main__":
    asyncio.run(main())