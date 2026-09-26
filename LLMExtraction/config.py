"""
Configuration for VGIMT Data Extraction Pipeline
"""

# SharePoint URL mappings for each category
# SHAREPOINT_BASE_URL = "https://volvogroup.sharepoint.com/sites/coll-score-global/"

CATEGORY_URL_MAPPING = {
    "Fieldglass": f"https://volvogroup.sharepoint.com/sites/coll-score-global/Shared%20Documents/Forms/All%20Documents.aspx?id=%2Fsites%2Fcoll%2Dscore%2Dglobal%2FShared%20Documents%2FSCORE%20Users%2FFieldglass&viewid=208a6df7%2D8470%2D4a24%2Da3f9%2D90fe652bf358&csf=1&FolderCTID=0x01200071B1606811A6EB43B56C24533A15EE8A",
    
    "Fiori": f"https://volvogroup.sharepoint.com/sites/coll-score-global/Shared%20Documents/Forms/All%20Documents.aspx?id=%2Fsites%2Fcoll%2Dscore%2Dglobal%2FShared%20Documents%2FSCORE%20Users%2FFiori&viewid=208a6df7%2D8470%2D4a24%2Da3f9%2D90fe652bf358&csf=1&FolderCTID=0x01200071B1606811A6EB43B56C24533A15EE8A",
    
    "Functional documentation": f" https://volvogroup.sharepoint.com/sites/coll-score-global/Shared%20Documents/Forms/All%20Documents.aspx?id=%2Fsites%2Fcoll%2Dscore%2Dglobal%2FShared%20Documents%2FSCORE%20Users%2FFunctional%20documentation&viewid=208a6df7%2D8470%2D4a24%2Da3f9%2D90fe652bf358&csf=1&FolderCTID=0x01200071B1606811A6EB43B56C24533A15EE8A",
    
    "GRC": f"https://volvogroup.sharepoint.com/sites/coll-score-global/Shared%20Documents/Forms/All%20Documents.aspx?id=%2Fsites%2Fcoll%2Dscore%2Dglobal%2FShared%20Documents%2FSCORE%20Users%2FGRC&viewid=208a6df7%2D8470%2D4a24%2Da3f9%2D90fe652bf358&csf=1&FolderCTID=0x01200071B1606811A6EB43B56C24533A15EE8A",
    
    "Process documentation": f"https://volvogroup.sharepoint.com/sites/coll-score-global/Shared%20Documents/Forms/All%20Documents.aspx?id=%2Fsites%2Fcoll%2Dscore%2Dglobal%2FShared%20Documents%2FSCORE%20Users%2FProcess%20documentation&viewid=208a6df7%2D8470%2D4a24%2Da3f9%2D90fe652bf358&csf=1&FolderCTID=0x01200071B1606811A6EB43B56C24533A15EE8A",
    "Score SAC Account": f"https://volvogroup.sharepoint.com/sites/coll-score-global/Shared%20Documents/Forms/All%20Documents.aspx?id=%2Fsites%2Fcoll%2Dscore%2Dglobal%2FShared%20Documents%2FSCORE%20Users%2FSCORE%20SAC%20Account&viewid=208a6df7%2D8470%2D4a24%2Da3f9%2D90fe652bf358&csf=1&FolderCTID=0x01200071B1606811A6EB43B56C24533A15EE8A",
    "Training": f"https://volvogroup.sharepoint.com/sites/coll-score-global/Shared%20Documents/Forms/All%20Documents.aspx?id=%2Fsites%2Fcoll%2Dscore%2Dglobal%2FShared%20Documents%2FSCORE%20Users%2FTraining&viewid=208a6df7%2D8470%2D4a24%2Da3f9%2D90fe652bf358&csf=1&FolderCTID=0x01200071B1606811A6EB43B56C24533A15EE8A",
    "WISE SAC Planning": f"https://volvogroup.sharepoint.com/sites/coll-score-global/Shared%20Documents/Forms/All%20Documents.aspx?id=%2Fsites%2Fcoll%2Dscore%2Dglobal%2FShared%20Documents%2FSCORE%20Users%2FWISE%20SAC%20Planning&viewid=208a6df7%2D8470%2D4a24%2Da3f9%2D90fe652bf358&csf=1&FolderCTID=0x01200071B1606811A6EB43B56C24533A15EE8A",
    "One Pager": f"https://volvogroup.sharepoint.com/:w:/r/sites/coll-score-global/_layouts/15/Doc.aspx?sourcedoc=%7B15E8C4EB-0C6F-4F67-BA20-8FD26CF62EF5%7D&file=One-Pager_User%20Manual.docx&action=default&mobileredirect=true",
    "SCORE New Fiori Timesheet User Manual.pptx": f"https://volvogroup.sharepoint.com/:p:/r/sites/coll-score-global/_layouts/15/Doc.aspx?sourcedoc=%7B12FE6EC5-DC96-4167-BC70-14698411B1CD%7D&file=SCORE%20New%20Fiori%20Timesheet%20User%20Manual.pptx&action=edit&mobileredirect=true",
    "BW reporting": f"https://volvogroup.sharepoint.com/sites/coll-score-global/Shared%20Documents/Forms/All%20Documents.aspx?id=%2Fsites%2Fcoll%2Dscore%2Dglobal%2FShared%20Documents%2FSCORE%20Users%2FTraining%2FBW%20reporting&viewid=208a6df7%2D8470%2D4a24%2Da3f9%2D90fe652bf358&csf=1&FolderCTID=0x01200071B1606811A6EB43B56C24533A15EE8AG",

}

# Supported file types
SUPPORTED_EXTENSIONS = {
    "pptx": "PowerPoint",
    "docx": "Word Document", 
    "xlsx": "Excel Spreadsheet",
    "csv": "CSV File",
    "pdf": "PDF Document",
    "msg": "Email Message",
    "docm": "Word Macro-Enabled Document"
}

# Content type mappings
CONTENT_TYPES = {
    "pptx": "slide",
    "docx": "document_section",
    "xlsx": "spreadsheet_data",
    "csv": "tabular_data",
    "pdf": "pdf_page",
    "msg": "email",
    "docm": "document_section"
}
