import json
import os

def report_test_result(output: str) -> str:
    """
    Report the final test execution result.
    
    Args:
        status (str): Test execution status ('pass' or 'fail')
        message (str, optional): Detailed explanation of the result
        code (str, optional): Generated Python test automation script
    
    Returns:
        str: Confirmation of result reporting
    """

    try:
        json_code=json.loads(output)   
        status = json_code.get('status', 'Unknown')
        message = json_code.get('message', '')
        scenario = json_code.get('scenario', 'Unnamed_Scenario')

        print(f"------------------Test Execution Result----------------------")
        print(f"Status: {status}")
        print(f"Message: {message}")
        
        # Create a directory to store test result JSON files if it doesn't exist
        os.makedirs("test_results", exist_ok=True)

        # Generate a unique filename based on timestamp
        scenario = scenario.strip().replace(" ", "_")
        filename = f"test_results/{scenario}.json"

        # Save the result data to a JSON file
        with open(filename, "w") as f:
            json.dump(json_code, f, indent=4)
        print(f"Test result saved to: {filename}")
    except Exception as e:
        return f"Got error while saving the data {e}"
