import os
import time
import dlt
from dlt.hub import run
from llama_index.core import SimpleDirectoryReader, PromptTemplate
from llama_index.readers.file import PyMuPDFReader

from pydantic import BaseModel, Field
from typing import List
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.bedrock_converse import BedrockConverse

def get_llm():
    if os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE"):
        print("Using AWS Bedrock LLM for extraction...")
        return BedrockConverse(model="global.anthropic.claude-sonnet-4-5-20250929-v1:0", temperature=0.1)
    elif os.environ.get("ANTHROPIC_API_KEY"):
        print("Using Anthropic Claude LLM for extraction...")
        return Anthropic(model="claude-3-5-sonnet-latest", temperature=0.1)
    elif os.environ.get("GOOGLE_API_KEY"):
        print("Using Gemini LLM for extraction...")
        return GoogleGenAI(model="gemini-2.5-flash", temperature=0.1)
    elif os.environ.get("OPENAI_API_KEY"):
        print("Using OpenAI LLM for extraction...")
        return OpenAI(model="gpt-4o-mini", temperature=0.1)
    else:
        raise ValueError("Please set AWS credentials, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or OPENAI_API_KEY to run the extraction.")

# --- GENERIC DOCUMENT EXTRACTION SCHEMA ---

class ExtractedEntity(BaseModel):
    key: str = Field(description="The name of the attribute or field extracted (e.g., 'Author', 'Total Amount', 'Invoice Number', 'Methodology').")
    value: str = Field(description="The extracted value for this attribute.")

class GenericDocument(BaseModel):
    document_type: str = Field(description="The type of document (e.g., Invoice, Research Paper, Resume, Contract, etc.)")
    title_or_id: str = Field(description="The main identifier, title, or reference number of the document.")
    summary: str = Field(description="A brief summary of what this document is about.")
    entities: List[ExtractedEntity] = Field(description="A list of key-value pairs representing the most important data points extracted from the document.")

@dlt.resource(name="documents", write_disposition="merge", primary_key="title_or_id")
def load_generic_pdfs(data_dir: str):
    llm = get_llm()
    if not os.path.exists(data_dir):
        print(f"Warning: Directory '{data_dir}' does not exist.")
        return
        
    pdf_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"Warning: No PDF files found in '{data_dir}'.")
        return

    total_loaded = 0
    for file_path in pdf_files:
        try:
            reader = SimpleDirectoryReader(
                input_files=[file_path],
                file_extractor={".pdf": PyMuPDFReader()}
            )
            documents = reader.load_data()
            print(f"Processing {os.path.basename(file_path)}...")
            
            # Combine up to 3 pages to avoid massive context but get enough info
            combined_text = ""
            for doc in documents[:3]:
                combined_text += doc.text + "\n"
            
            structured_data = llm.structured_predict(
                GenericDocument, 
                PromptTemplate(
                    "You are a universal document parser. Analyze the following document text.\n"
                    "Identify what type of document it is, summarize it, and extract the most relevant key entities into a key-value list.\n\n"
                    "Document Text:\n{text}"
                ),
                text=combined_text
            )
            
            doc_dict = structured_data.model_dump()
            doc_dict["source_file"] = os.path.basename(file_path)
            
            total_loaded += 1
            yield doc_dict
                
        except Exception as e:
            print(f"Error loading/extracting {file_path}: {e}")
            
        # Sleep to avoid hitting API rate limits on free tiers
        time.sleep(15)
            
    print(f"Finished extracting a total of {total_loaded} documents.")

@run.pipeline("generic_pdf_ingestion_pipeline")
def load_generic_pipeline():
    """Load generic PDFs from the data directory into Motherduck."""
    data_dir = "./data"
    os.makedirs(data_dir, exist_ok=True)
    
    pipeline = dlt.pipeline(
        pipeline_name="generic_pdf_ingestion_pipeline",
        destination="motherduck",
        dataset_name="universal_db_v2",
    )
    load_info = pipeline.run(load_generic_pdfs(data_dir))
    print(load_info)

if __name__ == "__main__":
    load_generic_pipeline()
