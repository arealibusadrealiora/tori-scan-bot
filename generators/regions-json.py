import requests
import json

def get_regions(api_data):
    regions = {location["label"]: location["code"] for location in api_data["locations"]}
    return regions

def get_areas(region_data):
    areas = {location["label"]: location["code"] for location in region_data["locations"]}
    return areas

def find_location_by_label(locations, label):
    for location in locations:
        if location["label"] == label:
            return location
    return None

def generate_region_and_area_data(api_url):
    response = requests.get(api_url)

    if response.status_code != 200:
        print("Failed to retrieve data from the API. Status code:", response.status_code)
        return

    api_data = response.json()
    regions = get_regions(api_data)

    region_area_data = {}

    for region_name, region_code in regions.items():
        region_data = find_location_by_label(api_data["locations"], region_name)
        if region_data:
            areas = get_areas(region_data)
            region_area_data[region_name] = {
                "region_code": region_code,
                "areas": areas
            }

    return region_area_data

def main():
    api_url = "https://api.tori.fi/api/v1.2/public/regions"

    region_area_data = generate_region_and_area_data(api_url)

    with open("locations.json", "w", encoding="utf-8") as output_file:
        json.dump(region_area_data, output_file, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
