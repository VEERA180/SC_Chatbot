"""
SCORE Chatbot - Azure AI Search Index Schema Definition
========================================================

This schema defines the structure for the score-chatbot-index with:
- 20 fields for document metadata and content
  - Includes parent_id & sequence_number for sequential context
  - Includes row_data & column_headers for CSV/XLSX row-level indexing
- Vector search configuration (HNSW, 3072 dimensions)
- Semantic search configuration
"""

# Index name
INDEX_NAME = "scorechatbotqav1"

# Vector search configuration (2023-11-01 API format)
VECTOR_SEARCH_CONFIG = {
    "profiles": [
        {
            "name": "vector-profile",
            "algorithm": "hnsw-algorithm"
        }
    ],
    "algorithms": [
        {
            "name": "hnsw-algorithm",
            "kind": "hnsw",
            "hnswParameters": {
                "metric": "cosine",
                "m": 16,
                "efConstruction": 400,
                "efSearch": 300
            }
        }
    ]
}

# Semantic search configuration (2024-07-01 API format)
SEMANTIC_CONFIG = {
    "configurations": [
        {
            "name": "semantic-config",
            "prioritizedFields": {
                "titleField": {
                    "fieldName": "heading"
                },
                "prioritizedContentFields": [
                    {
                        "fieldName": "summary"
                    }
                ],
                "prioritizedKeywordsFields": [
                    {
                        "fieldName": "file"
                    },
                    {
                        "fieldName": "parent_title"
                    }
                ]
            }
        }
    ]
}

# Field definitions
FIELDS = [
    # ========== KEY FIELD ==========
    {
        "name": "id",
        "type": "Edm.String",
        "key": True,
        "searchable": False,
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    
    # ========== CONTENT FOR EMBEDDING ==========
    {
        "name": "content_for_embedding",
        "type": "Edm.String",
        "key": False,
        "searchable": True,
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": False  # Not needed in results, only for search
    },
    
    # ========== VECTOR FIELD ==========
    {
        "name": "content_vector",
        "type": "Collection(Edm.Single)",
        "searchable": True,
        "retrievable": False,  # Not needed in results
        "dimensions": 3072,
        "vectorSearchProfile": "vector-profile"
    },
    
    # ========== MAIN CONTENT FIELDS ==========
    {
        "name": "heading",
        "type": "Edm.String",
        "key": False,
        "searchable": True,
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    {
        "name": "text",
        "type": "Edm.String",
        "key": False,
        "searchable": True,
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    {
        "name": "summary",
        "type": "Edm.String",
        "key": False,
        "searchable": True,
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    
    # ========== FILE & DOCUMENT METADATA ==========
    {
        "name": "file",
        "type": "Edm.String",
        "key": False,
        "searchable": True,
        "filterable": True,
        "facetable": True,
        "sortable": False,
        "retrievable": True
    },
    {
        "name": "page",
        "type": "Edm.Int32",
        "key": False,
        "searchable": False,
        "filterable": True,
        "facetable": False,
        "sortable": True,
        "retrievable": True
    },
    
    # ========== SEQUENTIAL CONTEXT FIELDS ==========
    {
        "name": "parent_id",
        "type": "Edm.String",
        "key": False,
        "searchable": False,
        "filterable": True,  # For querying all pages of same document
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    {
        "name": "sequence_number",
        "type": "Edm.Double",
        "key": False,
        "searchable": False,
        "filterable": True,
        "facetable": False,
        "sortable": True,  # For ordering pages sequentially
        "retrievable": True
    },
    
    # ========== ROW-LEVEL INDEXING FIELDS (CSV/XLSX) ==========
    {
        "name": "row_data",
        "type": "Edm.String",
        "key": False,
        "searchable": True,  # Searchable for row-level queries
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    {
        "name": "column_headers",
        "type": "Edm.String",
        "key": False,
        "searchable": True,  # Searchable to match column names
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    {
        "name": "parent_title",
        "type": "Edm.String",
        "key": False,
        "searchable": True,
        "filterable": True,
        "facetable": True,
        "sortable": True,
        "retrievable": True
    },
    {
        "name": "total_pages",
        "type": "Edm.Int32",
        "key": False,
        "searchable": False,
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    {
        "name": "document_location",
        "type": "Edm.String",
        "key": False,
        "searchable": False,
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    {
        "name": "URL",
        "type": "Edm.String",
        "key": False,
        "searchable": False,
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    {
        "name": "source",
        "type": "Edm.String",
        "key": False,
        "searchable": False,
        "filterable": True,
        "facetable": True,
        "sortable": False,
        "retrievable": True
    },
    
    # ========== ADDITIONAL CONTENT FIELDS ==========
    {
        "name": "numbered_steps",
        "type": "Edm.String",
        "key": False,
        "searchable": True,
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    {
        "name": "screenshot_description",
        "type": "Edm.String",
        "key": False,
        "searchable": True,
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    },
    {
        "name": "tables",
        "type": "Edm.String",
        "key": False,
        "searchable": True,  # Too large to search effectively
        "filterable": False,
        "facetable": False,
        "sortable": False,
        "retrievable": True
    }
]


def get_index_schema():
    """Return the complete index schema as a dictionary."""
    return {
        "name": INDEX_NAME,
        "fields": FIELDS,
        "vectorSearch": VECTOR_SEARCH_CONFIG,
        "semantic": SEMANTIC_CONFIG
    }


def print_schema_summary():
    """Print a summary of the schema."""
    print("=" * 60)
    print(f"Index Name: {INDEX_NAME}")
    print("=" * 60)
    print(f"\nTotal Fields: {len(FIELDS)}")
    print("\nField Summary:")
    print("-" * 80)
    print(f"{'Field':<25} {'Type':<20} {'Search':<8} {'Filter':<8} {'Facet':<8} {'Retrieve':<8}")
    print("-" * 80)
    
    for field in FIELDS:
        name = field['name']
        ftype = field['type'].replace('Edm.', '').replace('Collection(Single)', 'Vector')
        search = '✅' if field.get('searchable', False) else '❌'
        filt = '✅' if field.get('filterable', False) else '❌'
        facet = '✅' if field.get('facetable', False) else '❌'
        retrieve = '✅' if field.get('retrievable', False) else '❌'
        
        print(f"{name:<25} {ftype:<20} {search:<8} {filt:<8} {facet:<8} {retrieve:<8}")
    
    print("\n" + "=" * 60)
    print("Vector Search: HNSW (3072 dimensions, cosine metric)")
    print("Semantic Config: heading (title), summary (content), file & parent_title (keywords)")
    print("=" * 60)


if __name__ == "__main__":
    print_schema_summary()
