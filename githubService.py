import requests
import os
import zipfile
import re
from git import Repo
import shutil

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


def clone_github_repo(github_url,local_path="cloned_repo"):

    # Check if the local path already exists
    if os.path.exists(local_path):
        # If it exists, delete it
        print(f"Deleting existing directory at {local_path}...")
        shutil.rmtree(local_path)
        print("Directory deleted successfully!")

    # Clone the repository
    print(f"Cloning repository from {github_url}...")
    repo = Repo.clone_from(github_url, local_path)
    print("Repository cloned successfully!")

    # Get the last commit (HEAD) and its parent (previous commit)
    last_commit = repo.head.commit
    previous_commit = last_commit.parents[0] if last_commit.parents else None

    # If there's no previous commit (initial commit), compare with empty tree
    if not previous_commit:
        # For initial commit, list all files added
        changed_files = [-1]
    else:
        # Get the diff between the last commit and its parent
        diff = last_commit.diff(previous_commit)
        # Extract changed file paths into a list
        changed_files = [d.a_path for d in diff if d.a_path] + [d.b_path for d in diff if d.b_path and d.b_path != d.a_path]

    # Remove duplicates
    changed_files = list(set(changed_files))
    if len(changed_files) == 0:
        changed_files = [-1]
    # Print the list of changed files
    print("Changed files from the last commit:", changed_files)
    # changed_files = [-1]
    return local_path, changed_files
