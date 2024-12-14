import json

# This script creates a JSON based on tori locations which are later used in the bot.

def extract_hierarchy(filters):
    hierarchy = {}

    for item in filters:
        if item.get("name") == "location" and item.get("filter_items"):
            for region in item["filter_items"]:
                region_name = region["display_name"]
                region_code = region["value"]
                region_cities = {}
                for city in region.get("filter_items", []):
                    city_name = city["display_name"]
                    city_code = city["value"]
                    city_areas = {}
                    for area in city.get("filter_items", []):
                        area_name = area["display_name"]
                        area_code = area["value"]
                        city_areas[area_name] = area_code
                    region_cities[city_name] = {"city_code": city_code, "areas": city_areas}
                hierarchy[region_name] = {"region_code": region_code, "cities": region_cities}

    return hierarchy

def main():
    file_path = "filters.json"

    with open(file_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    filters = data.get("filters", [])
    hierarchy = extract_hierarchy(filters)

    with open("locations.json", "w", encoding="utf-8") as output_file:
        json.dump(hierarchy, output_file, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
