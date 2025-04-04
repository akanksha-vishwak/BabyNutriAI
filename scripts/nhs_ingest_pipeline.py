import os
import re
import json
import logging
from datetime import datetime
from urllib.parse import urljoin

import trafilatura

# Optional: Use nltk for sentence tokenization if available
try:
    import nltk
    nltk.download('punkt', quiet=True)
    from nltk.tokenize import sent_tokenize
    USE_SENT_TOKENIZATION = True
except ImportError:
    USE_SENT_TOKENIZATION = False

# === SETTINGS ===
DATA_DIR = "data/raw"  # Store raw scraped data separately
os.makedirs(DATA_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# === HELPERS ===

def fetch_clean_text(url):
    """
    Fetches HTML using Trafilatura and extracts the main text with links included.
    Raises an error if the URL cannot be fetched.
    """
    html = trafilatura.fetch_url(url)
    if html is None:
        raise ValueError(f"Could not fetch: {url}")
    extracted = trafilatura.extract(html, include_links=True)
    return normalize_links(extracted, base_url=url)

def normalize_links(text, base_url):
    """
    Normalizes relative links by converting them into absolute URLs.
    """
    link_pattern = re.compile(r'\((\/[^\)]+)\)')
    return re.sub(link_pattern, lambda m: f'({urljoin(base_url, m.group(1))})', text)

def estimate_tokens(text):
    """
    Provides a rough token count estimate.
    """
    return int(len(text.split()) * 1.3)

def chunk_text(text, max_words=100, overlap=20, use_sentence_splitting=False):
    """
    Splits text into chunks.
    
    - If `use_sentence_splitting` is True and nltk is available, split by sentences 
      ensuring chunks have roughly max_words with overlap.
    - Otherwise, do a simple word-based split.
    """
    if use_sentence_splitting and USE_SENT_TOKENIZATION:
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0
        for sentence in sentences:
            sentence_word_count = len(sentence.split())
            # If adding this sentence exceeds max_words and current_chunk is not empty,
            # finalize the current chunk.
            if current_length + sentence_word_count > max_words and current_chunk:
                chunks.append(" ".join(current_chunk))
                # Start new chunk with overlap from the end of the previous chunk
                overlap_text = " ".join(current_chunk[-overlap:]) if overlap < len(current_chunk) else " ".join(current_chunk)
                current_chunk = overlap_text.split()
                current_length = len(current_chunk)
            current_chunk.append(sentence)
            current_length += sentence_word_count
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks
    else:
        # Simple word-based splitting
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + max_words
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start += max_words - overlap
        return chunks

def extract_sections(text):
    """
    Splits text into sections based on heuristics for section headers:
    - A short line (<= 8 words)
    - Starts with an uppercase letter
    - Contains no punctuation like .?!:
    """
    sections = []
    lines = text.split("\n")
    current_section = "Unknown"
    buffer = []

    for line in lines:
        stripped = line.strip()
        if stripped and len(stripped.split()) <= 8 and stripped[0].isupper() and not any(p in stripped for p in ".?!:"):
            if buffer:
                sections.append((current_section, "\n".join(buffer).strip()))
                buffer = []
            current_section = stripped
        else:
            buffer.append(line)

    if buffer:
        sections.append((current_section, "\n".join(buffer).strip()))
    return sections

def process_url(url, title, output_filename, max_words=100, overlap=20, use_sentence_splitting=False):
    """
    Processes a single URL:
      - Fetches and cleans the text
      - Extracts sections and chunks them
      - Adds metadata and saves to a JSON file.
    """
    logging.info(f"Processing URL: {url}")
    try:
        clean_text = fetch_clean_text(url)
    except Exception as e:
        logging.error(f"Error fetching or cleaning text from {url}: {e}")
        return []
    
    timestamp = datetime.utcnow().isoformat()
    section_blocks = extract_sections(clean_text)
    all_chunks = []

    for section, sec_text in section_blocks:
        chunks = chunk_text(sec_text, max_words=max_words, overlap=overlap, use_sentence_splitting=use_sentence_splitting)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk": chunk,
                "section": section,
                "source_url": url,
                "title": title,
                "chunk_id": f"{title.replace(' ', '_').lower()}_{section.replace(' ', '_').lower()}_{i}",
                "scraped_at": timestamp,
                "tokens": estimate_tokens(chunk)
            })
    
    output_path = os.path.join(DATA_DIR, output_filename)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved {len(all_chunks)} chunks to {output_path}")
    except Exception as e:
        logging.error(f"Error saving file {output_path}: {e}")
    return all_chunks

# === BATCH PROCESSING ===
urls = {
    "babys_first_solid_foods": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/babys-first-solid-foods/",
    "help_your_baby_enjoy_new_foods": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/help-your-baby-enjoy-new-foods/",
    "baby_and_toddler_meal_ideas": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/baby-and-toddler-meal-ideas/",
    "childrens_food_safety_and_hygiene": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/childrens-food-safety-and-hygiene/",
    "drinks_and_cups_for_babies_and_young_children": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/drinks-and-cups-for-babies-and-young-children/",
    "food_allergies_in_babies_and_young_children": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/food-allergies-in-babies-and-young-children/",
    "foods_to_avoid_giving_babies_and_young_children": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/foods-to-avoid-giving-babies-and-young-children/",
    "fussy_eaters": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/fussy-eaters/",
    "vitamins_for_children": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/vitamins-for-children/",
    "what_to_feed_young_children": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/what-to-feed-young-children/",
    "young_children_and_food_common_questions": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/young-children-and-food-common-questions/",
}

def batch_process_urls(url_map, max_words=100, overlap=20, use_sentence_splitting=False):
    for key, url in url_map.items():
        title = key.replace("_", " ").title()
        filename = f"{key}.json"
        process_url(url, title=title, output_filename=filename, 
                    max_words=max_words, overlap=overlap, use_sentence_splitting=use_sentence_splitting)

# Run batch processing (adjust parameters as needed)
if __name__ == "__main__":
    batch_process_urls(urls, max_words=150, overlap=30, use_sentence_splitting=True)