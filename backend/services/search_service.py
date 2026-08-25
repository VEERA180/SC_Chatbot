"""
Search service for Azure AI Search
Handles vector and hybrid search with proper error handling
"""
from typing import List, Dict, Any, Optional
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.exceptions import AzureError

from core.config import SearchConfig
from core.exceptions import SearchError
from core.logging_config import get_logger

logger = get_logger(__name__)


class SearchService:
    """Manages Azure AI Search operations"""
    
    # Define fields to return from VGIMT documents
    RETURN_FIELDS = [
        "id", "heading", "text", "summary", "file", "page",
        "parent_title", "total_pages", "document_location", "URL", "source",
        "numbered_steps", "screenshot_description", "tables",
        "parent_id", "sequence_number", "row_data", "column_headers"  # Sequential context fields
    ]
    
    # Context overflow prevention limits
    MAX_TOTAL_DOCUMENTS = 40      # Global cap on total documents after expansion
    MAX_PARENTS_TO_EXPAND = 5     # Max number of parent documents to expand siblings for
    
    # Context window config for different file types
    CONTEXT_CONFIG = {
        "pptx": {"fetch_all": True, "max_items": 30},  # Fetch all slides (limit 50)
        "docx": {"fetch_all": True, "max_items": 30},  # Fetch all pages (limit 50)
        "pdf": {"fetch_all": False, "window_size": 3},  # ±3 pages around match
        "xlsx": {"fetch_all": False, "window_size": 10},  # ±5 rows around match
        "csv": {"fetch_all": False, "window_size": 10},   # ±5 rows around match
    }
    
    def __init__(self, config: SearchConfig):
        self.config = config
        
        try:
            self.client = SearchClient(
                endpoint=config.endpoint,
                index_name=config.index_name,
                credential=AzureKeyCredential(config.api_key)
            )
            logger.info(f"SearchService initialized: index={config.index_name}")
        except Exception as e:
            error_msg = f"Failed to initialize SearchClient: {str(e)}"
            logger.error(error_msg)
            raise SearchError(error_msg)
    
    def vector_search(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filter_expression: Optional[str] = None,
        include_sequential_context: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search with optional sequential context expansion
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return (default from config)
            filter_expression: OData filter expression
            include_sequential_context: If True, expand results with document siblings
            
        Returns:
            List of search results as dictionaries
            
        Raises:
            SearchError: If search operation fails
        """
        top_k = top_k or self.config.top_k
        
        try:
            logger.debug(f"Executing vector search (top_k={top_k})")
            
            # Create vectorized query
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top_k,
                fields=self.config.vector_field
            )
            
            # Execute search
            results = self.client.search(
                search_text=None,  # Pure vector search
                vector_queries=[vector_query],
                select=self.RETURN_FIELDS,
                filter=filter_expression,
                top=top_k
            )
            
            # Convert to list of dicts
            documents = []
            for doc in results:
                # Convert to dict and add score
                doc_dict = dict(doc)
                documents.append(doc_dict)
            
            logger.info(f"Vector search returned {len(documents)} results (before context expansion)")
            
            # Expand with sequential context if enabled
            if include_sequential_context and documents:
                documents = self.get_sequential_context(documents)
                logger.info(f"After sequential context expansion: {len(documents)} results")
            
            return documents
            
        except AzureError as e:
            error_msg = f"Azure Search error: {str(e)}"
            logger.error(error_msg)
            raise SearchError(error_msg, details={"top_k": top_k})
        
        except Exception as e:
            error_msg = f"Unexpected error during search: {str(e)}"
            logger.error(error_msg)
            raise SearchError(error_msg)
    
    def hybrid_search(
        self,
        query_text: str,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filter_expression: Optional[str] = None,
        include_sequential_context: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (text + vector) with optional sequential context expansion
        
        Args:
            query_text: Text query for keyword search
            query_embedding: Query vector for semantic search
            top_k: Number of results to return
            filter_expression: OData filter expression
            include_sequential_context: If True, expand results with document siblings
            
        Returns:
            List of search results
        """
        top_k = top_k or self.config.top_k
        
        try:
            logger.debug(f"Executing hybrid search: '{query_text}' (top_k={top_k})")
            
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top_k,
                fields=self.config.vector_field
            )
            
            results = self.client.search(
                search_text=query_text,  # Keyword search
                vector_queries=[vector_query],  # Vector search
                select=self.RETURN_FIELDS,
                filter=filter_expression,
                top=top_k
            )
            
            documents = [dict(doc) for doc in results]
            
            logger.info(f"Hybrid search returned {len(documents)} results (before context expansion)")
            
            # Expand with sequential context if enabled
            if include_sequential_context and documents:
                documents = self.get_sequential_context(documents)
                logger.info(f"After sequential context expansion: {len(documents)} results")
            
            return documents
            
        except AzureError as e:
            error_msg = f"Azure Search error: {str(e)}"
            logger.error(error_msg)
            raise SearchError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error during hybrid search: {str(e)}"
            logger.error(error_msg)
            raise SearchError(error_msg)
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document dictionary or None if not found
        """
        try:
            doc = self.client.get_document(key=doc_id)
            logger.debug(f"Retrieved document: {doc_id}")
            return dict(doc)
        except AzureError as e:
            logger.warning(f"Document not found: {doc_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {str(e)}")
            return None
    
    def get_document_count(self) -> int:
        """Get total number of documents in the index"""
        try:
            results = self.client.search(search_text="*", include_total_count=True, top=0)
            count = results.get_count()
            logger.debug(f"Index contains {count} documents")
            return count
        except Exception as e:
            logger.error(f"Error getting document count: {str(e)}")
            return 0
    
    def get_siblings_by_parent_id(
        self,
        parent_id: str,
        min_seq: Optional[float] = None,
        max_seq: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all sibling documents with the same parent_id, ordered by sequence_number
        
        Args:
            parent_id: The parent document ID to fetch siblings for
            min_seq: Optional minimum sequence_number (for context window)
            max_seq: Optional maximum sequence_number (for context window)
            
        Returns:
            List of sibling documents ordered by sequence_number
        """
        try:
            # Build filter expression
            filter_parts = [f"parent_id eq '{parent_id}'"]            
            if min_seq is not None:
                filter_parts.append(f"sequence_number ge {min_seq}")
            if max_seq is not None:
                filter_parts.append(f"sequence_number le {max_seq}")
            
            filter_expr = " and ".join(filter_parts)
            
            # Search with filter and order by sequence
            results = self.client.search(
                search_text="*",
                filter=filter_expr,
                order_by=["sequence_number asc"],
                select=self.RETURN_FIELDS,
                top=1000  # Max siblings to fetch
            )
            
            siblings = [dict(doc) for doc in results]
            logger.debug(f"Found {len(siblings)} siblings for parent_id={parent_id}")
            return siblings
            
        except Exception as e:
            logger.error(f"Error fetching siblings for parent_id={parent_id}: {str(e)}")
            return []
    
    def get_sequential_context(
        self,
        initial_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Expand search results with sequential context based on file type
        
        For PPTX/DOCX: Fetches all pages/slides of the document
        For CSV/XLSX: Fetches neighboring rows (±5 rows around match)
        For PDF: Fetches ±3 pages around match
        
        Includes overflow prevention:
        - MAX_TOTAL_DOCUMENTS: Global cap on total documents
        - MAX_PARENTS_TO_EXPAND: Limit on parent documents to expand
        - Priority sorting: Original matches first, then siblings
        
        Args:
            initial_results: Initial search results to expand
            
        Returns:
            Expanded results with sequential context, deduplicated and ordered
        """
        if not initial_results:
            return initial_results
        
        try:
            # Track original matched document IDs for priority sorting
            original_match_ids = set()
            expanded_docs = {}
            processed_parents = set()
            parents_expanded_count = 0
            
            for doc in initial_results:
                doc_id = doc.get("id")
                parent_id = doc.get("parent_id")
                file_name = doc.get("file", "").lower()
                sequence_num = doc.get("sequence_number", 1.0)
                
                # Add the original matched document and mark as original
                if doc_id:
                    expanded_docs[doc_id] = doc
                    original_match_ids.add(doc_id)
                
                # Skip if no parent_id or already processed this parent
                if not parent_id or parent_id in processed_parents:
                    continue
                
                # Check if we've hit the parent expansion limit
                if parents_expanded_count >= self.MAX_PARENTS_TO_EXPAND:
                    logger.debug(f"Reached MAX_PARENTS_TO_EXPAND limit ({self.MAX_PARENTS_TO_EXPAND}), skipping further expansion")
                    continue
                
                # Check if we've hit the total document limit
                if len(expanded_docs) >= self.MAX_TOTAL_DOCUMENTS:
                    logger.debug(f"Reached MAX_TOTAL_DOCUMENTS limit ({self.MAX_TOTAL_DOCUMENTS}), stopping expansion")
                    break
                
                # Determine file type
                file_ext = None
                for ext in ["pptx", "docx", "pdf", "xlsx", "csv"]:
                    if file_name.endswith(f".{ext}"):
                        file_ext = ext
                        break
                
                if not file_ext:
                    continue
                
                config = self.CONTEXT_CONFIG.get(file_ext, {"fetch_all": False, "window_size": 3})
                
                # Fetch siblings based on file type strategy
                if config.get("fetch_all", False):
                    # Fetch all siblings (for PPTX/DOCX)
                    siblings = self.get_siblings_by_parent_id(parent_id)
                    max_items = config.get("max_items", 50)
                    siblings = siblings[:max_items]  # Limit to prevent token overflow
                    logger.debug(f"Fetched all siblings for {file_name}: {len(siblings)} items (max: {max_items})")
                else:
                    # Fetch context window (for CSV/XLSX/PDF)
                    window_size = config.get("window_size", 5)
                    min_seq = sequence_num - window_size
                    max_seq = sequence_num + window_size
                    siblings = self.get_siblings_by_parent_id(parent_id, min_seq, max_seq)
                    logger.debug(f"Fetched context window for {file_name}: rows {min_seq:.0f}-{max_seq:.0f}, {len(siblings)} items")
                
                # Add siblings to expanded results (deduplicate by ID)
                # Respect the global document limit
                for sibling in siblings:
                    if len(expanded_docs) >= self.MAX_TOTAL_DOCUMENTS:
                        logger.debug(f"Hit MAX_TOTAL_DOCUMENTS ({self.MAX_TOTAL_DOCUMENTS}) during sibling expansion")
                        break
                    sibling_id = sibling.get("id")
                    if sibling_id and sibling_id not in expanded_docs:
                        expanded_docs[sibling_id] = sibling
                
                processed_parents.add(parent_id)
                parents_expanded_count += 1
            
            # Priority sorting: Original matches first, then siblings by parent_id/sequence
            result_list = list(expanded_docs.values())
            result_list.sort(key=lambda x: (
                0 if x.get("id") in original_match_ids else 1,  # Original matches first
                x.get("parent_id", ""),
                x.get("sequence_number", 0)
            ))
            
            logger.info(f"Sequential context expansion: {len(initial_results)} → {len(result_list)} documents "
                        f"(parents expanded: {parents_expanded_count}, max: {self.MAX_PARENTS_TO_EXPAND})")
            return result_list
            
        except Exception as e:
            logger.error(f"Error expanding sequential context: {str(e)}")
            return initial_results  # Return original results on error
