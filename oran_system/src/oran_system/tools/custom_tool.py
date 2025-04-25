from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import pandas as pd
import io
import json


class CsvReaderInput(BaseModel):
    """Input schema for CSV Reader Tool."""
    file_path: str = Field(..., description="Path to the CSV file to read")

class CsvReaderTool(BaseTool):
    name: str = "CSV Reader Tool"
    description: str = (
        "Reads and properly structures O-RAN CSV files. This tool helps you get properly formatted "
        "data from CSV files. Provide the file path, and it will return a structured representation "
        "of the CSV data that you can analyze."
    )
    args_schema: Type[BaseModel] = CsvReaderInput

    def _run(self, file_path: str) -> str:
        try:
            # Read the CSV file
            with open(file_path, 'r', newline='') as file:
                content = file.read()
                
            # Parse the CSV
            df = pd.read_csv(io.StringIO(content))
            
            # Replace NaN values with None for JSON serialization
            df = df.replace({"Null": None})
            
            # Convert to records format for easy analysis
            records = df.to_dict(orient='records')
            
            # Create a response with metadata and records
            response = {
                "file": file_path,
                "column_names": list(df.columns),
                "row_count": len(records),
                "data": records
            }
            
            # Return as JSON string for the agent to parse
            return json.dumps(response, indent=2)
            
        except Exception as e:
            return f"Error reading CSV file: {str(e)}"
        
