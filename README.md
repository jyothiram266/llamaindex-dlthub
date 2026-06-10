# Invoice Extraction Pipeline: LlamaIndex + dltHub + MotherDuck

This project demonstrates an end-to-end data pipeline that extracts structured information from unstructured PDF invoices using Large Language Models (LLMs) and loads the normalized data into a cloud data warehouse for analytics.

## What is this demo for?

Many businesses receive invoices in unstructured formats (like PDFs). Manually entering this data into databases is tedious and error-prone. This demo automates this process by:
1. **Reading PDFs**: Loading invoice documents from a local directory.
2. **LLM Extraction**: Using an LLM to "read" the invoice and map its contents into a strongly-typed schema (e.g., extracting Invoice Number, Date, Billed To, and an array of individual Line Items).
3. **Data Loading**: Automatically taking that extracted structure, normalizing nested data (like line items) into relational tables, and pushing it to a robust data warehouse.

## Why these technologies?

- **LlamaIndex**: Provides the orchestration layer for interacting with LLMs. It handles parsing the PDF documents and provides a unified interface for structured data extraction across different LLM providers (Anthropic, Google, OpenAI, AWS Bedrock).
- **dlt (data load tool)**: A lightweight library for building data pipelines. Instead of writing custom code to handle schema creation, data typing, and flattening nested structures (like a list of items inside an invoice), `dlt` handles this automatically. It inspects the Python dictionaries yielded by our pipeline, creates the corresponding tables (including a child table for the invoice items), and loads the data efficiently.
- **MotherDuck**: A cloud-based, serverless DuckDB data warehouse. It's incredibly fast, easy to set up, and serves as our destination for the analytical data. You can query your loaded invoice data seamlessly using SQL.

## Prerequisites

- Python 3.12+
- `uv` package manager (recommended for fast virtual environment setup)
- An API Key from one of the supported LLM providers (Anthropic Claude, Google Gemini, OpenAI, or AWS Bedrock).
- A MotherDuck account and API Token.

## How to run it from scratch

### 1. Setup the Environment

First, make sure to install dependencies using `uv`:

```bash
# This will create a virtual environment and install dependencies defined in pyproject.toml
uv sync
```

### 2. Generate Sample Data

We provide a script to generate mock PDF invoices so you can test the pipeline immediately:

```bash
uv run python generate_invoices.py
```

This will populate the `./data` directory with 15 synthetic PDF invoices.

### 3. Configure Credentials

The pipeline needs access to an LLM for extraction and MotherDuck for loading the data.

Set **one** of the following environment variables for your chosen LLM:
```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
# OR
export GOOGLE_API_KEY="your-google-gemini-key"
# OR
export OPENAI_API_KEY="your-openai-key"
# OR
export AWS_ACCESS_KEY_ID="your-aws-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret"
```

Next, configure your MotherDuck destination. `dlt` can use environment variables:
```bash
export DESTINATION__MOTHERDUCK__CREDENTIALS="md:llamaindex?motherduck_token=<YOUR_MOTHERDUCK_TOKEN>"
```
*(Alternatively, you can place this token in a `.dlt/secrets.toml` file.)*

### 4. Run the Pipeline

Execute the pipeline to extract data from the PDFs and load it into MotherDuck:

```bash
uv run python llama_dlt_pipeline.py
```

You will see output indicating the LLM being used, processing steps for each PDF, and finally a summary of the load process from `dlt`. Once complete, you can log into MotherDuck to query your newly structured `invoice_data` and `invoice_data__items` tables!

## Deploy to dltHub

To run this pipeline on a schedule automatically in the cloud:

```bash
uv run dlthub deploy
```

Open [app.dlthub.com](https://app.dlthub.com) to monitor and schedule your deployed jobs.
