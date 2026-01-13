import os
import fitz  # PyMuPDF
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY. Please set it in your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extracts text from a PDF file.
    
    Args:
        uploaded_file (str): The path to the PDF file.
        
    Returns:
        str: The extracted text.
    """
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    return "\n".join(text_parts)


def ask_openai(prompt: str, max_tokens: int = 500) -> str:
    """
    Sends a prompt to the OpenAI API and returns the response.
    
    Args:
        prompt (str): The prompt to send to the OpenAI API.
        model (str): The model to use for the request.
        temperature (float): The temperature for the response.
        
    Returns:
        str: The response from the OpenAI API.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",  
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
