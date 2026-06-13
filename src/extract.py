import pandas as pd
import os

def extract_csv(file_path: str) -> pd.DataFrame:
    """
    Ingests the raw CSV file into a pandas DataFrame.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Target clinical trials file not found at: {file_path}")
        
    try:
        # Read all columns as object/string initially to prevent pandas from 
        # making incorrect type inferences before Pydantic validation
        return pd.read_csv(file_path, dtype=str)
    except Exception as e:
        raise RuntimeError(f"Unexpected error while reading CSV file: {e}")