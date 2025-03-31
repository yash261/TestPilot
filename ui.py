import streamlit as st
import time
import threading
import os
from GithubService.githubService import detect_and_fetch_repo
import asyncio
from Agents.TestExecutorAgent.test_execution_agent import AITestAutomationAgent
import aiohttp



# Global list to store updates (thread-safe)
updates_list = []

def process_file(file_path):
    """Function to process each file."""
    print(f"Processing file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

import subprocess

def execute_js_script(script_path, **kwargs):
    """
    Executes a JavaScript script using Node.js and passes arguments in '--key=value' format.

    Args:
        script_path (str): Path to the JavaScript file.
        **kwargs: Key-value pairs of parameters to pass as arguments.

    Returns:
        str: Output from the script (expected to be a file path).
    """
    try:
        # Convert kwargs to command-line argument format (--key=value)
        args = [f"--{key}={value}" for key, value in kwargs.items()]

        # Build the command
        command = ["node", script_path] + args

        # Execute the script and capture output
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

        # Return the output (expected to be a file path)
        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        print(f"Error executing script: {e.stderr}")
        return None

async def run_test(bdd_script):
    """Function to make an API call with the BDD script."""
    global updates_list
    
    # Define the API endpoint (replace with your actual endpoint)
    api_url = "http://127.0.0.1:5000/run-test"  # Replace with your API URL
    
    # Prepare the payload (e.g., sending the BDD script as JSON)
    payload = {
        "script": bdd_script,
    }
    try:
        # Make the asynchronous API call
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()  # Assuming the API returns JSON
                    scenario = result.get("scenario", "Unknown Scenario")
                    status = result.get("status", "").lower()
                    message = result.get("message", "").lower()
                    if status == "pass":
                        updates_list.append(f"✅ {scenario}: Passed")
                    else:
                        updates_list.append(f"❌ {scenario}: Failed")
                    updates_list.append(f"message: {message}")

                else:
                    updates_list.append(f"❌ API call failed with status {response.status}")
    except Exception as e:
        updates_list.append(f"❌ Error during connect to test executor service call: {str(e)}")

def execute_tests(directory_path,design_path,additional_message):
    global updates_list
    directory_path = os.path.join(directory_path, "frontend", "src", "components")

    async def run_all_tests():
        updates_list.append(f"Generating bdd...")
        tests_folder_path=execute_js_script("bdd_generator/generate-bdd.js", components=directory_path,design=design_path,additional_info=additional_message)
        time.sleep(7)
        tests_folder_path="C:\\Users\\YASH\\Desktop\\Hackathon\\knowledgegraph\\tests\\features"
        print(f"tests_folder_path {tests_folder_path}")
        for root, _, files in os.walk(tests_folder_path):
            for file in files:
                if "signup" in str(file):
                    continue
                file_path = os.path.join(root, file)
                bdd = process_file(file_path)
                updates_list.append(f"📄 Running... {file}")

                await run_test(bdd)

                st.session_state["update_flag"] = not st.session_state.get("update_flag", False)  # UI refresh

    # Ensure Playwright runs in the main thread
    asyncio.run(run_all_tests())  

# Streamlit UI
st.set_page_config(page_title="Testing System", layout="centered")
st.title("🚀 Context-Aware Testing System")

# Repository Link or Local Path Input
st.markdown("### 🔗 Enter Repository Link or Local Path")
repo_path = st.text_input("Enter repo link or local path", help="Provide the repository link or local directory path to process.")

# File Path Input Box (Replaces File Upload)
st.markdown("### 📂 Enter File Path (Optional)")
file_path = st.text_input("Enter file path", help="Provide a local file path if required.")

# Radio buttons
st.markdown("### 🔘 Select an Option")
option = st.radio("Choose an option:", ("Functional Testing", "Unit Testing"))

# Additional Information
st.markdown("### ✏️ Additional Information")
additional_info = st.text_area("Enter any extra details", height=150, help="Provide any additional details related to your input.")

# Initialize session state
if "updates" not in st.session_state:
    st.session_state["updates"] = []
if "update_flag" not in st.session_state:
    st.session_state["update_flag"] = False  # Used to trigger UI refresh

# Execute button
st.markdown("### 🚀 Start Execution")
if st.button("Execute", help="Click to start processing."):
    updates_list.clear()  # Reset updates
    repo_result = detect_and_fetch_repo(repo_path)
    
    if repo_result[0] == "Invalid path":
        st.error("Invalid repository path! Please enter a valid GitHub link or local path.")
    else:
        repo_dir = repo_result[0]
        thread = threading.Thread(target=execute_tests, daemon=True, args=(repo_dir,file_path,additional_info))
        thread.start()
        st.success("Processing started! Updates will appear below.")

# Display updates dynamically
st.markdown("### 📢 Live Updates")
placeholder = st.empty()

while True:
    st.session_state["updates"] = updates_list.copy()  # Sync global list with session state
    with placeholder.container():
        for update in st.session_state["updates"]:
            st.write(update)
    time.sleep(1)
