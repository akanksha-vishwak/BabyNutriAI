import requests
from bs4 import BeautifulSoup

url = "https://www.nhs.uk/conditions/baby/weaning-and-feeding/"

# Fetch the page content
response = requests.get(url)
html = response.text

def slugify(link):
    """Converts a page path to a name like 'first_solid_foods'"""
    return link.strip("/").split("/")[-1].replace("-", "_")

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html, "html.parser")

# Extract all <a> tags and filter for those with href attributes
all_links = [a.get("href") for a in soup.find_all("a") if a.get("href")]

# Filter to include only relevant links
relevant_links = [link for link in all_links if "nhs.uk" in link or link.startswith("https://www.nhs.uk/conditions/baby/weaning-and-feeding/")]

if __name__ == "__main__":

    url_dict = {}
    for link in relevant_links:
        # Create a slugified key
        key = slugify(link)
        url_dict[key] = link

    print("urls = {")
    for name, url in url_dict.items():
        print(f'    "{name}": "{url}",')
    print("}")

# This script will print out a dictionary of URLs that can be used in the next script.
# The output will look like:
# urls = {
#     "first_solid_foods": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/babys-first-solid-foods/",
#}
