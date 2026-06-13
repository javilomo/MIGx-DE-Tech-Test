import os
import glob
import logging
from typing import List, Tuple

def extract_raw_xmls(directory_path: str) -> List[Tuple[str, str]]:
    """
    Scans the local source directory for XML files and reads their raw text content.
    Does not validate or parse the XML structure to strictly comply with Bronze guidelines.
    """
    
    # Look for all xml files in the raw folder
    search_pattern = os.path.join(directory_path, "*.xml")
    xml_files = glob.glob(search_pattern)
    
    if not xml_files:
        logging.warning(f"No XML files found in target directory: {directory_path}")
        return []
        
    raw_payloads = []
    for file_path in xml_files:
        try:
            file_name = os.path.basename(file_path)
            
            # Open with explicit UTF-8 encoding to avoid encoding issues with raw text blocks
            with open(file_path, 'r', encoding='utf-8') as file:
                raw_xml_content = file.read()
                raw_payloads.append((file_name, raw_xml_content))
                
        except Exception as e:
            # Fault tolerance: log individual file read failures but keep the pipeline moving
            logging.error(f"Critical error reading file {file_path}: {e}")
            
    return raw_payloads