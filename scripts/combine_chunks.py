import os
import json
import glob

# === CONFIG ===
RECIPE_DIR = "data/recipes"
NHS_DIR = "data/nhs"
OUTPUT_PATH = "data/combined/all_chunks.json"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

def load_chunks(folder, source_type):
    """
    Load all JSON files from the specified folder and return a list of dictionaries.
    """
    all_chunks = []
    for filepath in glob.glob(os.path.join(folder, "*.json")):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list):
                    # If the JSON file contains a list of dictionaries
                    for chunk in data:
                        chunk["source_type"] = source_type
                        all_chunks.append(chunk)
                else:
                    print(f"Skipping {filepath} — not a list.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {filepath}")
        except Exception as e:
            print(f"Failed to load file {filepath}: {e}")
    return all_chunks

if __name__ == "__main__":
    # Load chunks from both directories
    recipe_chunks = load_chunks(RECIPE_DIR, "recipe")
    nhs_chunks = load_chunks(NHS_DIR, "nhs")

    # Combine all chunks
    all_chunks = recipe_chunks + nhs_chunks

    # Save combined chunks to a single JSON file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as output_file:
        json.dump(all_chunks, output_file, indent=2, ensure_ascii=False)

    print(f"Combined {len(all_chunks)} chunks into {OUTPUT_PATH}")
