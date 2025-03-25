import requests
import os
import zipfile

import re
import os

def detect_and_fetch_repo(path: str):
    """
    Checks if the given path is a GitHub repository URL or a local directory.
    
    Args:
        path (str): The input path or URL.
    
    Returns:
        str: "github" if it's a GitHub link, "local" if it's a local path, "invalid" otherwise.
    """
    github_pattern = r"^(https?:\/\/)?(www\.)?github\.com\/[\w-]+\/[\w-]+(\.git)?(\/.*)?$"
    
    if re.match(github_pattern, path):
        return download_github_repo(path)
    elif os.path.exists(path) and os.path.isdir(path):
        return path,None
    else:
        return "Invalid path",None


def download_github_repo(repo_url, previous_commit=None,destination_folder=None):
    try:
        # Extract owner and repo name from URL
        # Expected format: https://github.com/owner/repo
        parts = repo_url.rstrip('/').split('/')
        if len(parts) < 5 or parts[2] != 'github.com':
            raise ValueError("Invalid GitHub repository URL")
        
        owner = parts[3]
        repo = parts[4]
        
        # Set default destination folder if not provided
        if destination_folder is None:
            destination_folder = os.getcwd()
        
        # Create download directory if it doesn't exist
        os.makedirs(destination_folder, exist_ok=True)
        
        # GitHub API URL for downloading the repo as zip
        api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
        
        # Send request to GitHub
        headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get(api_url, headers=headers, stream=True)
        
        # Check if request was successful
        if response.status_code != 200:
            raise Exception(f"Failed to download repository. Status code: {response.status_code}")
        
        # Temporary zip file path
        zip_path = os.path.join(destination_folder, f"{repo}.zip")
        
        # Download the zip file
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Extract the contents
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract all contents to destination folder
            zip_ref.extractall(destination_folder)
        
        # Clean up: remove the zip file
        os.remove(zip_path)
        
        print(f"Successfully downloaded and extracted {repo} to {destination_folder}")
        
        # Return the path to the extracted folder
        # GitHub adds a version hash to the folder name, so we need to find it
        extracted_folder = [f for f in os.listdir(destination_folder) 
                          if f.startswith(f"{owner}-{repo}")][0]
        
        repo_path = os.path.join(destination_folder, extracted_folder)
        # Get changed files
        changed_files = []
        
        if previous_commit:
            
            # Get the latest commit SHA
            commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            commits_response = requests.get(commits_url, headers=headers)
            if commits_response.status_code == 200:
                latest_commit = commits_response.json()[0]['sha']
                
                # Get commit comparison
                compare_url = f"https://api.github.com/repos/{owner}/{repo}/compare/{previous_commit}...{latest_commit}"
                compare_response = requests.get(compare_url, headers=headers)
                
                if compare_response.status_code == 200:
                    compare_data = compare_response.json()
                    changed_files = [file['filename'] for file in compare_data['files']]
        
        return repo_path, changed_files
       
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
