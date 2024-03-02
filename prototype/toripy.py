import requests
from bs4 import BeautifulSoup
import time

url = "https://www.tori.fi/koko_suomi?q=lapsi&cg=0&w=3"
previous_items = []

while True:
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('a', class_='item_row_flex')

        for item in items:
            item_id = item['id'].replace("item_","")

            if item_id not in previous_items:
                link = item['href']
                name = item.find('div', class_='li-title').text.strip()
                price = item.find('p', class_='list_price ineuros').text.strip()
                date_time = item.find('div', class_='date_image').text.strip()
                place = item.find('div', class_='cat_geo clean_links').find('p').text.strip()

                print("New item found:")
                print(f"Item ID: {item_id}")
                print(f"Link: {link}")
                print(f"Name: {name}")
                print(f"Price: {price}")
                print(f"Date: {date_time.split()[0]}")
                print(f"Time: {date_time.split()[1]}")
                print(f"Place: {place}\n")

                previous_items.append(item_id)

        time.sleep(900)

    except Exception as e:
        print("Error:", str(e))
        time.sleep(300)
