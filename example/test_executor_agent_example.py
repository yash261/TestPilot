
import asyncio
from Agents.TestExecutorAgent.test_execution_agent import AITestAutomationAgent


async def main():
    bdd_script = """
    Scenario: Login with invalid credentials
        Given I navigate to "https://market.koinpr.com/sign-in"
        When I enter "test123@gmail.com" in the email field
        And I enter "12345678" in the password field
        And I click the Sign In button
        Then I should see an error message "Invalid email or password"
    """
    agent = AITestAutomationAgent(bdd_script)
    await agent.run_tests()
    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())