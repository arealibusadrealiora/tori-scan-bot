import requests
import json

def get_categories(api_data):
    categories = {category["label"]: category["code"] for category in api_data["categories"]}
    return categories

def get_subcategories(category_data):
    subcategories = {subcategory["label"]: subcategory["code"] for subcategory in category_data["categories"]}
    return subcategories

def find_category_by_label(categories, label):
    for category in categories:
        if category["label"] == label:
            return category
    return None

def find_category_code(categories, label):
    for category in categories:
        if category["label"] == label:
            return category.get("code", "N/A")
    return "N/A"

def generate_category_and_subcategory_data(api_url):
    response = requests.get(api_url)

    if response.status_code != 200:
        print("Failed to retrieve data from the API. Status code:", response.status_code)
        return

    api_data = response.json()
    categories = get_categories(api_data)

    category_subcategory_data = {}

    for category_name, category_code in categories.items():
        category_data = find_category_by_label(api_data["categories"], category_name)
        if category_data:
            subcategories = get_subcategories(category_data)
            category_subcategory_data[category_name] = {
                "category_code": category_code,
                "subcategories": subcategories
            }

    return category_subcategory_data

def main():
    api_url = "https://api.tori.fi/api/v1.2/public/categories/filter"

    category_subcategory_data = generate_category_and_subcategory_data(api_url)

    with open("categories.json", "w", encoding="utf-8") as output_file:
        json.dump(category_subcategory_data, output_file, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
