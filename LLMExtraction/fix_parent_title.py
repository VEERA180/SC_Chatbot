"""
Fix parent_title and total_pages in the combined JSON file.
- parent_title = filename without extension
- total_pages = count of records with the same filename
"""

import json
import os
from collections import Counter

# Paths
combined_json_path = r"c:\Users\a439034\Desktop\VGIMT_ReactChatBot\ExtractedData\llm_output\all_extracted_combined.json"

print("Loading combined JSON...")
with open(combined_json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total records: {len(data)}")

# Step 1: Count total pages per file
file_counts = Counter(record.get("file", "") for record in data)
print(f"Unique files: {len(file_counts)}")

# Step 2: Update each record
updated_count = 0
for record in data:
    file_name = record.get("file", "")
    
    # Set parent_title to filename without extension
    if file_name:
        parent_title = os.path.splitext(file_name)[0]
    else:
        parent_title = "Unknown"
    
    # Set total_pages to count of records with same filename
    total_pages = file_counts.get(file_name, 1)
    
    # Update record
    record["parent_title"] = parent_title
    record["total_pages"] = total_pages
    updated_count += 1

print(f"Updated {updated_count} records")

# Step 3: Save updated JSON
print("Saving updated JSON...")
with open(combined_json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Done! Updated {combined_json_path}")

# Show sample
print("\n--- Sample record ---")
print(json.dumps(data[0], indent=2, ensure_ascii=False)[:500])
