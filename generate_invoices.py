import os
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# Clear old test files
data_dir = "./data"
os.makedirs(data_dir, exist_ok=True)
for f in os.listdir(data_dir):
    if f.endswith(".pdf"):
        os.remove(os.path.join(data_dir, f))

# Sample data for invoices
companies = ["Acme Corp", "Globex Corporation", "Soylent Corp", "Initech", "Umbrella Corp", "Stark Industries", "Wayne Enterprises", "Massive Dynamic"]
items = [
    ("Consulting Services", 150.00),
    ("Software License", 1200.00),
    ("Server Maintenance", 300.00),
    ("Cloud Storage", 50.00),
    ("Marketing Strategy", 800.00),
    ("Web Design", 1500.00),
    ("SEO Optimization", 400.00),
    ("Database Migration", 2500.00)
]

def generate_standard_invoice(pdf, invoice_id, company, date_str, selected_items):
    # Standard Table Invoice
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="INVOICE", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(100, 8, txt=f"Invoice #: INV-{invoice_id:04d}", ln=False)
    pdf.cell(100, 8, txt=f"Date: {date_str}", ln=True)
    pdf.cell(100, 8, txt=f"Billed To: {company}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(90, 10, txt="Description", border=1)
    pdf.cell(30, 10, txt="Qty", border=1, align="C")
    pdf.cell(35, 10, txt="Unit Price", border=1, align="R")
    pdf.cell(35, 10, txt="Total", border=1, align="R")
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    total_amount = 0
    for item_name, price, qty in selected_items:
        line_total = price * qty
        total_amount += line_total
        pdf.cell(90, 10, txt=item_name, border=1)
        pdf.cell(30, 10, txt=str(qty), border=1, align="C")
        pdf.cell(35, 10, txt=f"${price:.2f}", border=1, align="R")
        pdf.cell(35, 10, txt=f"${line_total:.2f}", border=1, align="R")
        pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(155, 10, txt="Total Amount Due:", border=0, align="R")
    pdf.cell(35, 10, txt=f"${total_amount:.2f}", border=1, align="R")

def generate_receipt_style(pdf, invoice_id, company, date_str, selected_items):
    # Narrow receipt style
    pdf.set_font("Courier", 'B', 14)
    pdf.cell(0, 8, txt="*** OFFICIAL RECEIPT ***", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Courier", size=10)
    pdf.cell(0, 6, txt=f"Receipt ID: RCPT-{invoice_id}", ln=True, align="L")
    pdf.cell(0, 6, txt=f"Issued On: {date_str}", ln=True, align="L")
    pdf.cell(0, 6, txt=f"Customer: {company}", ln=True, align="L")
    pdf.ln(5)
    pdf.cell(0, 6, txt="-"*50, ln=True, align="L")
    
    total_amount = 0
    for item_name, price, qty in selected_items:
        line_total = price * qty
        total_amount += line_total
        pdf.cell(0, 6, txt=f"{qty}x {item_name}", ln=True, align="L")
        pdf.cell(0, 6, txt=f"    @ ${price:.2f} ea .............. ${line_total:.2f}", ln=True, align="L")
        
    pdf.cell(0, 6, txt="-"*50, ln=True, align="L")
    pdf.set_font("Courier", 'B', 12)
    pdf.cell(0, 8, txt=f"FINAL TOTAL: ${total_amount:.2f}", ln=True, align="L")

def generate_letter_style(pdf, invoice_id, company, date_str, selected_items):
    # Letter-based format
    pdf.set_font("Times", size=12)
    pdf.cell(0, 8, txt=date_str, ln=True, align="R")
    pdf.ln(10)
    pdf.cell(0, 8, txt=f"To the Accounts Payable Department at {company},", ln=True, align="L")
    pdf.ln(5)
    pdf.multi_cell(0, 8, txt=f"Please find below the statement of services rendered for reference number #{invoice_id}. Payment is expected within 30 days of the date listed above.")
    pdf.ln(10)
    
    pdf.set_font("Times", 'B', 12)
    pdf.cell(0, 8, txt="Services Provided:", ln=True, align="L")
    pdf.set_font("Times", size=12)
    
    total_amount = 0
    for item_name, price, qty in selected_items:
        line_total = price * qty
        total_amount += line_total
        pdf.cell(10, 8, txt="-", ln=False, align="C")
        pdf.cell(0, 8, txt=f"{item_name} (Quantity: {qty}) - Rate: ${price:,.2f} -> Sum: ${line_total:,.2f}", ln=True, align="L")
        
    pdf.ln(10)
    pdf.set_font("Times", 'B', 14)
    pdf.cell(0, 10, txt=f"Total Balance Owed: ${total_amount:,.2f}", ln=True, align="L")
    pdf.set_font("Times", size=12)
    pdf.ln(5)
    pdf.cell(0, 8, txt="Thank you for your business.", ln=True, align="L")


def generate_invoice(invoice_id):
    pdf = FPDF()
    pdf.add_page()
    
    company = random.choice(companies)
    date_str = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
    
    num_items = random.randint(1, 4)
    selected_items = []
    for _ in range(num_items):
        item_name, price = random.choice(items)
        qty = random.randint(1, 5)
        selected_items.append((item_name, price, qty))
        
    layout_style = random.choice(["standard", "receipt", "letter"])
    
    if layout_style == "standard":
        generate_standard_invoice(pdf, invoice_id, company, date_str, selected_items)
    elif layout_style == "receipt":
        generate_receipt_style(pdf, invoice_id, company, date_str, selected_items)
    else:
        generate_letter_style(pdf, invoice_id, company, date_str, selected_items)
        
    # Save
    pdf.output(os.path.join(data_dir, f"invoice_INV-{invoice_id:04d}.pdf"))

# Generate 15 invoices
for i in range(101, 116):
    generate_invoice(i)
print("Successfully generated 15 realistic invoice PDFs with mixed layouts in ./data/")
