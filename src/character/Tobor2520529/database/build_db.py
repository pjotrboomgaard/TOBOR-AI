import os
import re
import argparse
import chromadb
from langchain_community.document_loaders import DirectoryLoader, PDFPlumberLoader
from langchain_community.embeddings import OpenAIEmbeddings
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import time
import hashlib  # Import hashlib for SHA-1 hashing
from tqdm import tqdm  # Import tqdm for progress bar

def normalize_filename(filename):
    """Normalize the filename by stripping whitespace and converting to lowercase."""
    return filename.strip().lower()

def chunk_document(text, max_chunk_size):
    """Split a document text into chunks of a specified maximum size."""
    chunks = []
    while text:
        split_pos = min(len(text), max_chunk_size)
        if split_pos < len(text):
            split_pos = text.rfind(' ', 0, split_pos) + 1
        chunks.append(text[:split_pos])
        text = text[split_pos:]
    return chunks

def clean_text(text):
    """Clean the text by removing unwanted characters and extra whitespace."""
    unwanted_chars = re.compile(r'[^a-zA-Z0-9\s.,!?;:()+%-]')
    almost_cleaned_text = re.sub(unwanted_chars, '', text)
    cleaned_text = re.sub(r'\s+', ' ', almost_cleaned_text).strip()
    return cleaned_text

def create_metadata(file_index, page_number, source, URL=None):
    """Create metadata for a document chunk."""
    metadata = {
        "document_id": file_index + 1,  # file_index represents the actual file number
        "page_number": page_number,
        "source": source,
        "URL": URL if URL is not None else "",
        "chunk_id": None  # This will be set later for each chunk
    }
    return metadata

def load_links_from_file(file_path):
    """
    Load filenames and URLs from a file that uses
    semicolons (;) as the delimiter, storing them in a dictionary.
    """
    links = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # If there's a semicolon in the line, split by the first semicolon
            if ';' in line:
                parts = line.strip().split(';', 1)
                if len(parts) == 2:
                    filename, url = parts
                    filename = filename.strip()
                    url = url.strip()
                    normalized_filename = normalize_filename(filename)
                    links[normalized_filename] = url
    return links

def generate_sha1_hash(content):
    """Generate a SHA-1 hash for the given content string."""
    return hashlib.sha1(content.encode('utf-8')).hexdigest()

# Set up environment for OpenAI API key
# Load API key from environment variable instead of hardcoding it
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Error: OPENAI_API_KEY environment variable not set")
    exit(1)
os.environ["OPENAI_API_KEY"] = openai_api_key

# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument('-input_dir', help='Input directory containing files to be cleaned and embedded in ChromaDB', default=None)
parser.add_argument('-specific_files', help='Specific file(s) to be processed (comma-separated list)', default=None)
parser.add_argument('-output_dir', help='Output directory for ChromaDB based on files', default=None)
parser.add_argument('-link_file', help='Path to a text file containing filenames and URLs', default=None)
parser.add_argument('-add_web_link_to_sources', help='Whether to add URLs to sources', action='store_true')
parser.add_argument('-db_name', help='Name of the database. Defaults to "DB_" + input directory name', default=None)

args = parser.parse_args()

# Set up output directory and database name
output_directory = args.output_dir if args.output_dir else '.'
db_name = args.db_name if args.db_name else (
    'DB_' + os.path.basename(args.input_dir.rstrip('/')) if args.input_dir else 'default'
)

print(f"Database Name: {db_name}")

# Verify input directory exists if provided
if args.input_dir and not os.path.exists(args.input_dir):
    print(f"Error: The directory {args.input_dir} does not exist.")
    exit()

# Create output directory if it does not exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Load links from file if provided
link_sources = {}
if args.link_file:
    link_sources = load_links_from_file(args.link_file)

# Load documents from specific files or directory
if args.specific_files:
    file_list = [file.strip() for file in args.specific_files.split(',')]
    documents = []
    for file_path in file_list:
        if os.path.exists(file_path):
            file_loader = PDFPlumberLoader(file_path=file_path)
            documents.extend(file_loader.load())
        else:
            print(f"Warning: The file {file_path} does not exist and will be skipped.")
else:
    loader = DirectoryLoader(
        path=args.input_dir,
        loader_cls=PDFPlumberLoader
    )
    documents = loader.load()

# If adding web links but no link file is provided, prompt user for URLs
if args.add_web_link_to_sources and not args.link_file:
    for document in documents:
        filename = document.metadata.get('source', None)
        if filename:
            link = input(f"Enter the URL for {filename}: ")
            normalized_filename = normalize_filename(filename)
            link_sources[normalized_filename] = link

# Check if any documents were loaded
if not documents:
    print("No documents were loaded. Please check the input source.")
    exit()
else:
    print(f"{len(documents)} pages loaded successfully.")

# Initialize ChromaDB and OpenAI Embeddings
db_path = os.path.join(output_directory, db_name)
chroma_client = chromadb.PersistentClient(path=db_path)
openai_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=os.environ["OPENAI_API_KEY"])

collection = chroma_client.get_or_create_collection(name="my_collection", embedding_function=openai_ef)

# Fetch the unique sources from the existing collection
existing_documents = collection.get()
unique_sources = set()
highest_existing_file_index = 0

if existing_documents and existing_documents.get('metadatas'):
    if 'source' in existing_documents['metadatas'][0]:
        unique_sources = {meta['source'] for meta in existing_documents['metadatas']}
        highest_existing_file_index = len(unique_sources)

file_index = highest_existing_file_index
page_number = 1
current_source = None

# Process each document and add it to the ChromaDB
for doc_index, document in enumerate(tqdm(documents, desc="Processing documents", unit="doc")):
    source = document.metadata.get('source', f"Document {file_index + 1}")
    filename = os.path.basename(source) if source else None
    normalized_filename = normalize_filename(filename)
    URL = link_sources.get(normalized_filename, None)

    if URL is None:
        print(f"Warning: No URL found for {filename}. Continuing without a URL.")

    if current_source != source:
        file_index += 1
        current_source = source
        page_number = 0

    print(f"Processing file number: {file_index}, page number: {page_number}")

    text = document.page_content
    cleaned_text = text
    # cleaned_text = clean_text(text)
    chunks = [cleaned_text]  # If you want more granular chunks, replace with chunk_document(cleaned_text, <chunk_size>)

    for chunk_index, chunk in enumerate(tqdm(chunks, desc="Processing chunks", unit="chunk", leave=False)):
        if not chunk.strip():
            print(f"Skipping empty chunk for file {file_index}, page {page_number}.")
            continue

        print(f'Processing chunk {chunk_index + 1}/{len(chunks)} of file {file_index}, page {page_number}')
        print(f"Chunk Content: {chunk[:100]}...")

        metadata = create_metadata(file_index, page_number, source, URL)
        chunk_id = generate_sha1_hash(chunk)
        metadata["chunk_id"] = chunk_id

        try:
            embeddings = openai_ef([chunk])
            collection.add(ids=[chunk_id], embeddings=embeddings, documents=[chunk], metadatas=[metadata])
        except Exception as e:
            print(f"Failed to process chunk {chunk_index + 1} due to error: {e}")

        time.sleep(1.5)

    page_number += 1

print("Processing complete. All documents have been added to ChromaDB.")

# Verify the contents of the ChromaDB collection
print("\nChecking the contents of the collection...")
results = collection.get()

print(f"Total items in collection: {len(results['documents'])}")
for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
    print(f"\nItem {i + 1}:")
    print(f"Chunk ID: {metadata['chunk_id']}")
    print(f"Document ID: {metadata['document_id']}")
    print(f"Page Number: {metadata['page_number']}")
    print(f"Source: {metadata['source']}")
    print(f"URL: {metadata.get('URL', 'N/A')}")
    print(f"Content: {doc[:100]}...")
