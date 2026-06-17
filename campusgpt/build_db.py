import os
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Initialize Persistent client in the chroma_db folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "chroma_db"))

# Use default embedding function (ONNX-based all-MiniLM-L6-v2)
emb_fn = embedding_functions.DefaultEmbeddingFunction()

CHROMA_COLLECTION = os.environ.get("CHROMA_COLLECTION", "vitap")

collection = client.get_or_create_collection(
    name=CHROMA_COLLECTION,
    embedding_function=emb_fn
)

folder = os.path.join(BASE_DIR, "extracted")

# Rich metadata mapping for each document source
METADATA_MAPPING = {
    "AISP_2025_Schedule.pdf": {"category": "academic", "document_type": "schedule"},
    "Code-of-Ethics-VIT-AP (1).pdf": {"category": "ethics", "document_type": "policy"},
    "Code-of-Ethics-VIT-AP.pdf": {"category": "ethics", "document_type": "policy"},
    "HOSTELLERS-AFFIDAVIT.pdf": {"category": "hostel", "document_type": "affidavit"},
    "IDP+Draft.pdf": {"category": "academic", "document_type": "policy"},
    "M.Sc.Programme-With-Entrance-Information-Brochure.pdf": {"category": "admission", "document_type": "brochure"},
    "VIT-AP-ADMISSION-POLICY.pdf": {"category": "admission", "document_type": "policy"},
    "VIT-AP-University-IPR_Policy-and-Guidelines.pdf": {"category": "academic", "document_type": "policy"},
    "VIT-AP-Academic-Regulations.pdf": {"category": "academic", "document_type": "policy"},
    "VITAP_Public_Self_Disclosure.pdf": {"category": "administration", "document_type": "disclosure"},
    "vitree-january-2025-information-brochure.pdf": {"category": "admission", "document_type": "brochure"},
}

# Delete the collection first if we want to rebuild clean
try:
    client.delete_collection(CHROMA_COLLECTION)
except Exception:
    pass
collection = client.get_or_create_collection(name=CHROMA_COLLECTION, embedding_function=emb_fn)

# Setup text splitter with chunk overlap
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)

print("Indexing documents into ChromaDB...")
for file in os.listdir(folder):
    if file.endswith(".txt"):
        print(f"Indexing {file}...")
        
        file_path = os.path.join(folder, file)
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        chunks = text_splitter.split_text(text)
        
        if not chunks:
            continue
            
        source_filename = file.replace(".txt", ".pdf")
        doc_meta = METADATA_MAPPING.get(source_filename, {"category": "general", "document_type": "document"})
        
        ids = [f"{file}_{idx}" for idx in range(len(chunks))]
        # Attach rich metadata to each chunk
        metadatas = [
            {
                "source": source_filename,
                "category": doc_meta["category"],
                "document_type": doc_meta["document_type"]
            }
            for _ in range(len(chunks))
        ]
        
        # Batch insert chunks
        batch_size = 200
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]
            batch_metadatas = metadatas[i : i + batch_size]
            
            collection.add(
                ids=batch_ids,
                documents=batch_chunks,
                metadatas=batch_metadatas
            )

print(f"Database Created successfully. Total chunks: {collection.count()}")

