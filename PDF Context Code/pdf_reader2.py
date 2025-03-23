import re
import fitz  # PyMuPDF
import hashlib
from typing import List, Dict
import spacy

# Load spaCy model for semantic analysis
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    doc.close()
    return text

def generate_chunk_id(content: str) -> str:
    """Generates a consistent chunk ID based on the hash of the content."""
    hash_object = hashlib.md5(content.encode('utf-8'))
    return f"chunk_{hash_object.hexdigest()}"

def semantic_chunking(text: str, max_chunk_size: int = 1000) -> List[str]:
    """Splits text into semantically coherent chunks using NLP."""
    doc = nlp(text)
    chunks = []
    current_chunk = ""
    
    for sent in doc.sents:
        if len(current_chunk) + len(sent.text) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sent.text
        else:
            current_chunk += " " + sent.text
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def chunk_document_hybrid(text: str, max_semantic_size: int = 1000) -> List[Dict[str, str]]:
    """
    Chunks the document using structural headings and semantic chunking for large content.
    
    Args:
        text (str): Raw text from the OCR output
        max_semantic_size (int): Maximum size before semantic splitting
        
    Returns:
        List[Dict]: List of chunks with metadata and content
    """
  
    lines = text.split('\n')
    
    # Patterns for main sections (all caps) and subsections
    main_section_pattern = r'^\d+\.\s+[A-Z\s]+$'  # e.g., "1. INTRODUCTION"
    subsection_pattern = r'^\d+\.\d+\s+[A-Za-z\s]+$'  # e.g., "1.1 Purpose"
    
    chunks = []
    current_chunk = {"metadata": {"section": "", "type": ""}, "content": ""}
    current_main_section = ""
    
    print("Processing lines:")
    for i, line in enumerate(lines):
        line = line.strip()
        # print(f"Line {i}: '{line}'")
        
        # Check for main section (all caps)
        if re.match(main_section_pattern, line):
            if current_chunk["content"]:  # Save previous chunk if it has content
                chunks.append(current_chunk)
                print(f"Saved chunk: {current_chunk['metadata']['section']}")
            current_main_section = line
            current_chunk = {
                "metadata": {
                    "section": current_main_section,
                    "type": "section"
                },
                "content": ""
            }
            print(f"New main section: {line}")
            continue
        
        # Check for subsection
        if re.match(subsection_pattern, line):
            if current_chunk["content"]:  # Save previous chunk if it has content
                chunks.append(current_chunk)
                print(f"Saved chunk: {current_chunk['metadata']['section']}")
            current_chunk = {
                "metadata": {
                    "section": line,
                    "parent_section": current_main_section,
                    "type": "subsection"
                },
                "content": ""
            }
            print(f"New subsection: {line}")
            continue
        
        # Add line to current chunk's content
        if line and current_chunk["metadata"]["section"]:  # Only add if we have a section
            current_chunk["content"] += " " + line
            print(f"Added to {current_chunk['metadata']['section']}: {line}")
    
    # Add the last chunk if it has content
    if current_chunk["content"]:
        chunks.append(current_chunk)
        print(f"Saved final chunk: {current_chunk['metadata']['section']}")
    
    # Refine chunks with semantic chunking if too large
    final_chunks = []
    for chunk in chunks:
        chunk["content"] = chunk["content"].strip()
        if len(chunk["content"]) > max_semantic_size and chunk["metadata"]["type"] == "subsection":
            sub_chunks = semantic_chunking(chunk["content"], max_semantic_size)
            for i, sub_content in enumerate(sub_chunks):
                new_chunk = {
                    "metadata": {
                        "section": f"{chunk['metadata']['section']} - Part {i+1}",
                        "parent_section": chunk["metadata"]["parent_section"],
                        "type": "subsection"
                    },
                    "content": sub_content
                }
                final_chunks.append(new_chunk)
                print(f"Semantically split {chunk['metadata']['section']} into Part {i+1}")
        else:
            final_chunks.append(chunk)
    
    # Add metadata
    for chunk in final_chunks:
        chunk["metadata"]["chunk_id"] = generate_chunk_id(chunk["content"])
        chunk["metadata"]["approx_length"] = len(chunk["content"])
    
    return final_chunks

def print_chunks(chunks: List[Dict[str, str]]):
    """Helper function to print chunks in a readable format"""
    if not chunks:
        print("No chunks generated!")
        return
    for chunk in chunks:
        print(f"\nChunk ID: {chunk['metadata']['chunk_id']}")
        print(f"Section: {chunk['metadata']['section']}")
        if "parent_section" in chunk["metadata"]:
            print(f"Parent Section: {chunk['metadata']['parent_section']}")
        print(f"Type: {chunk['metadata']['type']}")
        print(f"Length: {chunk['metadata']['approx_length']}")
        print(f"Content Preview: {chunk['content']}...")
        print("-" * 50)

def get_chunks(pdf_path:str):
    document_text = extract_text_from_pdf(pdf_path)
    chunks = chunk_document_hybrid(document_text, max_semantic_size=1000)
    return chunks


# Test with your document
if __name__ == "__main__":
    pdf_path = "Data/Demo.pdf"
    document_text = extract_text_from_pdf(pdf_path)
    
    chunks = chunk_document_hybrid(document_text, max_semantic_size=1000)
    print(f"\nTotal chunks generated: {len(chunks)}")
    print_chunks(chunks)