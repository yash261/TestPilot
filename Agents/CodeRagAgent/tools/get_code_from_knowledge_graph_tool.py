import asyncio
import logging
import re
from typing import Any, Dict
from langchain.tools import tool
from langchain_core.tools import StructuredTool
from neo4j import GraphDatabase
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from Agents.CodeRagAgent.service import InferenceService

class GetCodeFromNodeIdInput(BaseModel):
    project_id: str = Field(description="The repository ID, this is a UUID")
    node_id: str = Field(description="The node ID, this is a UUID")


@tool
def GetCodeFromNodeIdTool(node_id: str,project_id: str="default") -> Dict[str, Any]:
    """Retrieves code and docstring for a specific node in a repository.
        The input should be a string which is the id of node to retrieve code for.
        Returns dictionary containing node code, docstring, and file location details.
    """
    node_id = re.sub(r'^\s*`?|`\s*$|\s+', '', node_id)
    node_data = _get_node_data(project_id, node_id)
    return _process_result(node_data, node_id)

def _get_node_data(project_id: str, node_id: str) -> Dict[str, Any]:
    query = """
    MATCH (n:NODE {node_id: $node_id, repoId: $project_id})
    RETURN n.file_path AS file_path, n.start_line AS start_line, n.end_line AS end_line, n.text as code, n.docstring as docstring
    """
    with InferenceService().driver.session() as session:
        result = session.run(query, node_id=node_id, project_id=project_id)
        return result.single()

def _process_result(
    node_data: Dict[str, Any], node_id: str
) -> Dict[str, Any]:
    file_path = node_data["file_path"]
    start_line = node_data["start_line"]
    end_line = node_data["end_line"]
    relative_file_path = _get_relative_file_path(file_path)
    code_content = node_data.get("code", None)

    docstring = None
    if node_data.get("docstring", None):
        docstring = node_data["docstring"]

    return {
        "node_id": node_id,
        "file_path": relative_file_path,
        "start_line": start_line,
        "end_line": end_line,
        "code_content": code_content,
        "docstring": docstring,
    }

def _get_relative_file_path(file_path: str) -> str:
    parts = file_path.split("/")
    try:
        projects_index = parts.index("projects")
        return "/".join(parts[projects_index + 2 :])
    except ValueError:
        print(f"'projects' not found in file path: {file_path}")
        return file_path

