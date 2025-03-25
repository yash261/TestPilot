import asyncio
import logging
import os
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from neo4j import GraphDatabase
from pydantic import BaseModel
import tiktoken
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
import instructor
from Agents.CodeRagAgent.graph import RepoMap
from Agents.CodeRagAgent.utils import SimpleTokenCounter, SimpleIO, visualize_graph, generate_node_id
import networkx as nx
from grep_ast import filename_to_lang


load_dotenv()

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

logger = logging.getLogger(__name__)

class DocstringRequest(BaseModel):
    node_id: str
    text: str

class DocstringNode(BaseModel):
    node_id: str
    docstring: str
    tags: Optional[List[str]] = []


class DocstringResponse(BaseModel):
    docstrings: List[DocstringNode]


class InferenceService:
    
    def __init__(self):
        neo4j_auth = (os.environ["neo4j_username"], os.environ["neo4j_password"])
        self.driver=GraphDatabase.driver(os.environ["neo4j_uri"], auth=neo4j_auth)
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.environ["GOOGLE_API_KEY"])
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        self.parallel_requests = int(os.getenv("PARALLEL_REQUESTS", 50))

    def close(self):
        self.driver.close()


    def log_graph_stats(self, repo_id="default"):
        query = """
        MATCH (n:NODE {repoId: $repo_id})
        OPTIONAL MATCH (n)-[r]-(m:NODE {repoId: $repo_id})
        RETURN
        COUNT(DISTINCT n) AS nodeCount,
        COUNT(DISTINCT r) AS relationshipCount
        """

        try:
            # Establish connection
            with self.driver.session() as session:
                # Execute the query
                result = session.run(query, repo_id=repo_id)
                record = result.single()

                if record:
                    node_count = record["nodeCount"]
                    relationship_count = record["relationshipCount"]

                    # Log the results
                    print(
                        f"DEBUGNEO4J: Repo ID: {repo_id}, Nodes: {node_count}, Relationships: {relationship_count}"
                    )
                else:
                    print(
                        f"DEBUGNEO4J: No data found for repository ID: {repo_id}"
                    )

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")

    def num_tokens_from_string(self, string: str, model: str = "gpt-4") -> int:
        """Returns the number of tokens in a text string."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(string, disallowed_special=set()))

    def fetch_graph(self, repo_id: str) -> List[Dict]:
        batch_size = 500
        all_nodes = []
        with self.driver.session() as session:
            offset = 0
            while True:
                result = session.run(
                    "MATCH (n:NODE {repoId: $repo_id}) "
                    "RETURN n.node_id AS node_id, n.text AS text, n.file_path AS file_path, n.start_line AS start_line, n.end_line AS end_line, n.name AS name "
                    "SKIP $offset LIMIT $limit",
                    repo_id=repo_id,
                    offset=offset,
                    limit=batch_size,
                )
                batch = [dict(record) for record in result]
                if not batch:
                    break
                all_nodes.extend(batch)
                offset += batch_size
        print(f"DEBUGNEO4J: Fetched {len(all_nodes)} nodes for repo {repo_id}")
        return all_nodes

    def get_entry_points(self, repo_id: str) -> List[str]:
        batch_size = 400  # Define the batch size
        all_entry_points = []
        with self.driver.session() as session:
            offset = 0
            while True:
                result = session.run(
                    f"""
                    MATCH (f:FUNCTION)
                    WHERE f.repoId = '{repo_id}'
                    AND NOT ()-[:CALLS]->(f)
                    AND (f)-[:CALLS]->()
                    RETURN f.node_id as node_id
                    SKIP $offset LIMIT $limit
                    """,
                    offset=offset,
                    limit=batch_size,
                )
                batch = result.data()
                if not batch:
                    break
                all_entry_points.extend([record["node_id"] for record in batch])
                offset += batch_size
        return all_entry_points

    def get_neighbours(self, node_id: str, repo_id: str):
        with self.driver.session() as session:
            batch_size = 400  # Define the batch size
            all_nodes_info = []
            offset = 0
            while True:
                result = session.run(
                    """
                    MATCH (start {node_id: $node_id, repoId: $repo_id})
                    OPTIONAL MATCH (start)-[:CALLS]->(direct_neighbour)
                    OPTIONAL MATCH (start)-[:CALLS]->()-[:CALLS*0..]->(indirect_neighbour)
                    WITH start, COLLECT(DISTINCT direct_neighbour) + COLLECT(DISTINCT indirect_neighbour) AS all_neighbours
                    UNWIND all_neighbours AS neighbour
                    WITH start, neighbour
                    WHERE neighbour IS NOT NULL AND neighbour <> start
                    RETURN DISTINCT neighbour.node_id AS node_id, neighbour.name AS function_name, labels(neighbour) AS labels
                    SKIP $offset LIMIT $limit
                    """,
                    node_id=node_id,
                    repo_id=repo_id,
                    offset=offset,
                    limit=batch_size,
                )
                batch = result.data()
                if not batch:
                    break
                all_nodes_info.extend(
                    [
                        record["node_id"]
                        for record in batch
                        if "FUNCTION" in record["labels"]
                    ]
                )
                offset += batch_size
            return all_nodes_info

    def batch_nodes(
        self, nodes: List[Dict], max_tokens: int = 16000, model: str = "gpt-4"
    ) -> List[List[DocstringRequest]]:
        batches = []
        current_batch = []
        current_tokens = 0
        node_dict = {node["node_id"]: node for node in nodes}

        def replace_referenced_text(
            text: str, node_dict: Dict[str, Dict[str, str]]
        ) -> str:
            pattern = r"Code replaced for brevity\. See node_id ([a-f0-9]+)"
            regex = re.compile(pattern)

            def replace_match(match):
                node_id = match.group(1)
                if node_id in node_dict:
                    return "\n" + node_dict[node_id]["text"].split("\n", 1)[-1]
                return match.group(0)

            previous_text = None
            current_text = text

            while previous_text != current_text:
                previous_text = current_text
                current_text = regex.sub(replace_match, current_text)
            return current_text

        for node in nodes:
            if not node.get("text"):
                logger.warning(f"Node {node['node_id']} has no text. Skipping...")
                continue

            updated_text = replace_referenced_text(node["text"], node_dict)
            node_tokens = self.num_tokens_from_string(updated_text, model)

            if node_tokens > max_tokens:
                logger.warning(
                    f"Node {node['node_id']} - {node_tokens} tokens, has exceeded the max_tokens limit. Skipping..."
                )
                continue

            if current_tokens + node_tokens > max_tokens:
                if current_batch:  # Only append if there are items
                    batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(
                DocstringRequest(node_id=node["node_id"], text=updated_text)
            )
            current_tokens += node_tokens

        if current_batch:
            batches.append(current_batch)

        total_nodes = sum(len(batch) for batch in batches)
        print(f"Batched {total_nodes} nodes into {len(batches)} batches")
        print(f"Batch sizes: {[len(batch) for batch in batches]}")

        return batches

    def batch_entry_points(
        self,
        entry_points_neighbors: Dict[str, List[str]],
        docstring_lookup: Dict[str, str],
        max_tokens: int = 16000,
        model: str = "gpt-4",
    ) -> List[List[Dict[str, str]]]:
        batches = []
        current_batch = []
        current_tokens = 0

        for entry_point, neighbors in entry_points_neighbors.items():
            entry_docstring = docstring_lookup.get(entry_point, "")
            neighbor_docstrings = [
                f"{neighbor}: {docstring_lookup.get(neighbor, '')}"
                for neighbor in neighbors
            ]
            flow_description = "\n".join(neighbor_docstrings)

            entry_point_data = {
                "node_id": entry_point,
                "entry_docstring": entry_docstring,
                "flow_description": entry_docstring + "\n" + flow_description,
            }

            entry_point_tokens = self.num_tokens_from_string(
                entry_docstring + flow_description, model
            )

            if entry_point_tokens > max_tokens:
                continue  # Skip entry points that exceed the max_tokens limit

            if current_tokens + entry_point_tokens > max_tokens:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(entry_point_data)
            current_tokens += entry_point_tokens

        if current_batch:
            batches.append(current_batch)

        return batches

    async def generate_docstrings(self, repo_id: str="default") -> Dict[str, DocstringResponse]:
        print(
            f"DEBUGNEO4J: Function: {self.generate_docstrings.__name__}, Repo ID: {repo_id}"
        )
        self.log_graph_stats(repo_id)
        nodes = self.fetch_graph(repo_id)
        print(
            f"DEBUGNEO4J: After fetch graph, Repo ID: {repo_id}, Nodes: {len(nodes)}"
        )
        self.log_graph_stats(repo_id)
        print(
            f"Creating search indices for project {repo_id} with nodes count {len(nodes)}"
        )

        # print(
        #     f"nodes_to_index {nodes}"
        # )
        
        batches = self.batch_nodes(nodes)
        all_docstrings = {"docstrings": []}

        semaphore = asyncio.Semaphore(self.parallel_requests)

        async def process_batch(batch, batch_index: int):
            async with semaphore:
                print(f"Processing batch {batch_index} for project {repo_id}")
                response = await self.generate_response(batch, repo_id)
                if not isinstance(response, DocstringResponse):
                    logger.warning(
                        f"Parsing project {repo_id}: Invalid response from LLM. Not an instance of DocstringResponse. Retrying..."
                    )
                    response = await self.generate_response(batch, repo_id)
                else:
                    self.update_neo4j_with_docstrings(repo_id, response)
                return response

        tasks = [process_batch(batch, i) for i, batch in enumerate(batches)]
        results = await asyncio.gather(*tasks)

        for result in results:
            if not isinstance(result, DocstringResponse):
                logger.error(
                    f"Project {repo_id}: Invalid response from during inference. Manually verify the project completion."
                )

        updated_docstrings = all_docstrings
        return updated_docstrings
    
    async def generate_docstrings_updates(self, updated_nodes,repo_id: str="default") -> Dict[str, DocstringResponse]:
        
        if not updated_nodes:
            return {}
        
        batches = self.batch_nodes(updated_nodes)
        all_docstrings = {"docstrings": []}

        semaphore = asyncio.Semaphore(self.parallel_requests)

        async def process_batch(batch, batch_index: int):
            async with semaphore:
                print(f"Processing batch {batch_index} for project {repo_id}")
                response = await self.generate_response(batch, repo_id)
                if not isinstance(response, DocstringResponse):
                    logger.warning(
                        f"Parsing project {repo_id}: Invalid response from LLM. Not an instance of DocstringResponse. Retrying..."
                    )
                    response = await self.generate_response(batch, repo_id)
                else:
                    self.update_neo4j_with_docstrings(repo_id, response)
                return response

        tasks = [process_batch(batch, i) for i, batch in enumerate(batches)]
        results = await asyncio.gather(*tasks)

        for result in results:
            if not isinstance(result, DocstringResponse):
                logger.error(
                    f"Project {repo_id}: Invalid response from during inference. Manually verify the project completion."
                )

        updated_docstrings = all_docstrings
        return updated_docstrings

    async def generate_response(
        self,
        batch: List[DocstringRequest],
        repo_id: str = "default"
    ) -> DocstringResponse:
        base_prompt = """
        You are a senior software engineer with expertise in code analysis and documentation. Your task is to generate concise docstrings for each code snippet and tagging it based on its purpose. Approach this task methodically, following these steps:

        1. **Node Identification**:
        - Carefully parse the provided `code_snippets` to identify each `node_id` and its corresponding code block.
        - Ensure that every `node_id` present in the `code_snippets` is accounted for and processed individually.

        2. **For Each Node**:
        Perform the following tasks for every identified `node_id` and its associated code:

        You are a software engineer tasked with generating concise docstrings for each code snippet and tagging it based on its purpose.

        **Instructions**:
        2.1. **Identify Code Type**:
        - Determine whether each code snippet is primarily **backend** or **frontend**.
        - Use common indicators:
            - **Backend**: Handles database interactions, API endpoints, configuration, or server-side logic.
            - **Frontend**: Contains UI components, event handling, state management, or styling.

        2.2. **Summarize the Purpose**:
        - Based on the identified type, write a brief (1-2 sentences) summary of the code's main purpose and functionality.
        - Focus on what the code does, its role in the system, and any critical operations it performs.
        - If the code snippet is related to **specific roles** like authentication, database access, or UI component, state management, explicitly mention this role.

        2.3. **Assign Tags Based on Code Type**:
        - Use these specific tags based on whether the code is identified as backend or frontend:

        **Backend Tags**:
            - **AUTH**: Handles authentication or authorization.
            - **DATABASE**: Interacts with databases.
            - **API**: Defines API endpoints.
            - **UTILITY**: Provides helper or utility functions.
            - **PRODUCER**: Sends messages to a queue or topic.
            - **CONSUMER**: Processes messages from a queue or topic.
            - **EXTERNAL_SERVICE**: Integrates with external services.
            - **CONFIGURATION**: Manages configuration settings.

        **Frontend Tags**:
            - **UI_COMPONENT**: Renders a visual component in the UI.
            - **FORM_HANDLING**: Manages form data submission and validation.
            - **STATE_MANAGEMENT**: Manages application or component state.
            - **DATA_BINDING**: Binds data to UI elements.
            - **ROUTING**: Manages frontend navigation.
            - **EVENT_HANDLING**: Handles user interactions.
            - **STYLING**: Applies styling or theming.
            - **MEDIA**: Manages media, like images or video.
            - **ANIMATION**: Defines animations in the UI.
            - **ACCESSIBILITY**: Implements accessibility features.
            - **DATA_FETCHING**: Fetches data for frontend use.

        Your response must be a valid JSON object containing a list of docstrings, where each docstring object has:
        - node_id: The ID of the node being documented
        - docstring: A concise description of the code's purpose and functionality
        - tags: A list of relevant tags from the categories above

        Here are the code snippets:

        {code_snippets}
        """

        # Prepare the code snippets
        code_snippets = ""
        for request in batch:
            code_snippets += (
                f"node_id: {request.node_id} \n```\n{request.text}\n```\n\n "
            )

        messages = [
            {
                "role": "system",
                "content": "You are an expert software documentation assistant. You will analyze code and provide structured documentation in JSON format.",
            },
            {
                "role": "user",
                "content": base_prompt.format(code_snippets=code_snippets),
            },
        ]

        client = instructor.from_gemini(
        client=genai.GenerativeModel(
            model_name="models/gemini-2.0-flash",  # model defaults to "gemini-pro"
        ),
        mode=instructor.Mode.GEMINI_JSON,
        )
        response = client.chat.completions.create(
            messages=messages,
            response_model=DocstringResponse,
        )
        return response

    def generate_embedding(self, text: str) -> List[float]:
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()

    def update_neo4j_with_docstrings(self, repo_id: str, docstrings: DocstringResponse):
        with self.driver.session() as session:
            batch_size = 300
            docstring_list = [
                {
                    "node_id": n.node_id,
                    "docstring": n.docstring,
                    "tags": n.tags,
                    "embedding": self.generate_embedding(n.docstring),
                }
                for n in docstrings.docstrings
            ]
            repo_path = "default"
            is_local_repo = True if repo_path else False
            for i in range(0, len(docstring_list), batch_size):
                batch = docstring_list[i : i + batch_size]
                session.run(
                    """
                    UNWIND $batch AS item
                    MATCH (n:NODE {repoId: $repo_id, node_id: item.node_id})
                    SET n.docstring = item.docstring,
                        n.embedding = item.embedding,
                        n.tags = item.tags
                    """
                    + ("" if is_local_repo else "REMOVE n.text, n.signature"),
                    batch=batch,
                    repo_id=repo_id,
                )

    def store_graph_to_neo4j(self,nx_graph,project_id="default"):
        with self.driver.session() as session:
            node_count = nx_graph.number_of_nodes()
            print(f"Number of node: {node_count}")
            # Batch insert nodes
            batch_size = 300
            for i in range(0, node_count, batch_size):
                batch_nodes = list(nx_graph.nodes(data=True))[i : i + batch_size]
                nodes_to_create = []

                for node_id, node_data in batch_nodes:
                    # Get the node type and ensure it's one of our expected types
                    node_type = node_data.get("type", "UNKNOWN")
                    if node_type == "UNKNOWN":
                        continue
                    # Initialize labels with NODE
                    labels = ["NODE"]

                    # Add specific type label if it's a valid type
                    if node_type in ["FILE", "CLASS", "FUNCTION", "INTERFACE"]:
                        labels.append(node_type)

                    # Prepare node data
                    processed_node = {
                        "name": node_data.get(
                            "name", node_id
                        ),  # Use node_id as fallback
                        "file_path": node_data.get("file", ""),
                        "start_line": node_data.get("line", -1),
                        "end_line": node_data.get("end_line", -1),
                        "repoId": project_id,
                        "node_id": generate_node_id(node_id),
                        "type": node_type,
                        "text": node_data.get("text", ""),
                        "labels": labels,
                    }

                    # Remove None values
                    processed_node = {
                        k: v for k, v in processed_node.items() if v is not None
                    }
                    nodes_to_create.append(processed_node)

                # Create nodes with labels
                session.run(
                    """
                    UNWIND $nodes AS node
                    CALL apoc.create.node(node.labels, node) YIELD node AS n
                    RETURN count(*) AS created_count
                    """,
                    nodes=nodes_to_create,
                )

            relationship_count = nx_graph.number_of_edges()
            print(f"Creating {relationship_count} relationships")

            # Create relationships in batches
            for i in range(0, relationship_count, batch_size):
                batch_edges = list(nx_graph.edges(data=True))[i : i + batch_size]
                edges_to_create = []
                for source, target, data in batch_edges:
                    edge_data = {
                        "source_id": generate_node_id(source),
                        "target_id": generate_node_id(target),
                        "type": data.get("type", "REFERENCES"),
                        "repoId": project_id,
                    }
                    # Remove any null values from edge_data
                    edge_data = {k: v for k, v in edge_data.items() if v is not None}
                    edges_to_create.append(edge_data)

                session.run(
                    """
                    UNWIND $edges AS edge
                    MATCH (source:NODE {node_id: edge.source_id, repoId: edge.repoId})
                    MATCH (target:NODE {node_id: edge.target_id, repoId: edge.repoId})
                    CALL apoc.create.relationship(source, edge.type, {repoId: edge.repoId}, target) YIELD rel
                    RETURN count(rel) AS created_count
                    """,
                    edges=edges_to_create,
                )
                print("Graph stored in Neo4j successfully.")

    def project_setup(self,repo_dir: str,cleanup: bool=False):
        if(cleanup):
            self.cleanup_neo4j()
        map=RepoMap(root=repo_dir,verbose=True,main_model=SimpleTokenCounter(),io=SimpleIO(),)
        nx_graph = map.create_graph(repo_dir)
        # visualize_graph(nx_graph)
        self.store_graph_to_neo4j(nx_graph)

    def project_updates(self,repo_dir: str,changed_files,cleanup: bool=False):
        
        map=RepoMap(root=repo_dir,verbose=True,main_model=SimpleTokenCounter(),io=SimpleIO())
        
        
        if(cleanup):
            self.cleanup_neo4j()

        if changed_files[0]==-1: #Initial commit
            nx_graph = map.create_graph(repo_dir)
            self.store_graph_to_neo4j(nx_graph)
        else:
            nx_graph = map.check_for_updates(changed_files,repo_dir)
            updated_nodes = self.update_graph_to_neo4j(nx_graph)
            if updated_nodes:
                asyncio.run(self.generate_docstrings_updates(updated_nodes))

    def update_graph_to_neo4j(self,nx_graph,project_id="default"):
       
        with self.driver.session() as session:
            node_count = nx_graph.number_of_nodes()
            print(f"Number of node: {node_count}")
            # Batch insert nodes
            batch_size = 300
            for i in range(0, node_count, batch_size):
                batch_nodes = list(nx_graph.nodes(data=True))[i : i + batch_size]
                nodes_to_update = []

                for node_id, node_data in batch_nodes:
                    
                    nodes_to_update.append({
                        "node_id": generate_node_id(node_id),
                        "text": node_data.get("text", ""),
                        "repo_id": project_id
                        })
                    

                query = """
                UNWIND $nodes AS node
                MATCH (n:NODE {node_id: node.node_id})
                SET n.text = node.text
                """
                session.run(query, nodes=nodes_to_update)
                
        
        return nodes_to_update

    
    def cleanup_neo4j(self):
        print("This is a help function")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n;")
        self.driver.close()
        print("Neo4j graph cleaned up successfully.")
    
    def create_vector_index(self):
        with self.driver.session() as session:
            session.run(
                """
                CREATE VECTOR INDEX docstring_embedding IF NOT EXISTS
                FOR (n:NODE)
                ON (n.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 384,
                    `vector.similarity_function`: 'cosine'
                }}
                """
            )

    async def run_inference(self, repo_id: str="default"):
        docstrings = await self.generate_docstrings(repo_id)
        print(
            f"DEBUGNEO4J: After generate docstrings, Repo ID: {repo_id}, Docstrings: {len(docstrings)}"
        )
        self.log_graph_stats(repo_id)
        self.create_vector_index()


    def query_vector_index(
        self,
        query: str,
        node_ids: Optional[List[str]] = None,
        project_id: str="default",
        top_k: int = 5,
    ) -> List[Dict]:
        embedding = self.generate_embedding(query)

        with self.driver.session() as session:
            if node_ids:
                # Fetch context node IDs
                result_neighbors = session.run(
                    """
                    MATCH (n:NODE)
                    WHERE n.repoId = $project_id AND n.node_id IN $node_ids
                    CALL {
                        WITH n
                        MATCH (n)-[*1..4]-(neighbor:NODE)
                        RETURN COLLECT(DISTINCT neighbor.node_id) AS neighbor_ids
                    }
                    RETURN COLLECT(DISTINCT n.node_id) + REDUCE(acc = [], neighbor_ids IN COLLECT(neighbor_ids) | acc + neighbor_ids) AS context_node_ids
                    """,
                    project_id=project_id,
                    node_ids=node_ids,
                )
                context_node_ids = result_neighbors.single()["context_node_ids"]

                # Use vector index and filter by context_node_ids
                result = session.run(
                    """
                    CALL db.index.vector.queryNodes('docstring_embedding', $initial_k, $embedding)
                    YIELD node, score
                    WHERE node.repoId = $project_id AND node.node_id IN $context_node_ids
                    RETURN node.node_id AS node_id,
                        node.docstring AS docstring,
                        node.file_path AS file_path,
                        node.start_line AS start_line,
                        node.end_line AS end_line,
                        score AS similarity
                    ORDER BY similarity DESC
                    LIMIT $top_k
                    """,
                    project_id=project_id,
                    embedding=embedding,
                    context_node_ids=context_node_ids,
                    initial_k=top_k * 10,  # Adjust as needed
                    top_k=top_k,
                )
            else:
                result = session.run(
                    """
                    CALL db.index.vector.queryNodes('docstring_embedding', $top_k, $embedding)
                    YIELD node, score
                    WHERE node.repoId = $project_id
                    RETURN node.node_id AS node_id,
                        node.docstring AS docstring,
                        node.file_path AS file_path,
                        node.start_line AS start_line,
                        node.end_line AS end_line,
                        score AS similarity
                    """,
                    project_id=project_id,
                    embedding=embedding,
                    top_k=top_k,
                )

            # Ensure all fields are included in the final output
            return [dict(record) for record in result]
