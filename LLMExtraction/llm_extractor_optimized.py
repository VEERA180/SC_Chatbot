"""
LLM-based Document Extraction (Optimized)
Uses GPT-5 to extract structured content from PPTX, DOCX, PDF, Excel, CSV files.
"""

import os
import json
import base64
import glob
import requests
from typing import List, Dict, Any, Optional
from pptx import Presentation
from docx import Document
from dotenv import load_dotenv

load_dotenv()


class LLMDocumentExtractor:
    """
    Uses LLM to extract clean, accurate text from documents.
    Supports: PPTX, DOCX, PDF, Excel, CSV
    """
    
    def __init__(self, output_dir: str = None):
        self.llm_endpoint = os.getenv("LLM_NEW_ENDPOINT")
        self.llm_key = os.getenv("LLM_KEY")
        self.llm_model = os.getenv("LLM_MODEL")
        self.output_dir = output_dir or os.getenv("OUTPUT_DIR", "ExtractedData")
        self.sharepoint_forms = "https://volvogroup.sharepoint.com/sites/coll-score-global/Shared%20Documents/Forms/All%20Documents.aspx?csf=1&web=1&e=OVtfgx%2F&FolderCTID=0x01200071B1606811A6EB43B56C24533A15EE8A&id=%2Fsites%2Fcoll%2Dscore%2Dglobal%2FShared%20Documents%2FSCORE%20Users"
    
    # ==================== LLM API METHODS ====================
    
    def _call_llm(self, messages: List[Dict], max_tokens: int = 5000, timeout: int = 60) -> str:
        """Unified LLM API call method."""
        headers = {"Content-Type": "application/json", "api-key": self.llm_key}
        payload = {"messages": messages, "max_completion_tokens": max_tokens, "temperature": 1}
        if self.llm_model:
            payload["model"] = self.llm_model
        
        response = requests.post(self.llm_endpoint, headers=headers, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        raise Exception(f"LLM API error: {response.status_code} - {response.text}")
    
    def _call_llm_vision(self, image_base64: str, prompt: str, context: str = "") -> str:
        """Call GPT-5 Vision API with an image."""
        system_prompt = """You are a precise document text extractor for instructional presentations.
Extract the INSTRUCTIONAL content from slides that may contain screenshots.

RULES:
1. Extract INSTRUCTIONAL text - steps/instructions the author wrote
2. DO NOT extract text from UI screenshots unless referenced in instructions
3. Preserve exact wording - do not paraphrase
4. Note numbered steps (1, 2, 3) with arrows as KEY instructions

Return JSON:
{
    "heading": "Main title/heading (if any)",
    "text": "Main instructional text exactly as shown",
    "numbered_steps": ["1. First...", "2. Second..."],
    "screenshot_description": "What application/screen is shown (1 line)"
}"""
        
        user_content = [
            {"type": "text", "text": f"{prompt}\n\nSlide text elements:\n{context}" if context else prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}", "detail": "high"}}
        ]
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        return self._call_llm(messages, max_tokens=2000)
    
    def _call_llm_text(self, text: str, prompt: str) -> str:
        """Call GPT-5o with text content."""
        system_prompt = """You are a precise document text extractor. Structure the given text content.

RULES:
1. Use ONLY the text provided - do not add content
2. DO NOT paraphrase or modify the text
3. Preserve exact wording and formatting

Return JSON:
{
    "heading": "Main title/heading (if identifiable)",
    "text": "Main body text"
}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{prompt}\n\nDocument content:\n{text}"}
        ]
        return self._call_llm(messages)
    
    def _analyze_image(self, image_base64: str, context: str = "") -> str:
        """Analyze an image using GPT-5. Returns concise summary."""
        system_prompt = """Analyze this image from a document instruction guide.
Provide a CONCISE summary (4-6 sentences):
1. What the image shows (application/screen)
2. Key actions highlighted (red boxes, arrows, markers)
3. Important visible text/instructions
Return ONLY plain text summary."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": f"Summarize this image. Context: {context}" if context else "Summarize this image."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}", "detail": "high"}}
            ]}
        ]
        
        try:
            return self._call_llm(messages, max_tokens=300).strip()
        except:
            return ""
    
    # ==================== HELPER METHODS ====================
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract JSON."""
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        return response.strip()
    
    def _parse_llm_json(self, response: str, fallback: Dict = None) -> Dict:
        """Parse LLM response as JSON with fallback."""
        try:
            return json.loads(self._clean_json_response(response))
        except json.JSONDecodeError:
            return fallback or {}
    
    def _build_record(self, heading: str, text: str, file_name: str, page: int, 
                      metadata: Dict, tables: List = None, **extras) -> Dict:
        """Build a standardized output record."""
        record = {
            "heading": heading,
            "text": text,
            "tables": tables or [],
            "file": file_name,
            "page": page,
            "document_location": metadata.get("path", ""),
            "URL": self.sharepoint_forms,
            "source": "SCORE"
        }
        record.update(extras)
        return record
    
    def _build_summary(self, heading: str = "", text: str = "", 
                       steps: List[str] = None, screenshot_desc: str = "") -> str:
        """Build summary string from components."""
        parts = []
        if heading:
            parts.append(heading)
        if text:
            parts.append(text)
        if steps:
            parts.append("Steps: " + ". ".join(steps))
        if screenshot_desc:
            parts.append(f"[Screenshot: {screenshot_desc}]")
        return ". ".join(parts) if parts else ""
    
    # ==================== PPTX EXTRACTION ====================
    
    def extract_pptx(self, pptx_path: str, metadata: Dict) -> List[Dict]:
        """Extract content from PPTX using LLM."""
        results = []
        prs = Presentation(pptx_path)
        file_name = os.path.basename(pptx_path)
        total_slides = len(prs.slides)
        
        print(f"Processing PPTX: {file_name} ({total_slides} slides)")
        
        # Get parent_title from first slide (skip short text like slide numbers)
        parent_title = os.path.splitext(file_name)[0]  # Default to filename
        if prs.slides:
            first_slide = prs.slides[0]
            for shape in first_slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text = shape.text.strip()
                    # Skip if it's just a number or very short text (likely slide number)
                    if len(text) > 3 and not text.isdigit():
                        parent_title = text.split('\n')[0][:100]  # First line, max 100 chars
                        break
        
        for slide_idx, slide in enumerate(prs.slides):
            slide_num = slide_idx + 1
            print(f"  Slide {slide_num}/{total_slides}...", end=" ")
            
            # Extract raw text
            raw_text = "\n".join(shape.text.strip() for shape in slide.shapes 
                                  if hasattr(shape, "text") and shape.text.strip())
            
            if not raw_text.strip():
                print("(empty, skipping)")
                continue
            
            # Check for images
            image_base64 = None
            for shape in slide.shapes:
                if shape.shape_type == 13:  # Picture
                    try:
                        image_base64 = base64.b64encode(shape.image.blob).decode('utf-8')
                        break
                    except:
                        pass
            
            try:
                # Use LLM to structure content
                if image_base64:
                    prompt = f"Extract INSTRUCTIONAL content from slide {slide_num} of '{file_name}'."
                    llm_response = self._call_llm_vision(image_base64, prompt, raw_text)
                else:
                    prompt = f"Structure slide {slide_num} content from '{file_name}'."
                    llm_response = self._call_llm_text(raw_text, prompt)
                
                extracted = self._parse_llm_json(llm_response, {"heading": "", "text": raw_text})
                
                heading = extracted.get("heading", "")
                text = extracted.get("text", raw_text)
                steps = extracted.get("numbered_steps", [])
                screenshot_desc = extracted.get("screenshot_description", "") if image_base64 else ""
                
                record = self._build_record(heading, text, file_name, slide_num, metadata,
                                            tables=extracted.get("tables", []))
                
                # Add parent context
                record["parent_title"] = parent_title
                record["total_pages"] = total_slides
                
                if steps:
                    record["numbered_steps"] = steps
                if screenshot_desc:
                    record["screenshot_description"] = screenshot_desc
                
                record["summary"] = self._build_summary(heading, text, steps, screenshot_desc)
                results.append(record)
                print("done")
                
            except Exception as e:
                print(f"error: {e}")
                record = self._build_record("", raw_text, file_name, slide_num, metadata)
                record["summary"] = raw_text
                results.append(record)
        
        return results
    
    # ==================== DOCX EXTRACTION ====================
    
    def extract_docx(self, docx_path: str, metadata: Dict) -> List[Dict]:
        """Extract content from DOCX using LLM to split into sections."""
        from docx.oxml.ns import qn
        
        results = []
        doc = Document(docx_path)
        file_name = os.path.basename(docx_path)
        
        print(f"Processing DOCX: {file_name}")
        
        # Extract all paragraphs and tables
        all_paragraphs = []
        all_tables = []
        
        for element in doc.element.body:
            if element.tag.endswith('p'):
                para_text = "".join(node.text for node in element.iter() 
                                    if node.tag.endswith('t') and node.text)
                if para_text.strip():
                    all_paragraphs.append(para_text.strip())
            
            elif element.tag.endswith('tbl'):
                table_data = []
                for row in element.iter():
                    if row.tag.endswith('tr'):
                        row_data = []
                        for cell in row.iter():
                            if cell.tag.endswith('tc'):
                                cell_text = "".join(t.text for t in cell.iter() 
                                                   if t.tag.endswith('t') and t.text)
                                row_data.append(cell_text.strip())
                        if row_data:
                            table_data.append(row_data)
                if table_data:
                    all_tables.append(table_data)
        
        full_text = "\n".join(all_paragraphs)
        print(f"  Extracted {len(all_paragraphs)} paragraphs, {len(all_tables)} tables")
        
        # Use LLM to split into sections
        print("  Using LLM to identify sections...")
        sections = self._llm_split_sections(full_text, file_name)
        
        if not sections:
            sections = [{"heading": file_name, "text": full_text}]
        
        total_sections = len(sections)
        print(f"  Found {total_sections} sections")
        
        # Get parent_title from first section or file name
        parent_title = sections[0].get("heading", "") if sections else file_name
        if not parent_title:
            parent_title = os.path.splitext(file_name)[0]
        
        # Build results
        for idx, section in enumerate(sections, 1):
            record = self._build_record(
                section.get("heading", ""),
                section.get("text", ""),
                file_name, idx, metadata
            )
            # Add parent context
            record["parent_title"] = parent_title
            record["total_pages"] = total_sections
            results.append(record)
        
        # Add tables to last section
        if all_tables and results:
            results[-1]["tables"] = all_tables
        
        print(f"  Extracted {len(results)} sections")
        return results
    
    def _llm_split_sections(self, text: str, file_name: str) -> List[Dict]:
        """Use LLM to split document into logical sections."""
        # Truncate if too long
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n... [truncated]"
        
        prompt = f"""Analyze and split this document into logical sections.

Document: {file_name}

RULES:
1. Each section: "heading" (topic/question) and "text" (content/answer)
2. Main topics like "Support", "Access" are headings
3. Questions like "How do I get support?" are headings
4. Preserve ALL text exactly - do not summarize
5. Do not include numbering unless in original text

Return JSON array:
[{{"heading": "Topic/Question", "text": "Answer/content"}}]

DOCUMENT TEXT:
{text}

Return ONLY the JSON array."""

        messages = [
            {"role": "system", "content": "Split documents into sections. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._call_llm(messages, max_tokens=16000, timeout=120)
            return json.loads(self._clean_json_response(response))
        except Exception as e:
            print(f"    LLM error: {e}")
            return []
    
    # ==================== PDF EXTRACTION ====================
    
    def extract_pdf(self, pdf_path: str, metadata: Dict) -> List[Dict]:
        """Extract content from PDF using PyMuPDF + LLM for images."""
        import fitz
        
        results = []
        file_name = os.path.basename(pdf_path)
        
        print(f"Processing PDF: {file_name}")
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            print(f"  Total pages: {total_pages}")
            
            # Get parent_title from first page text or file name
            parent_title = os.path.splitext(file_name)[0]  # Default to filename
            if doc and len(doc) > 0:
                first_page_text = doc[0].get_text("text").strip()
                if first_page_text:
                    # Get first meaningful line (skip short text/page numbers)
                    for line in first_page_text.split('\n'):
                        line = line.strip()
                        if len(line) > 3 and not line.isdigit():
                            parent_title = line[:100]  # Max 100 chars
                            break
            
            images_dir = os.path.join(self.output_dir, "pdf_images")
            os.makedirs(images_dir, exist_ok=True)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_number = page_num + 1
                print(f"  Page {page_number}/{total_pages}...", end=" ")
                
                page_text = page.get_text("text").strip()
                tables = self._extract_pdf_tables(page)
                
                # Extract and analyze images
                image_summaries = []
                for img_idx, img_info in enumerate(page.get_images(full=True)):
                    try:
                        base_image = doc.extract_image(img_info[0])
                        img_base64 = base64.b64encode(base_image["image"]).decode('utf-8')
                        
                        # Save image
                        img_filename = f"{os.path.splitext(file_name)[0]}_p{page_number}_img{img_idx+1}.{base_image['ext']}"
                        with open(os.path.join(images_dir, img_filename), "wb") as f:
                            f.write(base_image["image"])
                        
                        summary = self._analyze_image(img_base64, f"PDF page {page_number}")
                        if summary:
                            image_summaries.append(summary)
                    except:
                        pass
                
                if image_summaries:
                    print(f"({len(image_summaries)} images)", end=" ")
                
                # Structure text with LLM
                heading, text = "", page_text
                if page_text and len(page_text) > 50:
                    try:
                        prompt = f"Structure PDF page {page_number} from '{file_name}'. Preserve ALL text."
                        extracted = self._parse_llm_json(self._call_llm_text(page_text, prompt))
                        heading = extracted.get("heading", "")
                        text = extracted.get("text", page_text)
                    except:
                        pass
                
                record = self._build_record(heading, text, file_name, page_number, metadata, tables)
                record["parent_title"] = parent_title
                record["total_pages"] = total_pages
                
                if image_summaries:
                    record["image_summary"] = image_summaries
                
                # Build summary with images
                summary_parts = [p for p in [heading, text] if p]
                if image_summaries:
                    summary_parts.append(f"[Screenshot: {' | '.join(image_summaries)}]")
                record["summary"] = ". ".join(summary_parts) if summary_parts else ""
                
                results.append(record)
                print("done")
            
            doc.close()
            
        except Exception as e:
            print(f"  Error: {e}")
            error_text = f"Failed to process PDF: {e}"
            record = self._build_record("Error", error_text, file_name, 1, metadata)
            record["parent_title"] = os.path.splitext(file_name)[0]
            record["total_pages"] = 0
            record["summary"] = f"Error. {error_text}"
            results.append(record)
        
        return results
    
    def _extract_pdf_tables(self, page) -> List[List[List[str]]]:
        """Extract tables from PDF page."""
        tables = []
        try:
            for block in page.get_text("dict")["blocks"]:
                if "lines" in block and len(block["lines"]) > 1:
                    rows = []
                    for line in block["lines"]:
                        cells = [span.get("text", "").strip() for span in line.get("spans", []) 
                                if span.get("text", "").strip()]
                        if cells:
                            rows.append(cells)
                    
                    if len(rows) > 1:
                        col_counts = [len(r) for r in rows]
                        if max(col_counts) > 1 and min(col_counts) == max(col_counts):
                            tables.append(rows)
        except:
            pass
        return tables
    
    # ==================== EXCEL EXTRACTION ====================
    
    def extract_excel(self, excel_path: str, metadata: Dict) -> List[Dict]:
        """Extract content from Excel files."""
        import pandas as pd
        from openpyxl import load_workbook
        
        results = []
        file_name = os.path.basename(excel_path)
        
        print(f"Processing Excel: {file_name}")
        
        try:
            wb = load_workbook(excel_path, read_only=True, data_only=True)
            sheet_names = wb.sheetnames
            wb.close()
            
            total_sheets = len(sheet_names)
            parent_title = os.path.splitext(file_name)[0]  # Use filename as parent title
            
            print(f"  Sheets: {sheet_names}")
            
            for sheet_idx, sheet_name in enumerate(sheet_names):
                print(f"  Sheet '{sheet_name}'...", end=" ")
                
                try:
                    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
                    
                    if df.empty:
                        print("(empty)")
                        continue
                    
                    table_data = [[str(c) if pd.notna(c) else "" for c in row] for _, row in df.iterrows()]
                    
                    record = self._build_record(
                        sheet_name,
                        f"Excel sheet '{sheet_name}' with {len(table_data)} rows, {len(df.columns)} columns.",
                        file_name, sheet_idx + 1, metadata, tables=[table_data]
                    )
                    record["sheet_name"] = sheet_name
                    record["parent_title"] = parent_title
                    record["total_pages"] = total_sheets
                    
                    # Add column headers
                    if table_data:
                        record["column_headers"] = [h for h in table_data[0] if h.strip()]
                    
                    results.append(record)
                    print(f"done ({len(table_data)} rows)")
                    
                except Exception as e:
                    print(f"error: {e}")
                    
        except Exception as e:
            print(f"  Error: {e}")
            record = self._build_record("Error", f"Failed to process Excel: {e}", file_name, 1, metadata)
            record["parent_title"] = os.path.splitext(file_name)[0]
            record["total_pages"] = 0
            results.append(record)
        
        return results
    
    # ==================== CSV EXTRACTION ====================
    
    def extract_csv(self, csv_path: str, metadata: Dict) -> List[Dict]:
        """Extract content from CSV files."""
        import pandas as pd
        
        results = []
        file_name = os.path.basename(csv_path)
        
        print(f"Processing CSV: {file_name}")
        
        try:
            # Try different encodings
            df = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding, header=None)
                    break
                except:
                    continue
            
            if df is None:
                raise Exception("Could not read CSV with any encoding")
            
            print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
            
            table_data = [[str(c) if pd.notna(c) else "" for c in row] for _, row in df.iterrows()]
            
            parent_title = os.path.splitext(file_name)[0]
            
            record = self._build_record(
                os.path.splitext(file_name)[0],
                f"CSV file with {len(table_data)} rows, {len(df.columns)} columns.",
                file_name, 1, metadata, tables=[table_data]
            )
            record["parent_title"] = parent_title
            record["total_pages"] = 1
            
            if table_data:
                record["column_headers"] = [h for h in table_data[0] if h.strip()]
            
            results.append(record)
            print(f"  Done ({len(table_data)} rows)")
            
        except Exception as e:
            print(f"  Error: {e}")
            record = self._build_record("Error", f"Failed to process CSV: {e}", file_name, 1, metadata)
            record["parent_title"] = os.path.splitext(file_name)[0]
            record["total_pages"] = 0
            results.append(record)
        
        return results


# ==================== FILE LOCATION MAPPER ====================

class FileLocationMapper:
    """Maps local file names to SharePoint paths using FileLocation.xlsx"""
    
    def __init__(self, filelocation_path: str):
        import pandas as pd
        df = pd.read_excel(filelocation_path)
        files_df = df[df['Item Type'] != 'Folder']
        
        self.file_map = {}
        for _, row in files_df.iterrows():
            name = row['Name']
            path = row['Path']
            self.file_map[name] = {
                "name": name,
                "path": f"{path}/{name}" if not path.endswith('/') else f"{path}{name}",
                "modified": row['Modified'],
                "modified_by": row['Modified By']
            }
    
    def get_metadata(self, file_name: str) -> Dict:
        """Get SharePoint metadata for a file."""
        # Exact match
        if file_name in self.file_map:
            return self.file_map[file_name]
        
        # Case-insensitive match
        for name, meta in self.file_map.items():
            if name.lower() == file_name.lower():
                return meta
        
        return {"name": file_name, "path": f"sites/colt-score-global/Shared Documents/SCORE Users/{file_name}"}


# ==================== MAIN EXTRACTION FUNCTION ====================

def get_output_filename(file_path: str, input_dir: str) -> str:
    """
    Generate unique output filename using folder prefix to handle duplicates.
    Example: Data/GTT/Guide.docx -> GTT_Guide_llm_extracted.json
    """
    file_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(file_name)[0]
    
    # Get relative path from input_dir
    rel_path = os.path.relpath(file_path, input_dir)
    parent_folder = os.path.dirname(rel_path)
    
    # If file is in a subfolder, add folder prefix
    if parent_folder:
        # Replace path separators with underscore and clean up
        folder_prefix = parent_folder.replace(os.sep, "_").replace("/", "_")
        return f"{folder_prefix}_{name_without_ext}_llm_extracted.json"
    else:
        return f"{name_without_ext}_llm_extracted.json"


def run_extraction(input_dir: str, output_dir: str, filelocation_path: str):
    """
    Run extraction on all supported files with resume capability.
    - Skips files that already have output JSON (resume logic)
    - Handles duplicate filenames with folder prefix
    - Creates combined JSON at the end
    """
    
    extractor = LLMDocumentExtractor(output_dir)
    mapper = FileLocationMapper(filelocation_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # Find files (exclude temp files)
    def find_files(pattern):
        return [f for f in glob.glob(os.path.join(input_dir, f"**/*.{pattern}"), recursive=True)
                if not os.path.basename(f).startswith('~$')]
    
    files = {
        'pptx': find_files('pptx'),
        'docx': find_files('docx'),
        'pdf': find_files('pdf'),
        'xlsx': find_files('xlsx'),
        'xls': [f for f in find_files('xls') if not f.endswith('.xlsx')],
        'csv': find_files('csv')
    }
    
    # Count total files
    total_files = sum(len(f) for f in files.values())
    
    print(f"\n{'='*60}")
    print("LLM Document Extraction (with Resume Support)")
    print(f"{'='*60}")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Total files found: {total_files}")
    print(f"  - PPTX: {len(files['pptx'])}")
    print(f"  - DOCX: {len(files['docx'])}")
    print(f"  - PDF:  {len(files['pdf'])}")
    print(f"  - Excel: {len(files['xlsx']) + len(files['xls'])}")
    print(f"  - CSV:  {len(files['csv'])}")
    print(f"{'='*60}\n")
    
    # Process files by type
    extractors = {
        'pptx': extractor.extract_pptx,
        'docx': extractor.extract_docx,
        'pdf': extractor.extract_pdf,
        'xlsx': extractor.extract_excel,
        'xls': extractor.extract_excel,
        'csv': extractor.extract_csv
    }
    
    processed_count = 0
    skipped_count = 0
    failed_count = 0
    all_results = []
    
    for file_type, extract_func in extractors.items():
        for file_path in files[file_type]:
            file_name = os.path.basename(file_path)
            output_filename = get_output_filename(file_path, input_dir)
            output_file = os.path.join(output_dir, output_filename)
            
            # RESUME LOGIC: Check if output already exists
            if os.path.exists(output_file):
                print(f"⏭️  SKIP (exists): {file_name}")
                skipped_count += 1
                
                # Load existing results for combined JSON
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        existing_results = json.load(f)
                        all_results.extend(existing_results)
                except:
                    pass
                continue
            
            # Process file
            try:
                metadata = mapper.get_metadata(file_name)
                print(f"\n📄 Processing ({processed_count + skipped_count + 1}/{total_files}): {file_name}")
                
                results = extract_func(file_path, metadata)
                
                # Save individual results immediately
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
                print(f"  ✅ Saved: {output_filename}")
                
                all_results.extend(results)
                processed_count += 1
                
            except Exception as e:
                print(f"  ❌ FAILED: {file_name} - {e}")
                failed_count += 1
                continue
    
    # Save combined JSON
    combined_file = os.path.join(output_dir, "all_extracted_combined.json")
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n{'='*60}")
    print("Extraction Complete!")
    print(f"{'='*60}")
    print(f"  ✅ Processed: {processed_count}")
    print(f"  ⏭️  Skipped (already done): {skipped_count}")
    print(f"  ❌ Failed: {failed_count}")
    print(f"  📊 Total records: {len(all_results)}")
    print(f"{'='*60}")
    print(f"📁 Combined JSON: {combined_file}")
    print(f"{'='*60}")
    
    return all_results


if __name__ == "__main__":
    workspace = r"c:\Users\a439034\Desktop\Score_UAT_Prod"
    
    # Change to Data/ folder for production
    run_extraction(
        input_dir=os.path.join(workspace, "Data"),
        output_dir=os.path.join(workspace, "ExtractedData", "llm_output"),
        filelocation_path=os.path.join(workspace,"Data" ,"FileLocation.xlsx")
    )
