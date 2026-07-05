import json
import google.generativeai as genai
from core.config import GEMINI_API_KEY
from core.logger import logger

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.5-flash')

def extract_receipt_info(image_path: str, categories: list, payments: list) -> dict:
    """Read receipt image and extract financial info in English."""
    try:
        sample_file = genai.upload_file(path=image_path)
        
        prompt = f"""
        You are a professional Malaysian accounting assistant. Please analyze this receipt photo, extract the following information, and output strictly in pure JSON format:
        - Date: Transaction date (Format: DD/MM/YYYY)
        - Vendor: Merchant/Vendor name
        - Company_Reg_No: Merchant's company registration number (e.g., SSM No., BRN, or TIN. Leave blank if not found)
        - Invoice_No: Receipt/Invoice/Bill Number (Leave blank if not found)
        - Tax_Amount: Tax amount (e.g., SST, Service Tax, GST. Output "0.00" if not found)
        - Amount: Total amount as a pure number (Final amount including tax, e.g., 50.00)
        - Items: List of purchased items (e.g., [{{"name": "Nasi Lemak", "price": "15.00"}}])
        - Category: Expense category (Must select strictly from this list: {categories}).
          **[CRITICAL RULE]: If it is a dining receipt and there are no special notes, default to the category containing "Staff Refreshment" or "Food".**
        - Payment_Method: Payment channel (Must select strictly from this list: {payments})
        
        Do not output any Markdown tags (like ```json). Only output a clean JSON string.
        """
        
        response = model.generate_content([sample_file, prompt])
        
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        result_json = json.loads(response_text.strip())
        
        result_json.setdefault("Company_Reg_No", "")
        result_json.setdefault("Invoice_No", "")
        result_json.setdefault("Tax_Amount", "0.00")
        
        return result_json
        
    except Exception as e:
        logger.error(f"AI Extraction Failed: {e}", exc_info=True)
        raise e