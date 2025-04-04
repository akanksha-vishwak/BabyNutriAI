import os
import re
import json
import logging
from datetime import datetime
from urllib.parse import urlparse

import trafilatura

# === CONFIG ===
DATA_DIR = "data/recipes"
os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# === HELPERS ===

def slugify(text):
    return re.sub(r"[\s_-]+", "_", re.sub(r"[^\w\s-]", "", text.strip().lower()))

def fetch_clean_text(url):
    html = trafilatura.fetch_url(url)
    if html is None:
        raise ValueError(f"Could not fetch: {url}")
    return trafilatura.extract(html)

def clean_footer_junk(text):
    blacklist = [
        "More recipes",
        "More in recipes and meal ideas",
        "More in Start for Life",
        "Start for Life",
        "Last reviewed",
        "Next review due"
    ]
    lines = text.strip().split("\n")
    cleaned_lines = [line for line in lines if line.strip() not in blacklist]
    return "\n".join(cleaned_lines)

def estimate_tokens(text):
    return int(len(text.split()) * 1.3)

def chunk_text(text, max_words=150, overlap=30):
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        end = start + max_words
        chunks.append(" ".join(words[start:end]))
        start += max_words - overlap
    return chunks

def parse_metadata_from_text(text):
    lines = text.strip().split("\n")
    metadata = {
        "title": None,
        "description": None,
        "age_range": None,
        "prep_time": None,
        "cook_time": None,
        "portions": None,
        "ingredients": [],
        "weaning_tip": None,
    }

    # Assume first 2 lines are title + description
    if len(lines) >= 1:
        metadata["title"] = lines[0].replace("recipe", "").strip().title()
    if len(lines) >= 2:
        metadata["description"] = lines[1].strip()

    section = None
    weaning_tip_next = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        if "age:" in stripped.lower():
            metadata["age_range"] = stripped.split(":", 1)[1].strip()
        elif "prep:" in stripped.lower():
            metadata["prep_time"] = stripped.split(":", 1)[1].strip()
        elif "cook:" in stripped.lower():
            metadata["cook_time"] = stripped.split(":", 1)[1].strip()
        elif "portions:" in stripped.lower():
            match = re.search(r"\d+", stripped)
            if match:
                metadata["portions"] = int(match.group())

        if stripped.lower() == "ingredients":
            section = "ingredients"
            continue
        elif stripped.lower() in {"method", "instructions"}:
            section = "method"
            continue
        elif "weaning tip" in stripped.lower():
            weaning_tip_next = True
            continue
        elif weaning_tip_next and not metadata["weaning_tip"]:
            metadata["weaning_tip"] = stripped
            weaning_tip_next = False

        if section == "ingredients" and stripped.startswith("-"):
            metadata["ingredients"].append(stripped.lstrip("-").strip())

    return metadata

def process_url(url, key, max_words=150, overlap=30):
    logging.info(f"Processing: {url}")
    try:
        full_text = fetch_clean_text(url)
        clean_text = clean_footer_junk(full_text)
        metadata = parse_metadata_from_text(clean_text)
        chunks = chunk_text(clean_text, max_words, overlap)
    except Exception as e:
        logging.error(f"Error processing {url}: {e}")
        return

    timestamp = datetime.utcnow().isoformat()
    slug = slugify(metadata["title"] or key)

    output = []
    for i, chunk in enumerate(chunks):
        output.append({
            "chunk": chunk,
            "chunk_id": f"{slug}_{i}",
            "title": metadata["title"],
            "description": metadata["description"],
            "source_url": url,
            "scraped_at": timestamp,
            "tokens": estimate_tokens(chunk),
            "age_range": metadata["age_range"],
            "prep_time": metadata["prep_time"],
            "cook_time": metadata["cook_time"],
            "portions": metadata["portions"],
            "ingredients": metadata["ingredients"],
            "weaning_tip": metadata["weaning_tip"],
            "meal_type": "unknown"
        })

    output_path = os.path.join(DATA_DIR, f"{slug}.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved {len(output)} chunks to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save {slug}: {e}")

# === URLS ===

recipe_urls = {
    "breakfast_cups": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/breakfast-cups/",
    "egg_cups_and_toast": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/egg-cups-and-toast/",
    "cheese_and_mushroom_cakes": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/cheese-and-mushroom-cakes/",
    "chicken_noodle_stew": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/chicken-noodle-stew/",
    "baked_plantain": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/baked-plantain/",
    "jamaican_fish_curry": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/jamaican-fish-curry/",
    "jacket_potato_and_chilli_veg": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/jacket-potato-and-chilli-veg/",
    "butternut_squash_and_red_pepper_soup": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/butternut-squash-and-red-pepper-soup/",
    "aromatic_beef_curry": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/aromatic-beef-curry/",
    "beef_bolognese": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/beef-bolognese/",
    "beefy_veg_curry": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/beefy-veg-curry/",
    "pineapple_slices_with_plain_yoghurt": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/pineapple-slices-with-plain-yoghurt/",
    "ham_pasta_bake": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/ham-pasta-bake/",
    "tender_lamb_strips": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/tender-lamb-strips/",
    "fish_ratatouille": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/fish-ratatouille/",
    "omelette_muffins": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/omelette-muffins/",
    "african_bean_stew": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/african-bean-stew/",
    "vegetable_and_ham_bake": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/vegetable-and-ham-bake/",
    "omelette_popovers": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/omelette-popovers/",
    "tasty_salmon_risotto": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/tasty-salmon-risotto/",
    "cinnamon_toast_and_banana_sticks": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/cinnamon-toast-and-banana-sticks/",
    "lentil_pasta_with_broccoli": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/lentil-pasta-with-broccoli/",
    "mexican_chicken_with_pitta": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/mexican-chicken-with-pitta/",
    "fruity_sticks": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/fruity-sticks/",
    "scrambly_egg_on_muffins": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/scrambly-egg-on-muffins/",
    "root_vegetable_mash": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/root-vegetable-mash/",
    "sweetcorn_chowder": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/sweetcorn-chowder/",
    "smashed_avocado_and_banana": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/smashed-avocado-and-banana/",
    "peachy_cereal": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/peachy-cereal/",
    "falafel": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/falafel/",
    "vegetable_biryani": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/vegetable-biryani/",
    "veggie_finger_foods": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/veggie-finger-foods/",
    "apple_and_blueberry_stew": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/apple-and-blueberry-stew/",
    "mixed_bean_hot_potato": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/mixed-bean-hot-potato/",
    "veggie_biryani": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/veggie-biryani/",
    "fish_curry": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/fish-curry/",
    "pea_and_ham_bake": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/pea-and-ham-bake/",
    "egg_and_toast_fingers_with_tomatoes": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/egg-and-toast-fingers-with-tomatoes/",
    "simple_baked_fish": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/simple-baked-fish/",
    "fish_risotto_with_peas": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/fish-risotto-with-peas/",
    "pasta_ratatouille": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/pasta-ratatouille/",
    "spag_bol": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/spag-bol/",
    "squash_and_lentil_soup": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/squash-and-lentil-soup/",
    "zesty_chicken_wrap": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/zesty-chicken-wrap/",
    "beetroot_dip_with_pitta_bread_fingers": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/beetroot-dip-with-pitta-bread-fingers/",
    "cheesy_english_muffins_and_cucumber_sticks": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/cheesy-english-muffins-and-cucumber-sticks/",
    "omelette_pots": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/omelette-pots/",
    "fish_risotto_with_red_pepper_sticks": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/fish-risotto-with-red-pepper-sticks/",
    "mac_and_cheese": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/mac-and-cheese/",
    "cinnamon_and_banana_toast": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/cinnamon-and-banana-toast/",
    "jamaican_fish": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/jamaican-fish/",
    "sweet_potato_fingers": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/sweet-potato-fingers/",
    "butterbean_goulash_green_beans": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/butterbean-goulash-green-beans/",
    "lemony_chicken_strips": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/lemony-chicken-strips/",
    "steamed_apple_and_pear": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/steamed-apple-and-pear/",
    "autumn_lentil_soup": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/autumn-lentil-soup/",
    "ham_flatbread": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/ham-flatbread/",
    "chicken_veg_and_noodle_dinner": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/chicken-veg-and-noodle-dinner/",
    "breakfast_3_ways": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/breakfast-3-ways/",
    "creamy_lentil_and_broccoli_pasta": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/creamy-lentil-and-broccoli-pasta/",
    "banana_and_berry_porridge": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/banana-and-berry-porridge/",
    "chickpea_biryani": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/chickpea-biryani/",
    "african_sweet_potato_stew": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/african-sweet-potato-stew/",
    "tuna_dip": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/tuna-dip/",
    "macaroni_cheese_and_peas": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/macaroni-cheese-and-peas/",
    "tuna_mayo_hot_potato": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/tuna-mayo-hot-potato/",
    "chicken_fajitas": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/chicken-fajitas/",
    "hummus_with_veggie_fingers": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/hummus-with-veggie-fingers/",
    "egg_and_mushroom_cups": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/egg-and-mushroom-cups/",
    "cinnamon_toasty_fingers": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/cinnamon-toasty-fingers/",
    "breakfast_eggs_and_tomato": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/breakfast-eggs-and-tomato/",
    "fruity_stew": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/fruity-stew/",
    "green_mash": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/green-mash/",
    "chicken_and_leek_hotpot": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/chicken-and-leek-hotpot/",
    "beanie_dip_with_breadsticks": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/beanie-dip-with-breadsticks/",
    "vegetable_pasta": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/vegetable-pasta/",
    "sweet_potato_patties": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/sweet-potato-patties/",
    "african_stew": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/african-stew/",
    "delicious_dhal": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/delicious-dhal/",
    "egg_fingers": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/egg-fingers/",
    "mexican_chicken": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/mexican-chicken/",
    "creamy_hotpot": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/creamy-hotpot/",
    "cheesy_beans_on_toast": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/cheesy-beans-on-toast/",
    "lamb_curry": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/lamb-curry/",
    "beef_curry_with_rice": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/beef-curry-with-rice/",
    "blueberry_porridge": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/blueberry-porridge/",
    "fruity_porridge": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/fruity-porridge/",
    "tuna_mayo_jackets": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/tuna-mayo-jackets/",
    "broccoli": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/broccoli/",
    "cheesy_toast_fingers_and_cucumber": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/cheesy-toast-fingers-and-cucumber/",
    "crustless_mini_quiche": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/crustless-mini-quiche/",
    "chicken_noodles": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/chicken-noodles/",
    "pasta_bolognese": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/pasta-bolognese/",
    "omelette_fingers": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/omelette-fingers/",
    "scrambled_egg": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/scrambled-egg/",
    "cheesy_pasta_and_peas": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/cheesy-pasta-and-peas/",
    "leek_and_potato": "https://www.nhs.uk/start-for-life/baby/recipes-and-meal-ideas/leek-and-potato/",
}

# === BATCH ===

def batch_process_urls(url_map, max_words=150, overlap=30):
    for key, url in url_map.items():
        process_url(url, key, max_words, overlap)

# === MAIN ===

if __name__ == "__main__":
    batch_process_urls(recipe_urls)
