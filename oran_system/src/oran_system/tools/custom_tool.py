from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import pandas as pd
import io
import json


class CsvQueryInput(BaseModel):
    """Input schema for CSV Query Tool."""
    file_path: str = Field(..., description="Path to the CSV file to read")
    query: Optional[str] = Field(None, description="Pandas query expression to filter the data. If None, returns all data.")

class CsvQueryTool(BaseTool):
    name: str = "CSV Query Tool"
    description: str = (
        "Reads and queries O-RAN CSV files using pandas expressions. This tool helps you extract specific data "
        "from CSV files based on query conditions. Provide the file path and an optional pandas query, "
        "and it will return filtered data that matches your query criteria."
    )
    args_schema: Type[BaseModel] = CsvQueryInput

    def _run(self, file_path: str, query: Optional[str] = None) -> str:
        try:
            # Read the CSV file
            with open(file_path, 'r', newline='') as file:
                content = file.read()
                
            # Parse the CSV into a pandas DataFrame
            df = pd.read_csv(io.StringIO(content))
            
            # Replace NaN values with None for JSON serialization
            df = df.replace({"Null": None})
            
            # Apply the query if provided
            if query and query.strip():
                try:
                    # Execute the query (safely)
                    # This evaluates the pandas query expression
                    filtered_df = df.query(query)
                    
                    # Create response with filtered data
                    response = {
                        "file": file_path,
                        "query": query,
                        "column_names": list(df.columns),
                        "original_row_count": len(df),
                        "filtered_row_count": len(filtered_df),
                        "filtered_data": filtered_df.to_dict(orient='records')
                    }
                except Exception as query_error:
                    return f"Error executing pandas query: {str(query_error)}"
            else:
                # No query provided, return all data
                response = {
                    "file": file_path,
                    "column_names": list(df.columns),
                    "row_count": len(df),
                    "data": df.to_dict(orient='records')
                }
            
            # Return as JSON string for the agent to parse
            return json.dumps(response, indent=2)
            
        except Exception as e:
            return f"Error reading CSV file: {str(e)}"
