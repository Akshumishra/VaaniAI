from src.backend.llm.agent_core.tools import Tool
from src.backend.llm.agent_core.arg_schema import ArgsSchema
from src.backend.llm.rag.pdf_store import pdf_store

class PDFSearchSchema:
    args = [
        ("query", ArgsSchema(type=str, description="The specific topic or question to search for in the PDF."))
    ]

def execute_pdf_search(query: str) -> dict:
    """Searches the currently uploaded PDF document."""
    results = pdf_store.search(query)
    
    # Check for empty results by seeing if it returned the error string or empty list
    is_empty = not results or (isinstance(results[0], str) and "No highly relevant" in results[0])
    
    return {
        "status": "success" if not is_empty else "error",
        "results": results
    }

pdf_search_tool = Tool(
    func=execute_pdf_search,
    description="Search the currently uploaded PDF document for relevant information. The tool returns text chunks along with their 'source' (filename) and 'page'. You MUST use this metadata to cite the source and page number in your response.",
    args_schema=PDFSearchSchema
)
