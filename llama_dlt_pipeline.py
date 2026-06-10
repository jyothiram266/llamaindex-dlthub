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

# Define the structure we want to extract with descriptions to help the LLM understand different layouts
class InvoiceItem(BaseModel):
    description: str = Field(description="The name or description of the product or service billed.")
    qty: int = Field(description="The quantity or hours billed. Default to 1 if not explicitly stated.")
    unit_price: float = Field(description="The price per single unit or hourly rate.")

class InvoiceData(BaseModel):
    invoice_number: str = Field(description="The unique identifier for the invoice. Could be called Invoice ID, Reference Number, etc.")
    date: str = Field(description="The date the invoice was issued, normalized to YYYY-MM-DD format.")
    billed_to: str = Field(description="The name of the company or person being billed.")
    total_amount: float = Field(description="The final total amount due on the invoice.")
    items: List[InvoiceItem] = Field(description="A list of all individual line items billed on the invoice.")

@dlt.resource(name="invoices", write_disposition="replace", primary_key="invoice_number")
def load_pdfs(data_dir: str):
    """
    Reads PDFs from the given directory, extracts structured data using an LLM,
    and yields them as dicts. dlt will automatically turn the 'items' list into a child table!
    """
    if os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE"):
        print("Using AWS Bedrock LLM for extraction...")
        llm = BedrockConverse(model="global.anthropic.claude-sonnet-4-5-20250929-v1:0", temperature=0.1)
    elif os.environ.get("ANTHROPIC_API_KEY"):
        print("Using Anthropic Claude LLM for extraction...")
        llm = Anthropic(model="claude-3-5-sonnet-latest", temperature=0.1)
    elif os.environ.get("GOOGLE_API_KEY"):
        print("Using Gemini LLM for extraction...")
        llm = GoogleGenAI(model="gemini-2.5-flash", temperature=0.1)
    elif os.environ.get("OPENAI_API_KEY"):
        print("Using OpenAI LLM for extraction...")
        llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
    else:
        raise ValueError("Please set AWS credentials, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or OPENAI_API_KEY to run the extraction.")

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
            
            for doc in documents:
                # Use LlamaIndex to extract structured data from the raw text
                structured_data = llm.structured_predict(
                    InvoiceData, 
                    PromptTemplate("Extract the invoice details from the following text:\n\n{text}"),
                    text=doc.text
                )
                
                # Combine LLM extracted data with file metadata
                invoice_dict = structured_data.model_dump()
                invoice_dict["source_file"] = doc.metadata.get("file_name", "")
                
                
                total_loaded += 1
                yield invoice_dict
                
        except Exception as e:
            print(f"Error loading/extracting {file_path}: {e}")
            
        # Sleep to avoid hitting API rate limits on free tiers
        #time.sleep(15)
            
    print(f"Finished extracting a total of {total_loaded} invoices.")

@run.pipeline("pdf_ingestion_pipeline")
def load_pdfs_pipeline():
    """Load PDFs from the data directory into DuckDB/MotherDuck."""
    data_dir = "./data"
    
    # Ensure data dir exists
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"Loading PDFs from {data_dir}")
    print("NOTE: To connect to MotherDuck, set the following environment variable:")
    print("      export DESTINATION__MOTHERDUCK__CREDENTIALS='md:llamaindex?motherduck_token=<YOUR_TOKEN>'")
    print("      or add it to your .dlt/secrets.toml under [destination.motherduck]\n")
    
    pipeline = dlt.pipeline(
        pipeline_name="pdf_ingestion_pipeline",
        destination="motherduck",
        dataset_name="llama_index_data",
    )
    
    load_info = pipeline.run(load_pdfs(data_dir))
    print(load_info)

if __name__ == "__main__":
    load_pdfs_pipeline()
