import json
from langchain.tools import tool
import os
from typing import Dict, Any
import re
@tool
def save_response_to_file(response: str) -> None:
    """
    Saves the response in the desired format (JSON, TXT, JAVA, PY) to a file.

    :param response: The final response (JSON string or plain text).
    :param file_path: Path where the file should be saved.
    :param file_format: Format of the file ('json', 'txt', 'java', 'py', etc).
    """
    response = re.search(r'\{.*\}', response).group(0)
    response = json.loads(response)
    text = response.get("response","")
    file_path = response.get("file_path")


    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure directory exists

    

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(text)  # Write plain text

    



