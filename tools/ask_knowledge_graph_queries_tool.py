import json
from langchain.agents import AgentType, AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate
from typing import Dict, List, Optional, Union, Annotated
from langchain.tools import tool
from pydantic import BaseModel, Field

class KnowledgeGraphQuery(BaseModel):
    queries: List[str] = Field(..., description="List of natural language questions to ask about the codebase")
    node_ids: Optional[List[str]] = Field(None, description="Optional list of node IDs to query")

@tool
def KnowledgeGraphQueryTool(input_str: str) -> List[Dict]:
    """
    Query the code knowledge graph using natural language questions.
    The knowledge graph contains information about every function, class, and file in the codebase.
    This tool allows asking multiple questions about the codebase in a single operation.
    Use this tool when you need to ask multiple related questions about the codebase at once.
    Do not use this to query code directly.
    
    The input should be a JSON string with the following format:
    {"queries": ["question1", "question2"], "node_ids": ["id1", "id2"]}

    "node_ids" is an optional field
    """
    from service import InferenceService

    input_data = json.loads(input_str) if isinstance(input_str, str) else input_str
    if isinstance(input_data, dict):
        queries = input_data.get("queries", [])
        if isinstance(queries, str):
            queries = [queries]  # Handle case where queries is a string
        node_ids = input_data.get("node_ids")
    else:
        # Fallback for unexpected input
        queries = [str(input_data)]
        node_ids = None
    
    results = []
    for query in queries:
        query_request = create_query_request(query, node_ids)
        result = InferenceService().query_vector_index(query_request.query, query_request.node_ids)
        results.append(result)
    return results

def create_query_request(query: str, node_ids: Optional[List[str]]):
    """Create a query request object with the necessary structure"""
    class QueryRequest:
        def __init__(self, query, node_ids):
            self.query = query
            self.node_ids = node_ids
    
    return QueryRequest(query, node_ids)