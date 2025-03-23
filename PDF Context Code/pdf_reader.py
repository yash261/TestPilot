import PyPDF2
from typing import List, Tuple
import re
import hashlib

def read_pdf(file_path: str) -> str:
    """Read text from a PDF file."""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return ""

def generate_chunk_id(text: str) -> str:
    """Generate a deterministic chunk ID based on text content."""
    # Create SHA-256 hash of the text
    hash_object = hashlib.sha256(text.encode('utf-8'))
    # Use first 32 characters of hex digest as ID
    return hash_object.hexdigest()[:32]

def create_semantic_chunks(text: str, max_chunk_size: int = 500) -> List[Tuple[str, str]]:
    """
    Create semantic chunks from text with deterministic IDs based on content.
    Args:
        text: Input text to chunk
        max_chunk_size: Maximum characters per chunk (approximate)
    Returns:
        List of tuples containing (chunk_id, chunk_text)
    """
    # Normalize whitespace and split into paragraphs
    text = re.sub(r'\s+', ' ', text.strip())
    paragraphs = text.split('\n\n')
    
    chunks = []
    
    for paragraph in paragraphs:
        # Clean paragraph
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # If paragraph is shorter than max_chunk_size, add it as is
        if len(paragraph) <= max_chunk_size:
            chunk_id = generate_chunk_id(paragraph)
            chunks.append((chunk_id, paragraph))
            continue
            
        # Split long paragraphs into sentences
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding sentence exceeds max_chunk_size, start new chunk
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                chunk_id = generate_chunk_id(current_chunk)
                chunks.append((chunk_id, current_chunk.strip()))
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                
        # Add remaining text as a chunk
        if current_chunk:
            chunk_id = generate_chunk_id(current_chunk)
            chunks.append((chunk_id, current_chunk.strip()))
    
    # Remove duplicates while preserving order
    seen_ids = set()
    unique_chunks = []
    for chunk_id, chunk_text in chunks:
        if chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            unique_chunks.append((chunk_id, chunk_text))
    
    return unique_chunks

def process_pdf_to_chunks(pdf_path: str, max_chunk_size: int = 500) -> List[Tuple[str, str]]:
    """
    Process a PDF file and return semantic chunks with deterministic IDs.
    Args:
        pdf_path: Path to the PDF file
        max_chunk_size: Maximum characters per chunk
    Returns:
        List of tuples containing (chunk_id, chunk_text)
    """
    # Read PDF
    text = read_pdf(pdf_path)
    if not text:
        return []
        
    # Create semantic chunks
    chunks = create_semantic_chunks(text, max_chunk_size)
    
    return chunks

def generate_chunks(pdf_path:str):
    
    try:
        # Process PDF and get chunks
        chunks = process_pdf_to_chunks(pdf_path, max_chunk_size=512)
        
        # Print results
        print(f"Created {len(chunks)} unique semantic chunks:")
        for chunk_id, chunk_text in chunks[:5]:  # Show first 5 chunks
            print(f"\nChunk ID: {chunk_id}")
            print(f"Text: {chunk_text[:100]}...")  # Show first 100 chars
            print(f"Length: {len(chunk_text)} characters")
        
        if len(chunks) > 5:
            print(f"...and {len(chunks) - 5} more chunks")
        return chunks
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
