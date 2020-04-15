from googleapiclient.discovery import build
import json
import requests
from PIL import Image
from io import BytesIO


def save_response(response):
    """save the JSON data so we don't constantly spam the API every time we run the program, and so we can use the JSON data later."""
    with open('temp/data.json', 'w') as outfile:
        json.dump(response, outfile, indent=4)
        print('Saved JSON response')


# identical to the one in reddit_downloader
def save_images(image_urls):
    headers = {
        'user-agent': 'drawer script'
    }
    for i, image_url in enumerate(image_urls):
        img_data = requests.get(image_url, headers=headers).content

        with Image.open(BytesIO(img_data)) as im:
            im.save('input/test{}.png'.format(i + 1))


def main():
    query_word = input('What\'s on your mind today, Ethan? \n')

    cse = build('customsearch', 'v1').cse()

    API_KEY = "AIzaSyCnEGK5qSgPRavJrfXbo1ggR88qQfWu0ds" # Custom Search API Key
    # customsearch engine dashboard: https://cse.google.com/cse/setup/basic?cx=005540582309688715671:vhsyr31pydb
    CX = "005540582309688715671:vhsyr31pydb" # Custom Search Engine ID

    # link for cse.list query parameters: https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list#request
    request = cse.list(
        q = query_word,
        cx = CX,
        key = API_KEY,
        searchType = "image",
        num = 5
    )
    response = request.execute()
    
    save_response(response)

    items = response["items"]
    image_urls = [item["link"] for item in items]

    save_images(image_urls)
    

if __name__ == '__main__':
    # main_saved_responses()
    main()