"""
Fix URLs in combined JSON based on document_location folder mapping.
"""
import json

# Input/Output paths
INPUT_FILE = r"c:\Users\a439034\Desktop\VGIMT_ReactChatBot\ExtractedData\llm_output\all_extracted_combined.json"
OUTPUT_FILE = INPUT_FILE  # Overwrite same file

# Folder to URL mapping (first folder after "VGIMT solution/")
FOLDER_URL_MAP = {
    "BRS": "https://volvogroup.sharepoint.com/sites/unit-vgimt/VGIMT%20solution/Forms/AllItems.aspx?id=%2Fsites%2Funit%2Dvgimt%2FVGIMT%20solution%2FBRS&viewid=c978f8fd%2Da43d%2D48d0%2D93ae%2D81c49f316f09",
    "End User Instructions": "https://volvogroup.sharepoint.com/sites/unit-vgimt/VGIMT%20solution/Forms/AllItems.aspx?id=%2Fsites%2Funit%2Dvgimt%2FVGIMT%20solution%2FEnd%20User%20Instructions&viewid=c978f8fd%2Da43d%2D48d0%2D93ae%2D81c49f316f09",
    "Key User Documents (Edit Access)": "https://volvogroup.sharepoint.com/sites/unit-vgimt/VGIMT%20solution/Forms/AllItems.aspx?id=%2Fsites%2Funit%2Dvgimt%2FVGIMT%20solution%2FKey%20User%20Documents%20%28Edit%20Access%29&viewid=c978f8fd%2Da43d%2D48d0%2D93ae%2D81c49f316f09",
    "Key User Instructions": "https://volvogroup.sharepoint.com/sites/unit-vgimt/VGIMT%20solution/Forms/AllItems.aspx?id=%2Fsites%2Funit%2Dvgimt%2FVGIMT%20solution%2FKey%20User%20Instructions&viewid=c978f8fd%2Da43d%2D48d0%2D93ae%2D81c49f316f09",
    "Roll-Outs": "https://volvogroup.sharepoint.com/sites/unit-vgimt/VGIMT%20solution/Forms/AllItems.aspx?id=%2Fsites%2Funit%2Dvgimt%2FVGIMT%20solution%2FRoll%2DOuts&viewid=c978f8fd%2Da43d%2D48d0%2D93ae%2D81c49f316f09",
}

# Default fallback URL
DEFAULT_URL = "https://volvogroup.sharepoint.com/sites/unit-vgimt/VGIMT%20solution/Forms/AllItems.aspx"


def get_folder_from_path(document_location: str) -> str:
    """Extract first folder after 'VGIMT solution/' from document_location."""
    marker = "VGIMT solution/"
    if marker in document_location:
        after_marker = document_location.split(marker, 1)[1]
        # Get first folder (before next /)
        first_folder = after_marker.split("/")[0]
        return first_folder
    return ""


def get_url_for_record(record: dict) -> str:
    """Get the correct URL based on document_location."""
    doc_location = record.get("document_location", "")
    folder = get_folder_from_path(doc_location)
    
    # Return mapped URL or default
    return FOLDER_URL_MAP.get(folder, DEFAULT_URL)


def main():
    print("Loading combined JSON...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total records: {len(data)}")
    
    # Track changes per folder
    folder_counts = {}
    updated_count = 0
    
    for record in data:
        doc_location = record.get("document_location", "")
        folder = get_folder_from_path(doc_location)
        
        # Count by folder
        folder_counts[folder] = folder_counts.get(folder, 0) + 1
        
        # Update URL
        new_url = get_url_for_record(record)
        if record.get("URL") != new_url:
            record["URL"] = new_url
            updated_count += 1
    
    print(f"\nRecords by folder:")
    for folder, count in sorted(folder_counts.items()):
        mapped = "✅" if folder in FOLDER_URL_MAP else "⚠️ (default)"
        print(f"  {folder or '(empty)'}: {count} {mapped}")
    
    print(f"\nUpdated {updated_count} URLs")
    
    # Save
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("✅ Done!")


if __name__ == "__main__":
    main()
