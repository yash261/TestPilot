import asyncio
from neo4j import GraphDatabase
from service import InferenceService


repo_dir="C:\\Users\\YASH\\Desktop\\Freelancing\\loanmanagementsystem\\backend"

service=InferenceService()
service.project_setup(repo_dir)
asyncio.run(service.run_inference())
