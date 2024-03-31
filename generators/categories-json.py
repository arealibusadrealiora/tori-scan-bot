import json

def extract_category_hierarchy(filters):
    hierarchy = {}

    for item in filters:
        if item.get("name") == "category" and item.get("filter_items"):
            for category in item["filter_items"]:
                category_name = category["display_name"]
                category_code = category["value"]
                category_subcategories = {}
                
                for subcategory in category.get("filter_items", []):
                    subcategory_name = subcategory["display_name"]
                    subcategory_code = subcategory["value"]
                    product_types = {}

                    for product_type in subcategory.get("filter_items", []):
                        product_type_name = product_type["display_name"]
                        product_type_code = product_type["value"]
                        product_types[product_type_name] = product_type_code

                    category_subcategories[subcategory_name] = {"subcategory_code": subcategory_code, "product_types": product_types}

                hierarchy[category_name] = {"category_code": category_code, "subcategories": category_subcategories}

    return hierarchy

def main():
    file_path = "filters.json"

    with open(file_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    filters = data.get("filters", [])
    hierarchy = extract_category_hierarchy(filters)

    with open("categories.json", "w", encoding="utf-8") as output_file:
        json.dump(hierarchy, output_file, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
