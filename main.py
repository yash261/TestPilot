import asyncio
from neo4j import GraphDatabase
from service import InferenceService
from githubService import download_github_repo
from utils import visualize_graph
import sys
import argparse

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process a GitHub repo or local directory for inference.')
    parser.add_argument('--github-url', type=str, help='URL of the GitHub repository')
    parser.add_argument('--repo-dir', type=str, help='Path to local repository directory')
    
    # Parse arguments
    args = parser.parse_args()

    # Initialize variables
    repo_dir = None
    changed_files = []

    # Check which argument was provided
    if args.github_url:
        repo_dir, changed_files = download_github_repo(args.github_url)
    elif args.repo_dir:
        repo_dir = args.repo_dir
    else:
        parser.error("Please provide either --github-url or --repo-dir")
        return

    # Run the inference service
    service = InferenceService()
    service.project_setup(repo_dir,True)
    asyncio.run(service.run_inference())

if __name__ == "__main__":
    main()
