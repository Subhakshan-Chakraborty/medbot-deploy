from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

# Extract data from PDF
def load_pdf_file(data):
    loader = DirectoryLoader(data, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    return documents

# Split into text chunks
def text_split(extracted_data):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    text_chunks = text_splitter.split_documents(extracted_data)
    return text_chunks

# Use lighter model to reduce memory usage
def download_hugging_face_embeddings():
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/paraphrase-MiniLM-L3-v2')  # lighter model (~60MB)
    return embeddings

# Extract user initials
def get_initials(name):
    parts = name.strip().split()
    return (parts[0][0] + parts[1][0]).upper() if len(parts) > 1 else parts[0][0].upper()
