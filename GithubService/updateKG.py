import asyncio
from Agents.CodeRagAgent.service import InferenceService
from dotenv import load_dotenv
import asyncio
from GithubService.githubService import clone_github_repo
import argparse
load_dotenv()

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process a GitHub repo or local directory for inference.')
    parser.add_argument('--github-url', type=str, help='URL of the GitHub repository')
    parser.add_argument('--repo-dir', type=str, help='Path to local repository directory')
    
    # Parse arguments
    args = parser.parse_args()

    # Initialize variables
    repo_dir = None
    changed_files = [-1]

    # Check which argument was provided
    if args.github_url:
        repo_dir, changed_files = clone_github_repo(args.github_url)
    elif args.repo_dir:
        repo_dir = args.repo_dir
    else:
        parser.error("Please provide either --github-url or --repo-dir")
        return
    
    
    clean_up = True
    # Run the inference service
    service = InferenceService()
    service.project_updates(repo_dir,changed_files,clean_up)
    if clean_up:
        asyncio.run(service.run_inference())

if __name__ == "__main__":
    main()


    
