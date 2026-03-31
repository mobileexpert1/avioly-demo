from __future__ import annotations
import pandas as pd
from pathlib import Path
from ..core.types import RetrievedChunk

def build_excel_chunks(collection_id: str, excel_path: Path) -> list[RetrievedChunk]:
    """
    Parses an Excel file and converts each sheet into a text chunk.
    """
    chunks = []
    try:
        # Load all sheets
        excel_data = pd.read_excel(excel_path, sheet_name=None)
        
        for sheet_name, df in excel_data.items():
            if df.empty:
                continue
                
            # Convert dataframe to a markdown table string for better LLM readability
            sheet_text = df.to_markdown(index=False)
            
            # Create a descriptive header for the LLM
            content = f"Document: {excel_path.name}\nSheet: {sheet_name}\n\n{sheet_text}"
            
            chunks.append(
                RetrievedChunk(
                    source_id=collection_id,
                    document_name=excel_path.name,
                    chunk_index=len(chunks),
                    text=content,
                    metadata={"sheet_name": sheet_name, "type": "excel"}
                )
            )
    except Exception as e:
        print(f"Error parsing Excel file {excel_path}: {e}")
        
    return chunks
