import os
import json
import asyncio
import time
from typing import List, Dict
from Agents.TestExecutorAgent.test_execution_agent import AITestAutomationAgent, PlaywrightExecutor

class TestSuiteExecutor:

    async def execute_test_from_json(self, json_file_path: str) -> Dict[str, any]:
        """
        Execute test steps from a JSON file using Playwright executor.

        Args:
            json_file_path (str): Path to the JSON file containing test steps

        Returns:
            Dict containing execution results with scenario, status, and message
        """
        try:
            # Read the JSON file
            with open(json_file_path, 'r') as file:
                test_data = json.load(file)

            # Validate test data structure
            if 'steps' not in test_data:
                raise ValueError("Invalid test JSON: Missing 'steps' key")

            # Initialize results with default values
            results = {
                "scenario": test_data.get("scenario", "Unnamed Scenario"),
                "status": "pass",
                "message": "Test completed successfully"
            }

            
            self.executor= PlaywrightExecutor(False)
            await self.executor.initialize_playwright()

            # Execute each step
            for step in test_data['steps']:
                step_result = await self.execute_single_step(step)
                
                # If any step fails, update results
                if step_result['status'] == 'fail':
                    results['status'] = 'fail'
                    results['message'] = step_result['message']
                    break

            await self.executor.close()

            return results

        except Exception as e:
            return {
                "scenario": test_data.get("scenario", "Unnamed Scenario") if 'test_data' in locals() else "Unknown",
                "status": "error",
                "message": str(e)
            }
        finally:
            # Ensure browser is closed
            await self.executor.close()

    async def execute_single_step(self, step: Dict[str, any]) -> Dict[str, str]:
        """
        Execute a single test step based on its action.

        Args:
            step (Dict): A step from the test JSON

        Returns:
            Dict with execution status and message
        """
        try:
            action = step.get('action')
            params = step.get('params', {})

            # Map actions to executor methods
            action_map = {
                'navigate': self.executor.navigate,
                'click': self.executor.click,
                'input_text': self.executor.input_text,
                'press_key': self.executor.press_key,
                'geturl': self.executor.geturl,
            }

            # Select the appropriate method
            if action not in action_map:
                return {
                    "status": "fail",
                    "message": f"Unsupported action: {action}"
                }

            # Extract parameters based on action
            if action == 'navigate':
                result = await action_map[action](params.get('url'))
            elif action == 'click':
                result = await action_map[action](params.get('selector'))
            elif action == 'input_text':
                result = await action_map[action](
                    params.get('selector'), 
                    params.get('text')
                )
            elif action == 'press_key':
                result = await action_map[action](
                    params.get('selector'), 
                    params.get('key')
                )
            elif action == 'geturl':
                result = await action_map[action]()

            # Check if the result indicates an error
            if result.startswith('ERROR:'):
                return {
                    "status": "fail",
                    "message": result
                }

            return {
                "status": "pass",
                "message": result
            }

        except Exception as e:
            return {
                "status": "fail",
                "message": f"Error executing step {action} with params: {params}: {str(e)}"
            }

    async def run_all_tests_in_directory(self, directory: str = "test_results"):
        """
        Run all test JSON files in a specified directory.

        Args:
            directory (str): Path to the directory containing test JSON files

        Returns:
            List of test results
        """
        # Ensure directory exists
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist.")
            return []

        # Get all JSON files in the directory
        json_files = [
            os.path.join(directory, f) 
            for f in os.listdir(directory) 
            if f.endswith('.json')
        ]

        # Execute tests sequentially
        overall_results = []
        for json_file in json_files:
            print(f"Executing test from: {json_file}")
            test_result = await self.execute_test_from_json(json_file)
            overall_results.append(test_result)
            print(f"Test Result: {test_result['status']}")

        return overall_results

# Async main function for demonstration
async def main():
    executor = TestSuiteExecutor()
    
    try:
        # Option 1: Execute a single test JSON
        # single_test_result = await executor.execute_test_from_json('test_results/some_test.json')
        # print(single_test_result)
        
        # Option 2: Run all tests in the test_results directory
        results = await executor.run_all_tests_in_directory()
        
        # Print detailed results
        for result in results:
            print(f"Scenario: {result['scenario']}")
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            print("---")

    except Exception as e:
        print(f"Error running tests: {e}")

# Run the tests if script is executed directly
if __name__ == "__main__":
    asyncio.run(main())