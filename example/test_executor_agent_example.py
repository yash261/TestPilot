
import asyncio
from Agents.TestExecutorAgent.test_execution_agent import AITestAutomationAgent


async def main():
    bdd_script = """
    Feature: Dashboard
  Scenario: Failed money transfer due to missing amount
    Given I am on the login page at http://192.168.0.103:3000/
    And I enter 'user' into the username field
    And I enter 'pass' into the password field
    And I click the 'Login' button
    And I am on the Dashboard page at http://192.168.0.103:3000/dashboard
    When I click on the user dropdown
    And I select "abc" user from the dropdown
    And I click the 'Transfer' button
    Then I should see an error message indicating the transfer failed
    """
    agent = AITestAutomationAgent()
    await agent.run_tests(bdd_script)
    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())