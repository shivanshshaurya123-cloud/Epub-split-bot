import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from google import genai

# ==========================================
# CONFIGURATION
# ==========================================
EPUB_FILE_PATH = "your_book.epub"  # Replace with your EPUB file path
OUTPUT_DIR = "output_chapters"     # Directory where the .txt files will be saved
MODEL_NAME = "gemini-2.5-flash"    # Standard Gemini model for text tasks

def extract_text_from_html(html_content):
    """Parses HTML content from the EPUB and returns plain text."""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Extract text, replacing block elements with newlines for readability
    text = soup.get_text(separator='\n\n', strip=True)
    return text

def get_chapter_summary(client, chapter_text):
    """Integrates with Gemini to process the chapter text."""
    # We are asking for a summary here, but you can change this prompt to 
    # translate the text, extract characters, fix grammar, etc.
    prompt = (
        "You are an AI assistant helping to process a book. "
        "Please provide a 2-3 sentence summary of the following chapter text. "
        "If the text is too short or just a title page, just say 'No summary needed.'\n\n"
        f"Text:\n{chapter_text[:5000]}" # Truncating to 5000 chars to save bandwidth, remove slicing if you want the whole chapter processed
    )
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"[Gemini API Error: {e}]"

def main():
    # 1. Initialize Gemini Client
    # It automatically picks up the GEMINI_API_KEY environment variable.
    # Alternatively, you can do: genai.Client(api_key="YOUR_API_KEY_HERE")
    print("Initializing Gemini Client...")
    client = genai.Client()

    # 2. Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 3. Load the EPUB file
    print(f"Loading EPUB: {EPUB_FILE_PATH}")
    try:
        book = epub.read_epub(EPUB_FILE_PATH)
    except Exception as e:
        print(f"Error reading EPUB: {e}")
        return

    # 4. Iterate through the items in the EPUB
    chapter_count = 1
    for item in book.get_items():
        # EPUBs contain images, css, etc. We only want the document (HTML) files
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            raw_content = item.get_content()
            chapter_text = extract_text_from_html(raw_content)

            # Skip empty or nearly empty chapters (like blank title pages)
            if len(chapter_text) < 50:
                continue
            
            print(f"Processing Chapter {chapter_count} (Length: {len(chapter_text)} characters)...")
            
            # 5. Integrate with Gemini
            summary = get_chapter_summary(client, chapter_text)
            
            # 6. Save to a .txt file
            file_name = f"Chapter_{chapter_count:03d}.txt"
            file_path = os.path.join(OUTPUT_DIR, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"--- GEMINI SUMMARY ---\n")
                f.write(f"{summary}\n")
                f.write(f"----------------------\n\n\n")
                f.write(chapter_text)
                
            print(f"Saved: {file_path}")
            chapter_count += 1

    print("\nExtraction and processing complete!")

if __name__ == "__main__":
    main()
    
