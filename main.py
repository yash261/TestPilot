import asyncio
from neo4j import GraphDatabase
from service import InferenceService


repo_dir="potpie\\app\\modules\\parsing\\knowledge_graph"

service=InferenceService()
service.project_setup(repo_dir)
asyncio.run(service.run_inference())
