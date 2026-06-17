import os
import re
import requests
import chromadb
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi
try:
    from sentence_transformers import CrossEncoder
except ImportError as e:
    print(f"Warning: Could not import sentence_transformers (CrossEncoder reranking will be disabled): {e}")
    CrossEncoder = None
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

def search_web(query: str, max_results: int = 5) -> List[dict]:
    if not DDGS:
        print("duckduckgo-search package not available.")
        return []
    
    # Try different backends in sequence for robustness against rate-limits / blocklists
    backends = ["auto", "html", "lite", "bing"]
    for backend in backends:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results, backend=backend))
                if results:
                    return [
                        {
                            "title": r.get("title", "Web Result"),
                            "snippet": r.get("body", ""),
                            "url": r.get("href", "")
                        }
                        for r in results
                    ]
        except Exception as e:
            print(f"Web search failed with backend {backend}: {e}")
    return []

def clean_llm_answer(text: str) -> str:
    if not text:
        return text

    # Strip markdown links (e.g. [Google](https://google.com) -> Google)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Strip bracketed reference numbers like [1], [2], [1, 2], [1 - 3]
    text = re.sub(r'\[\d+(?:[\s,\\\-]*\d+)*\]', '', text)
    # Strip parenthesized reference numbers like (1), (2), (1, 2)
    text = re.sub(r'\(\d+(?:[\s,\\\-]*\d+)*\)', '', text)

    # Specific documents and files
    pdf_pattern = r'[\w\-\+\.]+(?:\s+\(\d+\))?\.pdf'
    
    doc_names = [
        pdf_pattern,
        r'vit\-ap academic regulations',
        r'academic regulations',
        r'code of ethics',
        r'hostellers affidavit',
        r'idp\+?draft',
        r'idp draft',
        r'ipr policy and guidelines',
        r'ipr policy',
        r'ipr guidelines',
        r'admission policy',
        r'aisp 2025 schedule',
        r'aisp schedule',
        r'm\.sc\.\s*programme[\w\-\s]*brochure',
        r'm\.sc\.\s*programme',
        r'public self disclosure',
        r'self disclosure',
        r'vitree[\w\-\s]*brochure',
    ]

    # Generic terms for documents/sources
    generic_terms = [
        r'the (?:provided )?documents?',
        r'the (?:provided )?snippets?',
        r'the (?:provided )?policies?',
        r'the (?:provided )?regulations?',
        r'the (?:provided )?affidavits?',
        r'the (?:provided )?guidelines?',
        r'the (?:provided )?files?',
        r'the (?:provided )?context',
        r'the (?:provided )?sources?',
        r'the (?:provided )?database',
        r'the (?:provided )?texts?',
    ]

    all_docs_pattern = '|'.join(doc_names + generic_terms)

    # Split into sentences to filter out pure reference sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    cleaned_sentences = []

    # Regex to match sentences that are purely about where the info is located or what a doc contains
    sentence_ref_regex = (
        r'(?i)^\s*(?:please\s+)?(?:you\s+can\s+(?:find|check|read|see|look\s+up)\s+)?'
        r'(?:the|this|these|our|more|provided|local|context|source|\s)*\s*'
        r'(?:this|these|it|information|info|details?|regulations?|guidelines?|policies?|rules?|fees?|timings?|procedures?|affidavits?|pages?|numbers?|snippets?|documents?|snippets)\s+'
        r'(?:is|are|was|were|can\s+be|will\s+be|has\s+been|have\s+been|only|just|\s)*\s*'
        r'(?:described|detailed|specified|outlined|found|stated|contained|mentioned|given|provided|explained|retrieved|sourced|contain|contains|list|lists|show|shows|have|has|include|includes)\b'
        r'[^.]{0,30}?' # limit intermediate words before preposition to prevent matching long clauses
        r'(?:in|from|under|at|by|refer\s+to|see|check|details?\s+in)\s+(?:the\s+)?(?:provided\s+)?'
        r'(?:' + all_docs_pattern + r')\b\s*[\.\!\?]?\s*$'
    )

    for s in sentences:
        s_strip = s.strip()
        if not s_strip:
            continue
        
        # If it's a pure reference sentence, discard it completely
        if re.match(sentence_ref_regex, s_strip):
            continue
            
        # Otherwise, clean the sentence at the word/phrase level
        # 1. Strip introductory phrases + document/generic mentions
        intro_phrase_regex = r'(?i)\b(?:according to|based on|as per|in accordance with|referring to|refer to|in|from|under|details? in|specified in|described in|outlined in|contained in|see|as mentioned in|as outlined in|as detailed in|as described in|as specified in|found in|stated in)\s+(?:the\s+)?(?:provided\s+)?(?:' + all_docs_pattern + r')\b(?:,\s*)?'
        s_clean = re.sub(intro_phrase_regex, '', s_strip)

        # 2. Strip standalone PDF filenames
        s_clean = re.sub(r'(?i)\b[\w\-\+\.]+(?:\s+\(\d+\))?\.pdf\b', '', s_clean)

        # 3. Clean up empty parentheses/brackets
        s_clean = s_clean.replace("()", "").replace("[]", "")

        # 4. Clean up spacing and punctuation
        s_clean = re.sub(r'\s{2,}', ' ', s_clean)
        s_clean = s_clean.replace(" .", ".").replace(" ,", ",").strip()
        
        if s_clean:
            cleaned_sentences.append(s_clean)

    text = ' '.join(cleaned_sentences)
    text = capitalize_sentences(text)
    return text

def capitalize_sentences(text: str) -> str:
    if not text:
        return text
    # Capitalize first character of text if it's a letter
    text = re.sub(r'^([a-z])', lambda m: m.group(1).upper(), text)
    # Capitalize first character after a sentence boundary (.!? followed by whitespace)
    text = re.sub(r'([\.\!\?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
    return text



# Load environment variables from .env file if it exists
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

CHROMA_COLLECTION = os.environ.get("CHROMA_COLLECTION", "vitap")

# Initialize ChromaDB persistent client with default embedding function
client = chromadb.PersistentClient(path=CHROMA_PATH)
emb_fn = embedding_functions.DefaultEmbeddingFunction()
collection = client.get_or_create_collection(name=CHROMA_COLLECTION, embedding_function=emb_fn)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

# Gemini Cloud Support
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

class GeminiAPIError(Exception):
    pass

class GeminiRateLimitError(GeminiAPIError):
    pass

class GeminiAuthError(GeminiAPIError):
    pass

def generate_gemini_response(prompt_text: str, max_tokens: int = 8192, enable_search: bool = False, history: Optional[List[dict]] = None) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    contents = []
    if history:
        for msg in history:
            role = "user" if msg.get("role") == "user" else "model"
            if contents and contents[-1]["role"] == role:
                contents[-1]["parts"][0]["text"] += "\n" + msg.get("content", "")
            else:
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })
                
    if contents and contents[-1]["role"] == "user":
        contents[-1]["parts"][0]["text"] += "\n\n" + prompt_text
    else:
        contents.append({
            "role": "user",
            "parts": [{"text": prompt_text}]
        })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": max_tokens
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    }
    if enable_search:
        payload["tools"] = [{"google_search": {}}]
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            return None
        elif res.status_code == 429:
            raise GeminiRateLimitError("Quota exceeded or rate limit hit on Gemini API.")
        elif res.status_code in (400, 403):
            raise GeminiAuthError(f"Authentication/Configuration error (Status {res.status_code}): {res.text}")
        else:
            raise GeminiAPIError(f"Gemini API returned status {res.status_code}: {res.text}")
    except GeminiAPIError:
        raise
    except Exception as e:
        print(f"Gemini API request failed: {e}")
        raise GeminiAPIError(f"Gemini API request failed: {e}")

# Check for fine-tuned local model
FINE_TUNED_MODEL_PATH = os.path.join(BASE_DIR, "fine_tuned_model")
fine_tuned_pipeline = None

def load_fine_tuned_model():
    global fine_tuned_pipeline
    has_adapter = os.path.exists(os.path.join(FINE_TUNED_MODEL_PATH, "adapter_config.json"))
    has_full_model = os.path.exists(os.path.join(FINE_TUNED_MODEL_PATH, "config.json"))
    
    if has_adapter or has_full_model:
        print(f"Fine-tuned model/adapter found at {FINE_TUNED_MODEL_PATH}. Loading on CPU...")
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            import torch
            try:
                tokenizer = AutoTokenizer.from_pretrained(FINE_TUNED_MODEL_PATH)
            except Exception as tok_err:
                print(f"Tokenizer not found in fine-tuned model path ({tok_err}). Loading from base model 'Qwen/Qwen2.5-0.5B-Instruct'...")
                tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
                
            if has_adapter:
                from peft import PeftModel
                print("Loading base model 'Qwen/Qwen2.5-0.5B-Instruct' on CPU...")
                base_model = AutoModelForCausalLM.from_pretrained(
                    "Qwen/Qwen2.5-0.5B-Instruct",
                    torch_dtype=torch.float32,
                    device_map="cpu"
                )
                print("Loading PEFT adapter weights...")
                model = PeftModel.from_pretrained(base_model, FINE_TUNED_MODEL_PATH)
            else:
                model = AutoModelForCausalLM.from_pretrained(
                    FINE_TUNED_MODEL_PATH,
                    torch_dtype=torch.float32,
                    device_map="cpu"
                )
                
            fine_tuned_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer
            )
            print("Fine-tuned model/adapter loaded successfully.")
        except Exception as e:
            print("Failed to load fine-tuned model/adapter:", e)
            fine_tuned_pipeline = None
    else:
        print(f"Fine-tuned model/adapter not found at {FINE_TUNED_MODEL_PATH}. Using Ollama fallback.")

# Reranker global reference
reranker = None

def load_reranker():
    global reranker
    if CrossEncoder is not None:
        print("Loading CrossEncoder reranking model...")
        try:
            reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            print("CrossEncoder loaded successfully.")
        except Exception as e:
            print("Failed to load CrossEncoder reranking model:", e)
            reranker = None
    else:
        print("CrossEncoder reranking model skipped (sentence_transformers not available).")
        reranker = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models inside the worker process
    load_fine_tuned_model()
    load_reranker()
    yield
    # Clean up on shutdown
    global fine_tuned_pipeline, reranker
    fine_tuned_pipeline = None
    reranker = None

app = FastAPI(title="CampusGPT RAG Web API", lifespan=lifespan)

# BM25 Searcher Helper Class
class BM25Searcher:
    def __init__(self, collection):
        self.collection = collection
        self.bm25 = None
        self.documents = []
        self.metadatas = []
        self.ids = []
        self.reload()

    def reload(self):
        try:
            count = self.collection.count()
            if count == 0:
                self.bm25 = None
                return
            all_data = self.collection.get(include=["documents", "metadatas"])
            self.documents = all_data.get("documents", [])
            self.metadatas = all_data.get("metadatas", [])
            self.ids = all_data.get("ids", [])
            
            # Tokenize corpus for BM25
            tokenized_corpus = [re.findall(r'\w+', doc.lower()) for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_corpus)
            print(f"BM25 index built with {len(self.documents)} documents.")
        except Exception as e:
            print("Error loading BM25 index:", e)
            self.bm25 = None

    def search(self, query: str, top_n: int = 20, category: str = None, document_type: str = None) -> list:
        if not self.bm25:
            return []
        tokenized_query = re.findall(r'\w+', query.lower())
        scores = self.bm25.get_scores(tokenized_query)
        
        results = []
        for idx, score in enumerate(scores):
            meta = self.metadatas[idx]
            # Apply metadata filters if present
            if category and meta.get("category") != category:
                continue
            if document_type and meta.get("document_type") != document_type:
                continue
                
            results.append({
                "id": self.ids[idx],
                "document": self.documents[idx],
                "metadata": meta,
                "score": float(score)
            })
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_n]

# Initialize BM25 searcher
bm25_searcher = BM25Searcher(collection)

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

def sync_database_logic() -> dict:
    """
    Scans the data/pdfs directory and compares with ChromaDB / extracted folder.
    Handles dynamic extraction and chunk updates for changed, new, or deleted PDFs.
    """
    extracted_dir = os.path.join(BASE_DIR, "extracted")
    os.makedirs(extracted_dir, exist_ok=True)
    
    # 1. Get all current PDF files in data/pdfs
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR, exist_ok=True)
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    
    # 2. Get list of source files currently represented in ChromaDB
    db_sources = set()
    try:
        count = collection.count()
        if count > 0:
            all_meta = collection.get(include=["metadatas"])
            for m in all_meta.get("metadatas", []):
                if m and "source" in m:
                    db_sources.add(m["source"])
    except Exception as e:
        print(f"Error querying collection sources: {e}")
        
    updated_files = []
    deleted_files = []
    
    # 3. Handle Deleted PDFs: present in DB or extracted/ but not in pdf_files
    for source in list(db_sources):
        if source not in pdf_files:
            print(f"Deleting chunks for removed PDF: {source}")
            try:
                collection.delete(where={"source": source})
                deleted_files.append(source)
            except Exception as e:
                print(f"Failed to delete chunks for {source}: {e}")
            
            # Remove txt file
            txt_name = source.replace(".pdf", ".txt")
            txt_path = os.path.join(extracted_dir, txt_name)
            if os.path.exists(txt_path):
                try:
                    os.remove(txt_path)
                except Exception as e:
                    print(f"Failed to remove extracted txt {txt_path}: {e}")
                    
    # Check extracted/ directory for any orphaned txt files
    for filename in os.listdir(extracted_dir):
        if filename.endswith(".txt"):
            corr_pdf = filename.replace(".txt", ".pdf")
            if corr_pdf not in pdf_files:
                txt_path = os.path.join(extracted_dir, filename)
                try:
                    os.remove(txt_path)
                    if corr_pdf not in deleted_files:
                        deleted_files.append(corr_pdf)
                except Exception as e:
                    print(f"Failed to remove orphaned txt {txt_path}: {e}")

    # 4. Handle Added or Modified PDFs
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks_added_count = 0
    
    for pdf_name in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        txt_name = pdf_name.replace(".pdf", ".txt")
        txt_path = os.path.join(extracted_dir, txt_name)
        
        needs_processing = False
        
        # Determine if we need to process/re-index this file
        if not os.path.exists(txt_path):
            needs_processing = True
            print(f"File {pdf_name} needs processing: extracted text missing.")
        elif os.path.getmtime(pdf_path) > os.path.getmtime(txt_path):
            needs_processing = True
            print(f"File {pdf_name} needs processing: PDF was updated.")
        elif pdf_name not in db_sources:
            needs_processing = True
            print(f"File {pdf_name} needs processing: not found in database.")
        else:
            try:
                chunks_in_db = collection.get(where={"source": pdf_name}, limit=1)
                if not chunks_in_db or not chunks_in_db.get("ids") or len(chunks_in_db["ids"]) == 0:
                    needs_processing = True
                    print(f"File {pdf_name} needs processing: 0 chunks in database.")
            except Exception:
                needs_processing = True
                
        if needs_processing:
            print(f"Extracting and indexing {pdf_name}...")
            try:
                # A. Extract text
                reader = PdfReader(pdf_path)
                text = ""
                for idx, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        text += f"[Empty Page {idx + 1}]\n"
                
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                    
                # B. Remove existing chunks from DB (if any)
                try:
                    collection.delete(where={"source": pdf_name})
                except Exception:
                    pass
                    
                # C. Split and embed/index
                chunks = text_splitter.split_text(text)
                if chunks:
                    doc_meta = METADATA_MAPPING.get(pdf_name, {"category": "general", "document_type": "document"})
                    ids = [f"{txt_name}_{idx}" for idx in range(len(chunks))]
                    metadatas = [
                        {
                            "source": pdf_name,
                            "category": doc_meta["category"],
                            "document_type": doc_meta["document_type"]
                        }
                        for _ in range(len(chunks))
                    ]
                    
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
                    chunks_added_count += len(chunks)
                    
                updated_files.append(pdf_name)
            except Exception as e:
                print(f"Error indexing {pdf_name}: {e}")
                
    # 5. Reload BM25 index and rebuild searcher if files changed
    changes_occurred = len(updated_files) > 0 or len(deleted_files) > 0
    if changes_occurred:
        print("Changes detected. Reloading BM25 searcher index...")
        bm25_searcher.reload()
        
    return {
        "status": "success",
        "updated_files": updated_files,
        "deleted_files": deleted_files,
        "chunks_added": chunks_added_count,
        "total_chunks": collection.count()
    }


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4
    rag_mode: Optional[bool] = True
    category: Optional[str] = None
    document_type: Optional[str] = None
    enable_hybrid: Optional[bool] = True
    enable_rewrite: Optional[bool] = False
    enable_rerank: Optional[bool] = True
    history: Optional[List[dict]] = None

def get_available_model() -> Optional[str]:
    """
    Scans Ollama tags API for downloaded models and returns the best match.
    Prioritizes qwen2.5:3b, then qwen2:1.5b, then other installed models.
    """
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=2)
        if res.status_code == 200:
            models = [m["name"] for m in res.json().get("models", [])]
            if not models:
                return None
            
            # Priority list for VIT-AP search
            priorities = [OLLAMA_MODEL, "qwen2:1.5b", "qwen2", "phi3:mini", "gemma", "tinyllama"]
            for target in priorities:
                for model in models:
                    if target in model or model.startswith(target):
                        return model
            # Default fallback to the first model in list
            return models[0]
    except Exception:
        pass
    return None

def rewrite_query(query: str, active_model: str, history: Optional[List[dict]] = None) -> str:
    """
    Asks Ollama or Gemini to rewrite the query into an optimized version for semantic document search,
    taking conversation history into account if available.
    """
    history_context = ""
    if history:
        history_context = "Conversation history:\n"
        for msg in history:
            role_name = "User" if msg.get("role") == "user" else "CampusGPT"
            history_context += f"{role_name}: {msg.get('content', '')}\n"
        history_context += "\n"

    prompt = (
        "You are an AI search query optimizer.\n"
        "Your task is to rewrite the user's latest input search query to make it highly specific, "
        "autonomous, and complete, utilizing the conversation history if necessary to resolve context, pronouns, or references.\n"
        "Add relevant context terms such as 'VIT-AP University' or specific regulations where appropriate.\n"
        "Output ONLY the optimized query. Do not add preambles, greetings, or explanations.\n\n"
        f"{history_context}"
        f"Latest User Query: {query}\n"
        "Optimized Query:"
    )
    if GEMINI_API_KEY:
        try:
            rewritten = generate_gemini_response(prompt, max_tokens=2048)
            if rewritten:
                if (rewritten.startswith('"') and rewritten.endswith('"')) or (rewritten.startswith("'") and rewritten.endswith("'")):
                    rewritten = rewritten[1:-1].strip()
                return rewritten
        except Exception as e:
            print("Gemini query rewriting failed, trying local Ollama / falling back:", e)

    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": active_model,
                "prompt": prompt,
                "stream": False
            },
            timeout=5
        )
        if res.status_code == 200:
            rewritten = res.json().get("response", "").strip()
            if (rewritten.startswith('"') and rewritten.endswith('"')) or (rewritten.startswith("'") and rewritten.endswith("'")):
                rewritten = rewritten[1:-1].strip()
            return rewritten if rewritten else query
    except Exception as e:
        print("Query rewriting failed, falling back to original query:", e)
    return query

def reciprocal_rank_fusion(vector_results: list, bm25_results: list, k: int = 60) -> list:
    """
    Combines vector search and BM25 results using Reciprocal Rank Fusion.
    """
    rrf_scores = {}
    
    # Process vector results
    for rank, item in enumerate(vector_results):
        item_id = item["id"]
        if item_id not in rrf_scores:
            rrf_scores[item_id] = {"item": item, "score": 0.0}
        rrf_scores[item_id]["score"] += 1.0 / (k + rank + 1)
        
    # Process BM25 results
    for rank, item in enumerate(bm25_results):
        item_id = item["id"]
        if item_id not in rrf_scores:
            rrf_scores[item_id] = {"item": item, "score": 0.0}
        rrf_scores[item_id]["score"] += 1.0 / (k + rank + 1)
        
    # Sort by RRF score descending
    sorted_scores = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)
    return [x["item"] for x in sorted_scores]

def rerank_passages(query: str, passages: list, top_k: int = 4) -> list:
    """
    Uses the CrossEncoder to rerank candidates.
    """
    if not reranker or not passages:
        return passages[:top_k]
        
    pairs = [[query, p["document"]] for p in passages]
    try:
        scores = reranker.predict(pairs)
        for idx, score in enumerate(scores):
            passages[idx]["rerank_score"] = float(score)
        passages.sort(key=lambda x: x["rerank_score"], reverse=True)
        return passages[:top_k]
    except Exception as e:
        print("Reranking failed:", e)
        return passages[:top_k]

@app.get("/")
def read_root():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/style.css")
def read_css():
    return FileResponse(os.path.join(BASE_DIR, "style.css"))

@app.get("/app.js")
def read_js():
    return FileResponse(os.path.join(BASE_DIR, "app.js"))

@app.get("/api/status")
def check_status():
    """
    Checks the status of local models and service.
    """
    ollama_connected = False
    model_loaded = False
    active_model = None
    
    gemini_active = GEMINI_API_KEY is not None
    
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=1)
        if res.status_code == 200:
            ollama_connected = True
            active_model = get_available_model()
            model_loaded = active_model is not None
    except Exception:
        pass

    # Try loading local model if not yet loaded and path exists
    global fine_tuned_pipeline
    if not fine_tuned_pipeline and os.path.exists(os.path.join(FINE_TUNED_MODEL_PATH, "config.json")):
        load_fine_tuned_model()

    # Ensure BM25 matches the current database collection count
    db_count = collection.count()
    if len(bm25_searcher.documents) != db_count:
        bm25_searcher.reload()

    return {
        "ollama_connected": ollama_connected or gemini_active,
        "model_available": model_loaded or (fine_tuned_pipeline is not None) or gemini_active,
        "target_model": f"Gemini {GEMINI_MODEL} (Cloud)" if gemini_active else ("Fine-Tuned CampusGPT" if fine_tuned_pipeline else (active_model or OLLAMA_MODEL)),
        "total_chunks_in_db": db_count,
        "fine_tuned_active": fine_tuned_pipeline is not None,
        "gemini_active": gemini_active
    }

@app.get("/api/pdfs")
def list_pdfs():
    """
    Lists all PDF files in the data/pdfs directory and their status.
    """
    try:
        if not os.path.exists(PDF_DIR):
            return {"pdfs": []}
            
        files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
        pdf_list = []
        
        for filename in files:
            file_path = os.path.join(PDF_DIR, filename)
            size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
            
            # Count chunks indexed for this PDF
            all_chunks = collection.get(where={"source": filename}, include=[])
            chunk_count = len(all_chunks.get("ids", []))
            
            pdf_list.append({
                "filename": filename,
                "size_mb": size_mb,
                "is_ingested": chunk_count > 0,
                "chunks": chunk_count
            })
            
        return {"pdfs": pdf_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync")
def sync_database():
    """
    Triggers an incremental sync of PDF files in the data/pdfs directory.
    """
    try:
        res = sync_database_logic()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
def query_rag(request: QueryRequest):
    """
    Retrieves document chunks from ChromaDB/BM25, reranks them, and feeds them to Ollama.
    """
    global fine_tuned_pipeline
    query = request.query
    top_k = request.top_k
    rag_mode = request.rag_mode
    
    # --- SECURITY GUARDRAILS ---
    # 1. Input length limitation to prevent buffer/cost exhaustion
    if len(query) > 500:
        return {
            "answer": "⚠️ Guardrail Warning: Query is too long. Please restrict your query to under 500 characters.",
            "results": [],
            "ollama_connected": True
        }
        
    # 2. Simple regex prompt injection / jailbreak protection
    suspicious_patterns = [
        r"ignore (all |the )?previous instructions",
        r"ignore (all |the )?system prompt",
        r"you are no longer",
        r"system instructions",
        r"bypass safety",
        r"jailbreak",
        r"dan mode",
        r"do anything now"
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, query.lower()):
            return {
                "answer": "⚠️ Guardrail Warning: Your query triggered our safety filters. Please frame your question academically about VIT-AP policies.",
                "results": [],
                "ollama_connected": True
            }
    # ---------------------------

    try:
        db_count = collection.count()
        if db_count == 0:
            return {
                "answer": "No documents have been indexed in the database yet. Please run build_db.py or index some PDFs.",
                "results": [],
                "ollama_connected": False
            }
            
        # 0. Sync BM25 index if count mismatch
        if len(bm25_searcher.documents) != db_count:
            bm25_searcher.reload()
            
        # 1. Query Rewriting via LLM if requested
        active_model = get_available_model()
        search_query = query
        if request.enable_rewrite:
            if GEMINI_API_KEY or active_model:
                search_query = rewrite_query(query, active_model, request.history)
                print(f"Original Query: '{query}' -> Rewritten Search Query: '{search_query}'")

        # 2. Candidate Retrieval
        candidates = []
        where_filter = {}
        if request.category:
            where_filter["category"] = request.category
        if request.document_type:
            where_filter["document_type"] = request.document_type
            
        # We query more elements (up to 20) to give RRF and Reranking rich context to filter from
        n_retrieve = min(20, db_count)
        
        # A. Vector Search
        vector_candidates = []
        try:
            if where_filter:
                vector_raw = collection.query(
                    query_texts=[search_query],
                    n_results=n_retrieve,
                    where=where_filter
                )
            else:
                vector_raw = collection.query(
                    query_texts=[search_query],
                    n_results=n_retrieve
                )
                
            if vector_raw and vector_raw.get("documents") and len(vector_raw["documents"]) > 0:
                docs = vector_raw["documents"][0]
                metas = vector_raw["metadatas"][0]
                dists = vector_raw["distances"][0]
                ids = vector_raw["ids"][0]
                for i in range(len(docs)):
                    dist = dists[i]
                    similarity = 1.0 / (1.0 + dist)
                    vector_candidates.append({
                        "id": ids[i],
                        "document": docs[i],
                        "metadata": metas[i],
                        "similarity": round(similarity * 100, 2)
                    })
        except Exception as e:
            print("ChromaDB vector query failed:", e)

        # B. BM25 Search
        bm25_candidates = []
        if request.enable_hybrid:
            bm25_candidates = bm25_searcher.search(
                search_query,
                top_n=n_retrieve,
                category=request.category,
                document_type=request.document_type
            )
            
        # Combine searches
        if request.enable_hybrid:
            candidates = reciprocal_rank_fusion(vector_candidates, bm25_candidates)
        else:
            candidates = vector_candidates

        # 3. Reranking
        if request.enable_rerank and reranker:
            final_results = rerank_passages(search_query, candidates, top_k=top_k)
        else:
            final_results = candidates[:top_k]

        # Check if the query asks for something outside of our local database
        is_external_query = False
        
        # Determine if query has words suggesting external or time-sensitive info
        external_keywords = [
            r"\bnews\b", r"\bevent\b", r"\bevents\b", r"\brecent\b", r"\blatest\b", 
            r"\bhappen\b", r"\bhappened\b", r"\bcurrent\b", r"\btoday\b", r"\byesterday\b", 
            r"\bweather\b", r"\bcalendar\b", r"\bweb\b", r"\binternet\b", r"\bgoogle\b",
            r"\b2025\b", r"\b2026\b", r"\blast year\b", r"\bthis year\b"
        ]
        has_external_keyword = any(re.search(pat, query.lower()) for pat in external_keywords)
        
        if not final_results:
            is_external_query = True
        elif len(vector_candidates) > 0:
            top_similarity = vector_candidates[0]["similarity"]
            # Trigger web search if similarity is very low (< 45.0%)
            # OR if it's moderately low (< 48.0%) and contains external keywords
            if top_similarity < 45.0:
                is_external_query = True
            elif top_similarity < 48.0 and has_external_keyword:
                is_external_query = True

        # 4. Format Prompt and context
        formatted_results = []
        context_parts = []
        
        for item in final_results:
            formatted_results.append(item)
            context_parts.append(f"Source: {item['metadata'].get('source')}\nContent: {item['document']}\n")

        # If it is an external query, perform a free web search fallback
        if is_external_query:
            print(f"Low confidence local match detected. Running Web Search fallback for: '{search_query}'...")
            web_results = search_web(search_query, max_results=4)
            if web_results or GEMINI_API_KEY:
                # Override/augment context parts with web search snippets if available
                context_parts = []
                if web_results:
                    for r in web_results:
                        context_parts.append(f"Source: {r['url']}\nContent: {r['snippet']}\n")
                        formatted_results.append({
                            "id": f"web_{r['url']}",
                            "document": r["snippet"],
                            "metadata": {
                                "source": r["title"] + " (Web)"
                            },
                            "similarity": 100.0
                        })
            
        # 5. RAG Synthesis via Local Fine-Tuned Model, Gemini API, or Ollama Fallback
        answer = None
        ollama_connected = False
        used_model = None
        
        if rag_mode and (formatted_results or is_external_query):
            context_text = "\n---\n".join(context_parts) if context_parts else ""
            
            # Scenario A: Use Google Gemini API (Cloud) if key is provided
            if GEMINI_API_KEY:
                if is_external_query:
                    prompt = (
                        f"You are CampusGPT, a helpful academic assistant for VIT-AP University. "
                        f"The user is asking a question that is outside our local document database. "
                        f"Please answer the user's question directly using Google Search grounding. "
                        f"CRITICAL: Do NOT output any website names, sources, or citations (like [1], [2], or inline links) in your response text. Write a clean, direct answer without any external references.\n\n"
                        f"USER QUESTION: {query}"
                    )
                else:
                    prompt = (
                        f"You are CampusGPT, a helpful academic assistant for VIT-AP University. "
                        f"Your task is to answer the user's question using ONLY the provided document snippets from university policies, regulations, hosteller affidavits, etc. "
                        f"Be factual, concise, and structured. CRITICAL: Do NOT output any PDF filenames, document names, sources, websites, or external references anywhere in your response text. Avoid phrases like 'According to...', 'based on the documents', or listing PDF names or brackets (like [1], [2]). Just answer directly and naturally.\n\n"
                        f"CONTEXT SNIPPETS:\n{context_text}\n"
                        f"USER QUESTION: {query}\n\n"
                        f"CAMPUSGPT ANSWER:"
                    )
                print(f"Generating answer via Google Gemini API (Cloud) with enable_search={is_external_query}...")
                try:
                    answer = generate_gemini_response(prompt, max_tokens=8192, enable_search=is_external_query, history=request.history)
                    if answer:
                        ollama_connected = True  # Virtual online status for UI
                        used_model = "Gemini 2.5 Flash (Cloud)"
                    else:
                        print("Failed to generate response from Google Gemini API. Falling back to local models...")
                except GeminiRateLimitError:
                    answer = "⚠️ CampusGPT is currently receiving too many requests. Please try again in a few moments."
                    ollama_connected = True
                    used_model = "Gemini 2.5 Flash (Rate Limited)"
                except GeminiAuthError as e:
                    answer = "⚠️ CampusGPT configuration error: Invalid Gemini API key or unauthorized access. Please check your .env configuration."
                    ollama_connected = False
                    used_model = "Gemini API Auth Failure"
                except GeminiAPIError as e:
                    print(f"Gemini API error during synthesis: {e}. Falling back to local models...")

            
            # Scenario B: Local Fine-Tuned Model
            if not answer and fine_tuned_pipeline:
                try:
                    # Format as standard chat template for fine-tuned Instruct model
                    system_content = (
                        "You are CampusGPT, a helpful academic assistant for VIT-AP University. "
                        "Answer the user's question using the provided web search context snippets. "
                        "Be factual, concise, and structured. CRITICAL: Do NOT output any website names, PDF filenames, sources, or external references anywhere in your response text. Avoid phrases like 'According to...', 'based on the documents', or listing brackets (like [1], [2]). Just answer directly and naturally."
                        if is_external_query else
                        "You are CampusGPT, a helpful academic assistant for VIT-AP University. "
                        "Answer the user's question using ONLY the provided document snippets. "
                        "Be factual, concise, and structured. CRITICAL: Do NOT output any PDF filenames, document names, sources, websites, or external references anywhere in your response text. Avoid phrases like 'According to...', 'based on the documents', or listing PDF names or brackets (like [1], [2]). Just answer directly and naturally."
                    )
                    messages = [{"role": "system", "content": system_content}]
                    if request.history:
                        for msg in request.history:
                            messages.append({
                                "role": msg.get("role", "user"),
                                "content": msg.get("content", "")
                            })
                    messages.append({
                        "role": "user",
                        "content": f"CONTEXT SNIPPETS:\n{context_text}\nUSER QUESTION: {query}"
                    })
                    
                    formatted_prompt = fine_tuned_pipeline.tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True
                    )
                    
                    print(f"Generating answer locally using Fine-Tuned CampusGPT model on CPU...")
                    outputs = fine_tuned_pipeline(
                        formatted_prompt,
                        max_new_tokens=512,
                        do_sample=True,
                        temperature=0.3,
                        top_p=0.9
                    )
                    
                    generated_text = outputs[0]["generated_text"]
                    if generated_text.startswith(formatted_prompt):
                        answer = generated_text[len(formatted_prompt):].strip()
                    else:
                        answer = generated_text.strip()
                    used_model = "Fine-Tuned CampusGPT (Local)"
                except Exception as e:
                    print("Error during local fine-tuned model inference:", e)
                    # Let fallback happen
                    fine_tuned_pipeline = None
            
            # Scenario C: Local Ollama
            if not answer:
                if not active_model:
                    answer = (
                        "CampusGPT is currently offline. We are unable to load the language model. "
                        "Please verify your Gemini API key in the .env file, or check if the local Ollama service is running and has models installed."
                    )
                    used_model = "Offline Fallback"
                else:
                    history_str = ""
                    if request.history:
                        history_str = "Conversation history:\n"
                        for msg in request.history:
                            role_name = "User" if msg.get("role") == "user" else "CampusGPT"
                            history_str += f"{role_name}: {msg.get('content', '')}\n"
                        history_str += "\n"

                    if is_external_query:
                        prompt = (
                            f"You are CampusGPT, a helpful academic assistant for VIT-AP University. "
                            f"Your task is to answer the user's question using the provided web search context snippets. "
                            f"Be factual, concise, and structured. CRITICAL: Do NOT output any website names, PDF filenames, sources, or external references anywhere in your response text. Avoid phrases like 'According to...', 'based on the documents', or listing brackets (like [1], [2]). Just answer directly and naturally.\n\n"
                            f"WEB SEARCH SNIPPETS:\n{context_text}\n"
                            f"{history_str}"
                            f"USER QUESTION: {query}\n\n"
                            f"CAMPUSGPT ANSWER:"
                        )
                    else:
                        prompt = (
                            f"You are CampusGPT, a helpful academic assistant for VIT-AP University. "
                            f"Your task is to answer the user's question using ONLY the provided document snippets from university policies, regulations, hosteller affidavits, etc. "
                            f"Be factual, concise, and structured. CRITICAL: Do NOT output any PDF filenames, document names, sources, websites, or external references anywhere in your response text. Avoid phrases like 'According to...', 'based on the documents', or listing PDF names or brackets (like [1], [2]). Just answer directly and naturally.\n\n"
                            f"CONTEXT SNIPPETS:\n{context_text}\n"
                            f"{history_str}"
                            f"USER QUESTION: {query}\n\n"
                            f"CAMPUSGPT ANSWER:"
                        )
                    
                    try:
                        res = requests.post(
                            OLLAMA_URL,
                            json={
                                "model": active_model,
                                "prompt": prompt,
                                "stream": False
                            },
                            timeout=25
                        )
                        
                        if res.status_code == 200:
                            answer = res.json().get("response")
                            ollama_connected = True
                            used_model = f"{active_model} (Local Ollama)"
                        else:
                            answer = f"Error generating response using model '{active_model}' from local Ollama."
                            used_model = "Failed Local Ollama"
                    except requests.exceptions.RequestException:
                        answer = "CampusGPT LLM offline. Connection to local Ollama service timed out."
                        used_model = "Offline Fallback (Timeout)"
        else:
            answer = "No matching segments were found in the database matching your filters. Please verify query keywords or change filters."
            
        # Check if local generation returned a refusal/lack-of-info response,
        # and if so, trigger web search fallback.
        if rag_mode and answer and not is_external_query:
            # Regex patterns for lack of info
            insufficient_context_patterns = [
                r"\bno\s+(?:information|details?|data|guidelines?|rules?|policies?|records?)\b",
                r"\bnot\s+(?:mentioned|specified|provided|found|outlined|detailed|contained)\b",
                r"\b(?:does|do|did)\s+not\s+(?:contain|outline|mention|specify|provide|have)\b",
                r"\bcannot\s+(?:find|be found|answer)\b",
                r"\bunable\s+to\s+(?:find|answer)\b",
                r"\bnot\s+available\s+in\s+the\b"
            ]
            
            has_insufficient_context = any(
                re.search(pat, answer.lower()) for pat in insufficient_context_patterns
            )
            
            if has_insufficient_context:
                print(f"LLM indicated insufficient local context: '{answer}'. Triggering Web Search fallback...")
                is_external_query = True
                web_results = search_web(search_query, max_results=4)
                if web_results or GEMINI_API_KEY:
                    context_parts = []
                    if web_results:
                        for r in web_results:
                            context_parts.append(f"Source: {r['url']}\nContent: {r['snippet']}\n")
                            formatted_results.append({
                                "id": f"web_{r['url']}",
                                "document": r["snippet"],
                                "metadata": {
                                    "source": r["title"] + " (Web)"
                                },
                                "similarity": 100.0
                            })
                    context_text = "\n---\n".join(context_parts) if context_parts else ""
                    
                    # Re-run Scenario A, B, or C using web context
                    answer = None
                    if GEMINI_API_KEY:
                        prompt = (
                            f"You are CampusGPT, a helpful academic assistant for VIT-AP University. "
                            f"The user is asking a question that is outside our local document database. "
                            f"Please answer the user's question directly using Google Search grounding. "
                            f"CRITICAL: Do NOT output any website names, sources, or citations (like [1], [2], or inline links) in your response text. Write a clean, direct answer without any external references.\n\n"
                            f"USER QUESTION: {query}"
                        )
                        print(f"Re-generating answer via Google Gemini API (Cloud) using Web Search grounding...")
                        try:
                            answer = generate_gemini_response(prompt, max_tokens=8192, enable_search=True, history=request.history)
                            if answer:
                                used_model = "Gemini 2.5 Flash (Cloud)"
                        except GeminiRateLimitError:
                            answer = "⚠️ CampusGPT is currently receiving too many requests. Please try again in a few moments."
                            used_model = "Gemini 2.5 Flash (Rate Limited)"
                        except GeminiAuthError as e:
                            answer = "⚠️ CampusGPT configuration error: Invalid Gemini API key or unauthorized access. Please check your .env configuration."
                            used_model = "Gemini API Auth Failure"
                        except GeminiAPIError as e:
                            print(f"Gemini API error during re-generation: {e}. Falling back to local models...")
                    
                    if not answer and fine_tuned_pipeline:
                        try:
                            system_content = (
                                "You are CampusGPT, a helpful academic assistant for VIT-AP University. "
                                "Answer the user's question using the provided web search context snippets. "
                                "Be factual, concise, and structured. CRITICAL: Do NOT output any website names, PDF filenames, sources, or external references anywhere in your response text. Avoid phrases like 'According to...', 'based on the documents', or listing brackets (like [1], [2]). Just answer directly and naturally."
                            )
                            messages = [{"role": "system", "content": system_content}]
                            if request.history:
                                for msg in request.history:
                                    messages.append({
                                        "role": msg.get("role", "user"),
                                        "content": msg.get("content", "")
                                    })
                            messages.append({
                                "role": "user",
                                "content": f"CONTEXT SNIPPETS:\n{context_text}\nUSER QUESTION: {query}"
                            })
                            formatted_prompt = fine_tuned_pipeline.tokenizer.apply_chat_template(
                                messages, tokenize=False, add_generation_prompt=True
                            )
                            print(f"Re-generating answer locally using Fine-Tuned CampusGPT model on CPU with Web results...")
                            outputs = fine_tuned_pipeline(
                                formatted_prompt, max_new_tokens=512, do_sample=True, temperature=0.3, top_p=0.9
                            )
                            generated_text = outputs[0]["generated_text"]
                            if generated_text.startswith(formatted_prompt):
                                answer = generated_text[len(formatted_prompt):].strip()
                            else:
                                answer = generated_text.strip()
                            used_model = "Fine-Tuned CampusGPT (Local)"
                        except Exception as e:
                            print("Re-generation via local fine-tuned model failed:", e)
                            
                    if not answer and active_model:
                        history_str = ""
                        if request.history:
                            history_str = "Conversation history:\n"
                            for msg in request.history:
                                role_name = "User" if msg.get("role") == "user" else "CampusGPT"
                                history_str += f"{role_name}: {msg.get('content', '')}\n"
                            history_str += "\n"

                        prompt = (
                            f"You are CampusGPT, a helpful academic assistant for VIT-AP University. "
                            f"Your task is to answer the user's question using the provided web search context snippets. "
                            f"Be factual, concise, and structured. CRITICAL: Do NOT output any website names, PDF filenames, sources, or external references anywhere in your response text. Avoid phrases like 'According to...', 'based on the documents', or listing brackets (like [1], [2]). Just answer directly and naturally.\n\n"
                            f"WEB SEARCH SNIPPETS:\n{context_text}\n"
                            f"{history_str}"
                            f"USER QUESTION: {query}\n\n"
                            f"CAMPUSGPT ANSWER:"
                        )
                        try:
                            res = requests.post(
                                OLLAMA_URL,
                                json={"model": active_model, "prompt": prompt, "stream": False},
                                timeout=25
                            )
                            if res.status_code == 200:
                                answer = res.json().get("response")
                                used_model = f"{active_model} (Local Ollama)"
                        except Exception as e:
                            print("Re-generation via local Ollama failed:", e)

        # Clean answer to strip any accidental references/citations
        answer = clean_llm_answer(answer)
        
        return {
            "answer": answer,
            "results": formatted_results,
            "ollama_connected": ollama_connected or (GEMINI_API_KEY is not None),
            "active_model": used_model if used_model else ("Gemini 2.5 Flash (Cloud)" if GEMINI_API_KEY else ("Fine-Tuned CampusGPT (Local)" if fine_tuned_pipeline else active_model)),
            "rewritten_query": search_query if request.enable_rewrite and search_query != query else None
        }
        
    except Exception as e:
        print("Error processing RAG query:", e)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
