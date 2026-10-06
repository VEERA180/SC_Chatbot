"""
VGIMT Chatbot - Document Chunking, Embedding & Upload Script
=============================================================

This script handles:
1. Chunking large Excel tables (50 rows per chunk)
2. Generating embeddings using Volvo GenAI Hub
3. Uploading documents to Azure AI Search

Features:
- Resume capability with checkpoints
- Batch processing (Embedding: 10, Upload: 100)
- Progress tracking and detailed logging
- Error handling with retries

Usage:
    python upload_documents.py                    # Run full pipeline
    python upload_documents.py --chunk-only       # Only chunk and save
    python upload_documents.py --resume           # Resume from checkpoint
    python upload_documents.py --stats            # Show statistics only
"""

import json
import hashlib
import os
import sys
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import urllib3

# Disable SSL warnings for internal APIs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_PATH = PROJECT_ROOT / ".env"
INPUT_FILE = PROJECT_ROOT / "ExtractedData" / "llm_output" / "all_extracted_combined.json"
CHUNKED_FILE = PROJECT_ROOT / "ExtractedData" / "llm_output" / "all_extracted_chunked.json"
CHECKPOINT_FILE = SCRIPT_DIR / "upload_checkpoint.json"
LOG_FILE = SCRIPT_DIR / "upload_log.txt"

# Chunking config
EXCEL_CHUNK_SIZE = 50  # rows per chunk for Excel tables
ROW_LEVEL_INDEXING = True  # Enable row-level indexing for CSV/XLSX (pin-point accuracy)

# Batch sizes
EMBEDDING_BATCH_SIZE = 10
UPLOAD_BATCH_SIZE = 100

# Retry config
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# ============================================================================
# LOAD ENVIRONMENT 
# ============================================================================

def load_environment():
    """Load environment variables from .env file."""
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
        print(f"✅ Loaded environment from {ENV_PATH}")
    else:
        print(f"❌ Environment file not found: {ENV_PATH}")
        sys.exit(1)
    
    required_vars = [
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX",
        "OPENAI_SDK_ENDPOINT",
        "EMBEDDING_DEPLOYMENT",
        "EMBEDDING_API_KEY",
        "EMBEDDING_API_VERSION",
        "EMBEDDING_DIMENSIONS",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "AZURE_TENANT_ID"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    return {
        "search_endpoint": os.getenv("AZURE_SEARCH_ENDPOINT"),
        "search_api_key": os.getenv("AZURE_SEARCH_API_KEY"),
        "search_index": os.getenv("AZURE_SEARCH_INDEX"),
        "search_api_version": os.getenv("AZURE_SEARCH_API_VERSION", "2023-11-01"),
        "embedding_endpoint": os.getenv("OPENAI_SDK_ENDPOINT"),
        "deployment": os.getenv("EMBEDDING_DEPLOYMENT"),
        "embedding_api_key": os.getenv("EMBEDDING_API_KEY"),
        "embedding_api_version": os.getenv("EMBEDDING_API_VERSION"),
        "embedding_dimensions": int(os.getenv("EMBEDDING_DIMENSIONS", "3072")),
        "azure_client_id": os.getenv("AZURE_CLIENT_ID"),
        "azure_client_secret": os.getenv("AZURE_CLIENT_SECRET"),
        "azure_tenant_id": os.getenv("AZURE_TENANT_ID"),
        "openai_endpoint": os.getenv("OPENAI_SDK_ENDPOINT")
    }


# ============================================================================
# LOGGING
# ============================================================================

def log_message(message: str, console: bool = True):
    """Log message to file and optionally console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")
    
    if console:
        print(message)


# ============================================================================
# CHECKPOINT MANAGEMENT
# ============================================================================

def save_checkpoint(data: Dict[str, Any]):
    """Save checkpoint for resume capability."""
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    log_message(f"💾 Checkpoint saved: {data.get('stage', 'unknown')} - {data.get('progress', 0)} items", console=False)


def load_checkpoint() -> Optional[Dict[str, Any]]:
    """Load checkpoint if exists."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def clear_checkpoint():
    """Clear checkpoint file."""
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        log_message("🗑️ Checkpoint cleared")


# ============================================================================
# DATA LOADING
# ============================================================================

def load_input_data() -> List[Dict[str, Any]]:
    """Load input JSON data."""
    log_message(f"📂 Loading data from {INPUT_FILE}")
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    log_message(f"✅ Loaded {len(data):,} records")
    return data


def save_chunked_data(data: List[Dict[str, Any]]):
    """Save chunked data to new JSON file."""
    log_message(f"💾 Saving chunked data to {CHUNKED_FILE}")
    
    with open(CHUNKED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    log_message(f"✅ Saved {len(data):,} records to {CHUNKED_FILE.name}")


# ============================================================================
# ID GENERATION
# ============================================================================

def generate_id(document_location: str, page: int, chunk: int = 0) -> str:
    """
    Generate unique ID using MD5 hash.
    Format: {document_location}_{page}_{chunk} -> MD5[:16]
    """
    id_string = f"{document_location}_{page}_{chunk}"
    return hashlib.md5(id_string.encode()).hexdigest()[:16]


def generate_parent_id(file_name: str) -> str:
    """
    Generate parent ID for grouping all chunks/pages of a document.
    Uses MD5 hash of the filename for consistency.
    This enables sequential context retrieval by grouping all pages of the same document.
    """
    return hashlib.md5(file_name.encode()).hexdigest()[:16]


# ============================================================================
# EXCEL TABLE CHUNKING
# ============================================================================

def parse_table_to_rows(table_str: str) -> List[List[str]]:
    """Parse markdown table string to rows."""
    if not table_str or not table_str.strip():
        return []
    
    lines = table_str.strip().split("\n")
    rows = []
    
    for line in lines:
        # Skip separator lines (e.g., |---|---|---|)
        if line.strip().startswith("|") and set(line.replace("|", "").replace("-", "").strip()) == set():
            continue
        if "---" in line and "|" in line:
            continue
        
        # Parse data rows
        if "|" in line:
            cells = [cell.strip() for cell in line.split("|")]
            # Remove empty first/last cells from | delimiter
            cells = [c for c in cells if c or cells.index(c) not in [0, len(cells)-1]]
            if cells:
                rows.append(cells)
    
    return rows


def rows_to_markdown_table(header: List[str], rows: List[List[str]]) -> str:
    """Convert rows back to markdown table format."""
    if not rows:
        return ""
    
    lines = []
    
    # Header row
    lines.append("| " + " | ".join(header) + " |")
    
    # Separator
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    
    # Data rows
    for row in rows:
        # Pad row if needed
        while len(row) < len(header):
            row.append("")
        lines.append("| " + " | ".join(row[:len(header)]) + " |")
    
    return "\n".join(lines)


def create_row_level_documents(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create row-level documents for CSV/XLSX files.
    Each row becomes a separate searchable document with column headers preserved.
    This enables pin-point accurate retrieval for tabular data.
    """
    tables = record.get("tables", [])
    
    # If no tables, return empty list
    if not tables or not isinstance(tables, list):
        return []
    
    # Check if this is a CSV/Excel file
    file_name = record.get("file", "").lower()
    is_tabular = file_name.endswith((".xlsx", ".xls", ".csv"))
    
    if not is_tabular:
        return []
    
    # Parse tables and extract rows
    all_rows = []
    headers = []
    
    for table in tables:
        if isinstance(table, str):
            rows = parse_table_to_rows(table)
            if rows and len(rows) > 0:
                if not headers:
                    headers = rows[0]  # First row is header
                    data_rows = rows[1:]  # Rest are data
                else:
                    data_rows = rows
                all_rows.extend(data_rows)
        elif isinstance(table, dict):
            table_str = table.get("content", str(table))
            rows = parse_table_to_rows(table_str)
            if rows and len(rows) > 0:
                if not headers:
                    headers = rows[0]
                    data_rows = rows[1:]
                else:
                    data_rows = rows
                all_rows.extend(data_rows)
    
    # If no data rows found, return empty
    if not all_rows or not headers:
        return []
    
    # Create document for each row
    row_documents = []
    parent_id = generate_parent_id(record.get("file", ""))
    
    for row_idx, row in enumerate(all_rows):
        # Create row_data string: "Column1: Value1 | Column2: Value2 | ..."
        row_data_parts = []
        for col_idx, header in enumerate(headers):
            value = row[col_idx] if col_idx < len(row) else ""
            if value.strip():  # Only include non-empty values
                row_data_parts.append(f"{header}: {value}")
        
        row_data = " | ".join(row_data_parts)
        
        # Skip empty rows
        if not row_data.strip():
            continue
        
        # Create document for this row
        row_doc = {
            "id": generate_id(record.get("document_location", ""), record.get("page", 1), row_idx + 1),
            "parent_id": parent_id,
            "sequence_number": float(row_idx + 1),
            "file": record.get("file", ""),
            "page": record.get("page", 1),
            "total_pages": record.get("total_pages", 1),
            "document_location": record.get("document_location", ""),
            "URL": record.get("URL", ""),
            "source": record.get("source", "VGIMT"),
            "parent_title": record.get("parent_title", ""),
            "heading": f"{record.get('heading', '')} - Row {row_idx + 1}",
            "summary": row_data,  # Row data as summary for embedding
            "row_data": row_data,  # Dedicated field for row content
            "text": row_data,
            "tables": "",  # Individual row, not full table
            "numbered_steps": "",
            "screenshot_description": "",
            "column_headers": " | ".join(headers)  # Store headers for reference
        }
        
        row_documents.append(row_doc)
    
    if row_documents:
        log_message(f"  📊 Row-level: {record.get('file', 'unknown')} -> {len(row_documents)} rows", console=False)
    
    return row_documents


def chunk_excel_tables(record: Dict[str, Any], chunk_size: int = EXCEL_CHUNK_SIZE) -> List[Dict[str, Any]]:
    """
    Chunk large Excel tables into smaller records.
    Returns list of chunked records (or single record if no chunking needed).
    """
    tables = record.get("tables", [])
    
    # If no tables or tables is not a list, return as-is
    if not tables or not isinstance(tables, list):
        return [record]
    
    # Check if this is an Excel file with large tables
    file_name = record.get("file", "").lower()
    is_excel = file_name.endswith((".xlsx", ".xls", ".csv"))
    
    if not is_excel:
        return [record]
    
    # Parse all tables and count total rows
    all_table_rows = []
    headers = []
    
    for table in tables:
        if isinstance(table, str):
            rows = parse_table_to_rows(table)
            if rows:
                if not headers and len(rows) > 0:
                    headers = rows[0]  # First row is header
                    all_table_rows.extend(rows[1:])  # Rest are data rows
                else:
                    all_table_rows.extend(rows)
        elif isinstance(table, dict):
            # Handle dict format if present
            table_str = table.get("content", str(table))
            rows = parse_table_to_rows(table_str)
            if rows:
                if not headers and len(rows) > 0:
                    headers = rows[0]
                    all_table_rows.extend(rows[1:])
                else:
                    all_table_rows.extend(rows)
    
    # If not enough rows to chunk, return as-is
    if len(all_table_rows) <= chunk_size:
        return [record]
    
    # Chunk the rows
    chunks = []
    total_chunks = (len(all_table_rows) + chunk_size - 1) // chunk_size
    
    for i in range(0, len(all_table_rows), chunk_size):
        chunk_num = i // chunk_size + 1
        chunk_rows = all_table_rows[i:i + chunk_size]
        
        # Create chunked record
        chunked_record = record.copy()
        
        # Generate new ID for chunk
        chunked_record["id"] = generate_id(
            record.get("document_location", ""),
            record.get("page", 1),
            chunk_num
        )
        
        # Update tables with chunked data
        chunked_table = rows_to_markdown_table(headers, chunk_rows)
        chunked_record["tables"] = [chunked_table] if chunked_table else []
        
        # Update heading/summary to indicate chunk
        original_heading = record.get("heading", "")
        chunked_record["heading"] = f"{original_heading} (Part {chunk_num}/{total_chunks})"
        
        # Update summary to include chunk info
        original_summary = record.get("summary", "")
        row_range = f"rows {i+1}-{min(i+chunk_size, len(all_table_rows))}"
        chunked_record["summary"] = f"{original_summary} [{row_range} of {len(all_table_rows)}]"
        
        # Mark as chunked
        chunked_record["chunk_info"] = {
            "chunk_num": chunk_num,
            "total_chunks": total_chunks,
            "row_start": i + 1,
            "row_end": min(i + chunk_size, len(all_table_rows)),
            "total_rows": len(all_table_rows)
        }
        
        chunks.append(chunked_record)
    
    return chunks


def process_all_records(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process all records with row-level indexing for CSV/XLSX and chunking for others."""
    log_message("🔄 Processing records (row-level indexing for CSV/XLSX, chunking for others)...")
    
    processed = []
    chunked_count = 0
    row_level_count = 0
    row_docs_total = 0
    original_count = len(data)
    
    for i, record in enumerate(data):
        # Generate ID if not present
        if "id" not in record:
            record["id"] = generate_id(
                record.get("document_location", ""),
                record.get("page", 1),
                0
            )
        
        # Add parent_id for sequential context (groups all pages of same document)
        file_name = record.get("file", "")
        record["parent_id"] = generate_parent_id(file_name)
        
        # Add sequence_number for ordering (use page number)
        record["sequence_number"] = float(record.get("page", 1))
        
        # Check if this is a CSV/Excel file for row-level indexing
        is_tabular = file_name.lower().endswith((".xlsx", ".xls", ".csv"))
        
        if is_tabular and ROW_LEVEL_INDEXING:
            # Create row-level documents for CSV/XLSX
            row_docs = create_row_level_documents(record)
            
            if row_docs:
                row_level_count += 1
                row_docs_total += len(row_docs)
                processed.extend(row_docs)
                continue  # Skip normal processing for this record
        
        # For non-tabular files or if row-level indexing didn't produce results,
        # use regular chunking
        chunks = chunk_excel_tables(record)
        
        if len(chunks) > 1:
            chunked_count += 1
            log_message(f"  📊 Chunked: {record.get('file', 'unknown')} -> {len(chunks)} parts", console=False)
            
            # For chunked files, update sequence numbers for sub-chunks
            for chunk_idx, chunk in enumerate(chunks):
                chunk["parent_id"] = record["parent_id"]
                chunk["sequence_number"] = float(record.get("page", 1)) + (chunk_idx * 0.01)
        
        processed.extend(chunks)
        
        # Progress update
        if (i + 1) % 500 == 0:
            log_message(f"  Processed {i+1:,}/{original_count:,} records...")
    
    log_message(f"✅ Processing complete:")
    log_message(f"   - Original records: {original_count:,}")
    log_message(f"   - CSV/XLSX files with row-level indexing: {row_level_count:,} ({row_docs_total:,} rows)")
    log_message(f"   - Other records chunked: {chunked_count:,}")
    log_message(f"   - Final documents: {len(processed):,}")
    
    return processed


# ============================================================================
# CONTENT FOR EMBEDDING
# ============================================================================

def create_content_for_embedding(record: Dict[str, Any]) -> str:
    """
    Create content string for embedding.
    Format: {parent_title} | {file} | {heading} | {summary}
    """
    parts = [
        record.get("parent_title", ""),
        record.get("file", ""),
        record.get("heading", ""),
        record.get("summary", "")
    ]
    
    # Filter out empty parts and join
    content = " | ".join(p for p in parts if p and p.strip())
    
    # Truncate if too long (embedding models have token limits)
    max_chars = 8000  # Safe limit for most embedding models
    if len(content) > max_chars:
        content = content[:max_chars]
    
    return content


# ============================================================================
# AZURE AD AUTHENTICATION
# ============================================================================

# Cache for bearer token
_bearer_token_cache = {
    "token": None,
    "expires_at": 0
}

def get_azure_bearer_token(config: Dict[str, Any]) -> str:
    """
    Get Azure AD Bearer token for embeddings API.
    Caches the token and refreshes when expired.
    """
    import time as time_module
    
    # Check if cached token is still valid (with 5 min buffer)
    if _bearer_token_cache["token"] and _bearer_token_cache["expires_at"] > time_module.time() + 300:
        return _bearer_token_cache["token"]
    
    log_message("🔑 Fetching new Azure AD Bearer token...")
    
    token_url = f"https://login.microsoftonline.com/{config['azure_tenant_id']}/oauth2/v2.0/token"
    
    data = {
        "client_id": config["azure_client_id"],
        "client_secret": config["azure_client_secret"],
        "grant_type": "client_credentials",
        "scope": "api://a18b5274-e7df-4ae7-a9af-b5d200dd200f/.default"
    }
    
    try:
        response = requests.post(token_url, data=data, verify=False, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        token = "Bearer " + result["access_token"]
        
        # Cache token with expiry (default 1 hour)
        expires_in = result.get("expires_in", 3600)
        _bearer_token_cache["token"] = token
        _bearer_token_cache["expires_at"] = time_module.time() + expires_in
        
        log_message("✅ Bearer token obtained successfully")
        return token
        
    except Exception as e:
        # Surface the actual AAD error body (e.g. AADSTS codes) to aid diagnosis
        detail = ""
        resp = getattr(e, "response", None)
        if resp is not None:
            try:
                body = resp.json()
                detail = f" | {body.get('error')}: {body.get('error_description', '')}"
            except Exception:
                detail = f" | {resp.text}"
        raise Exception(f"Failed to get Azure AD Bearer token: {str(e)}{detail}")


# ============================================================================
# EMBEDDING GENERATION
# ============================================================================

def get_embeddings(texts: List[str], config: Dict[str, Any]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts using Volvo GenAI Hub.
    Uses Azure AD Bearer token authentication.
    """
    # Get bearer token
    bearer_token = get_azure_bearer_token(config)
    
    # Volvo GenAI Hub embedding endpoint (needs /azure-openai-data-inference path)
    url = f"{config['embedding_endpoint']}/openai/deployments/{config['deployment']}/embeddings?api-version={config['embedding_api_version']}"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": bearer_token,
        "api-key": config['embedding_api_key']  # Needs both Bearer token and api-key!
    }
    
    payload = {
        "input": texts,
        "dimensions": config["embedding_dimensions"]
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(url, headers=headers, json=payload, verify=False, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            embeddings = [item["embedding"] for item in result["data"]]
            return embeddings
            
        except requests.exceptions.RequestException as e:
            log_message(f"⚠️ Embedding attempt {attempt + 1}/{MAX_RETRIES} failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                # If 401, refresh token
                if hasattr(e, 'response') and e.response is not None and e.response.status_code == 401:
                    _bearer_token_cache["token"] = None
                    bearer_token = get_azure_bearer_token(config)
                    headers["Authorization"] = bearer_token
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise Exception(f"Failed to generate embeddings after {MAX_RETRIES} attempts: {str(e)}")
    
    return []


def process_embeddings(records: List[Dict[str, Any]], config: Dict[str, Any], start_idx: int = 0) -> List[Dict[str, Any]]:
    """Process all records and generate embeddings in batches."""
    log_message(f"🔢 Generating embeddings (batch size: {EMBEDDING_BATCH_SIZE})...")
    
    total = len(records)
    processed_count = start_idx
    
    for i in range(start_idx, total, EMBEDDING_BATCH_SIZE):
        batch_end = min(i + EMBEDDING_BATCH_SIZE, total)
        batch = records[i:batch_end]
        
        # Create content for embedding
        texts = [create_content_for_embedding(r) for r in batch]
        
        # Generate embeddings
        try:
            embeddings = get_embeddings(texts, config)
            
            # Assign embeddings to records
            for j, embedding in enumerate(embeddings):
                records[i + j]["content_vector"] = embedding
                records[i + j]["content_for_embedding"] = texts[j]
            
            processed_count = batch_end
            
            # Progress update
            progress_pct = (processed_count / total) * 100
            log_message(f"  📊 Embeddings: {processed_count:,}/{total:,} ({progress_pct:.1f}%)")
            
            # Save checkpoint
            save_checkpoint({
                "stage": "embedding",
                "progress": processed_count,
                "total": total,
                "timestamp": datetime.now().isoformat()
            })
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            log_message(f"❌ Error at batch {i}-{batch_end}: {str(e)}")
            save_checkpoint({
                "stage": "embedding",
                "progress": i,
                "total": total,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            raise
    
    log_message(f"✅ Embedding generation complete: {processed_count:,} records")
    return records


# ============================================================================
# AZURE SEARCH UPLOAD
# ============================================================================

def prepare_document_for_upload(record: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a single document for Azure Search upload."""
    
    # Helper function to ensure string conversion (handles arrays, None, nested structures)
    def to_string(value, separator="\n"):
        """Convert any value to string, handling lists, None, and nested structures."""
        if value is None or value == "":
            return ""
        if isinstance(value, list):
            # Filter out None/empty and convert each item to string
            return separator.join(str(item) for item in value if item not in (None, "", []))
        return str(value)
    
    doc = {
        "@search.action": "upload",
        "id": to_string(record.get("id", "")),
        "parent_id": to_string(record.get("parent_id", "")),
        "sequence_number": record.get("sequence_number", 1.0),
        "content_for_embedding": to_string(record.get("content_for_embedding", "")),
        "content_vector": record.get("content_vector", []),  # Only field that stays as array
        "heading": to_string(record.get("heading", "")),
        "text": to_string(record.get("text", "")),
        "summary": to_string(record.get("summary", "")),
        "file": to_string(record.get("file", "")),
        "page": record.get("page", 1),
        "parent_title": to_string(record.get("parent_title", "")),
        "total_pages": record.get("total_pages", 1),
        "document_location": to_string(record.get("document_location", "")),
        "URL": to_string(record.get("URL", "")),
        "source": to_string(record.get("source", "VGIMT")),
        "row_data": to_string(record.get("row_data", "")),
        "column_headers": to_string(record.get("column_headers", "")),
        "numbered_steps": to_string(record.get("numbered_steps", ""), separator="\n"),
        "screenshot_description": to_string(record.get("screenshot_description", "")),
        "tables": to_string(record.get("tables", ""), separator="\n\n"),
    }
    
    return doc


def upload_batch(documents: List[Dict[str, Any]], config: Dict[str, Any]) -> Tuple[int, int]:
    """Upload a batch of documents to Azure Search. Returns (success_count, error_count)."""
    url = f"{config['search_endpoint']}/indexes/{config['search_index']}/docs/index?api-version={config['search_api_version']}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": config["search_api_key"]
    }
    
    payload = {"value": documents}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200 or response.status_code == 207:
                result = response.json()
                values = result.get("value", [])
                success = sum(1 for v in values if v.get("status", False))
                errors = len(values) - success
                return success, errors
            else:
                log_message(f"⚠️ Upload attempt {attempt + 1}/{MAX_RETRIES} failed: {response.status_code} - {response.text[:200]}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    
        except requests.exceptions.RequestException as e:
            log_message(f"⚠️ Upload attempt {attempt + 1}/{MAX_RETRIES} failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    
    return 0, len(documents)


def upload_to_search(records: List[Dict[str, Any]], config: Dict[str, Any], start_idx: int = 0) -> Tuple[int, int]:
    """Upload all records to Azure Search in batches."""
    log_message(f"☁️ Uploading to Azure Search (batch size: {UPLOAD_BATCH_SIZE})...")
    
    total = len(records)
    total_success = 0
    total_errors = 0
    
    for i in range(start_idx, total, UPLOAD_BATCH_SIZE):
        batch_end = min(i + UPLOAD_BATCH_SIZE, total)
        batch = records[i:batch_end]
        
        # Prepare documents
        documents = [prepare_document_for_upload(r) for r in batch]
        
        # Upload batch
        success, errors = upload_batch(documents, config)
        total_success += success
        total_errors += errors
        
        # Progress update
        progress_pct = (batch_end / total) * 100
        log_message(f"  ☁️ Upload: {batch_end:,}/{total:,} ({progress_pct:.1f}%) - Success: {total_success:,}, Errors: {total_errors:,}")
        
        # Save checkpoint
        save_checkpoint({
            "stage": "upload",
            "progress": batch_end,
            "total": total,
            "success": total_success,
            "errors": total_errors,
            "timestamp": datetime.now().isoformat()
        })
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    log_message(f"✅ Upload complete: {total_success:,} success, {total_errors:,} errors")
    return total_success, total_errors


# ============================================================================
# STATISTICS
# ============================================================================

def show_statistics(data: List[Dict[str, Any]]):
    """Show statistics about the data."""
    print("\n" + "=" * 60)
    print("📊 DATA STATISTICS")
    print("=" * 60)
    
    # Count by file type
    file_types = {}
    for record in data:
        file_name = record.get("file", "unknown")
        ext = Path(file_name).suffix.lower() if file_name else ".unknown"
        file_types[ext] = file_types.get(ext, 0) + 1
    
    print(f"\n📁 Total records: {len(data):,}")
    print("\n📄 By file type:")
    for ext, count in sorted(file_types.items(), key=lambda x: -x[1]):
        print(f"   {ext}: {count:,}")
    
    # Count by source
    sources = {}
    for record in data:
        source = record.get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1
    
    print("\n🏷️ By source:")
    for source, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"   {source}: {count:,}")
    
    # Unique files
    unique_files = set(r.get("file", "") for r in data)
    print(f"\n📚 Unique files: {len(unique_files):,}")
    
    # Records with tables
    with_tables = sum(1 for r in data if r.get("tables") and len(r.get("tables", [])) > 0)
    print(f"\n📊 Records with tables: {with_tables:,}")
    
    # Records with embeddings
    with_embeddings = sum(1 for r in data if r.get("content_vector"))
    print(f"\n🔢 Records with embeddings: {with_embeddings:,}")
    
    print("\n" + "=" * 60)


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_full_pipeline(config: Dict[str, Any], resume: bool = False):
    """Run the full pipeline: chunk -> embed -> upload."""
    start_time = time.time()
    log_message("=" * 60)
    log_message("🚀 VGIMT Document Upload Pipeline Started")
    log_message("=" * 60)
    
    checkpoint = load_checkpoint() if resume else None
    
    # Stage 1: Load and chunk data
    if checkpoint and checkpoint.get("stage") in ["embedding", "upload"]:
        log_message("📂 Loading chunked data from checkpoint...")
        with open(CHUNKED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        log_message(f"✅ Loaded {len(data):,} chunked records")
    else:
        # Load original data
        data = load_input_data()
        
        # Process and chunk
        data = process_all_records(data)
        
        # Save chunked data
        save_chunked_data(data)
        
        # Clear any old checkpoint
        clear_checkpoint()
    
    # Stage 2: Generate embeddings
    embedding_start_idx = 0
    if checkpoint and checkpoint.get("stage") == "embedding":
        embedding_start_idx = checkpoint.get("progress", 0)
        log_message(f"🔄 Resuming embeddings from index {embedding_start_idx:,}")
    elif checkpoint and checkpoint.get("stage") == "upload":
        log_message("✅ Embeddings already complete, skipping...")
        # Load data with embeddings
        with open(CHUNKED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        embedding_start_idx = 0
    
    if not (checkpoint and checkpoint.get("stage") == "upload"):
        data = process_embeddings(data, config, embedding_start_idx)
        
        # Save data with embeddings
        save_chunked_data(data)
    
    # Stage 3: Upload to Azure Search
    upload_start_idx = 0
    if checkpoint and checkpoint.get("stage") == "upload":
        upload_start_idx = checkpoint.get("progress", 0)
        log_message(f"🔄 Resuming upload from index {upload_start_idx:,}")
    
    success, errors = upload_to_search(data, config, upload_start_idx)
    
    # Clear checkpoint on success
    if errors == 0:
        clear_checkpoint()
    
    # Summary
    elapsed = time.time() - start_time
    log_message("=" * 60)
    log_message("🎉 PIPELINE COMPLETE")
    log_message("=" * 60)
    log_message(f"⏱️ Total time: {elapsed/60:.1f} minutes")
    log_message(f"📊 Total records: {len(data):,}")
    log_message(f"✅ Successfully uploaded: {success:,}")
    log_message(f"❌ Upload errors: {errors:,}")
    log_message("=" * 60)


def run_chunk_only():
    """Run only the chunking stage."""
    log_message("=" * 60)
    log_message("🔄 CHUNK ONLY MODE")
    log_message("=" * 60)
    
    # Load original data
    data = load_input_data()
    
    # Process and chunk
    data = process_all_records(data)
    
    # Save chunked data
    save_chunked_data(data)
    
    # Show statistics
    show_statistics(data)
    
    log_message("✅ Chunking complete!")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="VGIMT Document Upload Pipeline")
    parser.add_argument("--chunk-only", action="store_true", help="Only chunk data, don't embed or upload")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    parser.add_argument("--clear-checkpoint", action="store_true", help="Clear checkpoint and start fresh")
    
    args = parser.parse_args()
    
    # Load environment
    config = load_environment()
    
    print("\n📍 Configuration:")
    print(f"   Search Endpoint: {config['search_endpoint']}")
    print(f"   Search Index: {config['search_index']}")
    print(f"   Embedding Model: {config['deployment']}")
    print(f"   Embedding Dimensions: {config['embedding_dimensions']}")
    print()
    
    if args.clear_checkpoint:
        clear_checkpoint()
        print("✅ Checkpoint cleared. Run again without --clear-checkpoint to start fresh.")
        return
    
    if args.stats:
        if CHUNKED_FILE.exists():
            with open(CHUNKED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = load_input_data()
        show_statistics(data)
        return
    
    if args.chunk_only:
        run_chunk_only()
        return
    
    # Run full pipeline
    run_full_pipeline(config, resume=args.resume)


if __name__ == "__main__":
    main()
