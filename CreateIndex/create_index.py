"""
VGIMT Chatbot - Create Azure AI Search Index
=============================================
Creates the vgimt-chatbot-index using the schema defined in index_schema.py

Usage:
    python create_index.py           # Create index (prompts if exists)
    python create_index.py --recreate # Delete and recreate index
"""
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any
from urllib import request, error

# Import our schema
from index_schema import get_index_schema, INDEX_NAME, print_schema_summary


def load_env_file():
    """Load .env file from parent directory."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("Warning: python-dotenv not installed. Using environment variables only.")
        return
    
    # Check current directory first, then parent directory
    env_path = Path(".env")
    if not env_path.exists():
        env_path = Path(__file__).parent.parent / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from: {env_path}")
    else:
        print("⚠️ No .env file found")


def create_index(endpoint: str, api_key: str, index_schema: dict, api_version: str = "2023-11-01"):
    """Create or update an index in Azure AI Search."""
    
    index_name = index_schema["name"]
    url = f"{endpoint.rstrip('/')}/indexes/{index_name}?api-version={api_version}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    # Convert schema to JSON
    data = json.dumps(index_schema).encode("utf-8")
    
    # Use PUT to create or update
    req = request.Request(url, data=data, headers=headers, method="PUT")
    
    try:
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"\n✅ Index '{index_name}' created/updated successfully!")
            return result
    except error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"\n❌ Error creating index: HTTP {e.code}")
        print(f"Details: {error_body}")
        raise


def check_index_exists(endpoint: str, api_key: str, index_name: str, api_version: str = "2023-11-01") -> bool:
    """Check if an index already exists."""
    
    url = f"{endpoint.rstrip('/')}/indexes/{index_name}?api-version={api_version}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    req = request.Request(url, headers=headers, method="GET")
    
    try:
        with request.urlopen(req) as response:
            return True
    except error.HTTPError as e:
        if e.code == 404:
            return False
        raise


def delete_index(endpoint: str, api_key: str, index_name: str, api_version: str = "2023-11-01"):
    """Delete an existing index."""
    
    url = f"{endpoint.rstrip('/')}/indexes/{index_name}?api-version={api_version}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    req = request.Request(url, headers=headers, method="DELETE")
    
    try:
        with request.urlopen(req) as response:
            print(f"✅ Index '{index_name}' deleted.")
            return True
    except error.HTTPError as e:
        if e.code == 404:
            print(f"ℹ️ Index '{index_name}' does not exist.")
            return False
        raise


def main():
    """Main function to create the index."""
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Create Azure AI Search index for VGIMT Chatbot"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete existing index and recreate it"
    )
    parser.add_argument(
        "--api-version",
        default="2023-11-01",
        help="Azure Search API version (default: 2023-11-01)"
    )
    args = parser.parse_args()
    
    # Load environment variables
    load_env_file()
    
    # Get credentials from environment
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    api_key = os.getenv("AZURE_SEARCH_API_KEY")
    api_version = os.getenv("AZURE_SEARCH_API_VERSION", args.api_version)
    
    if not endpoint or not api_key:
        print("❌ Error: Missing required environment variables")
        print("   Required: AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY")
        print("   Check your .env file")
        sys.exit(1)
    
    # Normalize endpoint
    endpoint = endpoint.rstrip("/")
    
    print("=" * 80)
    print("🚀 Azure AI Search - VGIMT Chatbot Index Creator")
    print("=" * 80)
    print(f"\n📍 Endpoint: {endpoint}")
    print(f"🔑 API Version: {api_version}")
    
    # Print schema summary
    print("\n")
    print_schema_summary()
    
    # Get the schema
    schema = get_index_schema()
    index_name = schema["name"]
    
    print(f"\n🔍 Checking if index '{index_name}' exists...")
    
    try:
        # Check if index exists
        exists = check_index_exists(endpoint, api_key, index_name, api_version)
        
        if exists:
            if args.recreate:
                print(f"⚠️  Recreate mode: Deleting existing index...")
                delete_index(endpoint, api_key, index_name, api_version)
            else:
                print(f"⚠️ Index '{index_name}' already exists.")
                response = input("Do you want to delete and recreate it? (yes/no): ").strip().lower()
                if response == "yes":
                    delete_index(endpoint, api_key, index_name, api_version)
                else:
                    print("ℹ️ Keeping existing index. Exiting.")
                    return
        else:
            print(f"ℹ️  Index '{index_name}' does not exist. Creating new...")
        
        # Create the index
        print(f"\n📝 Creating index '{index_name}'...")
        print(f"   📊 Fields: {len(schema['fields'])}")
        print(f"   🔍 Vector dimensions: 3072")
        print(f"   🧠 Semantic search: Enabled")
        
        create_index(endpoint, api_key, schema, api_version)
        
        print("\n" + "=" * 80)
        print("✨ SUCCESS! Index is ready for data upload")
        print("=" * 80)
        print("\n📝 Next Steps:")
        print("   1. Generate embeddings for your documents")
        print("   2. Upload documents to the index")
        print("   3. Test search queries in Azure Portal")
        print("   4. Configure your chatbot backend to use this index")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
