import json
import os

def load_categories(language: str) -> dict:
    '''
    Load category data from a JSON file based on the specified language.
    Args:
        language (str): Language code.
    Returns:
        dict: Category data.
    '''
    file_path = f'jsons/categories/{language}.json'
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Category file for language '{language}' not found.")
    with open(file_path, encoding='utf-8') as f:
        categories_data = json.load(f)
    return categories_data

def load_locations(language: str) -> dict:
    '''
    Load location data from a JSON file based on the specified language.
    Args:
        language (str): Language code.
    Returns:
        dict: Location data.
    '''
    file_path = f'jsons/locations/{language}.json'
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Location file for language '{language}' not found.")
    with open(file_path, encoding='utf-8') as f:
        locations_data = json.load(f)
    return locations_data

def load_messages(language: str) -> dict:
    '''
    Load message templates from a JSON file based on the specified language.
    Args:
        language (str): Language code.
    Returns:
        dict: Message templates.
    '''
    file_path = f'jsons/messages/{language}.json'
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Messages file for language '{language}' not found.")
    with open(file_path, encoding='utf-8') as f:
        messages_data = json.load(f)
    return messages_data
