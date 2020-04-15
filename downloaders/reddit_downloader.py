import praw
import json
import requests
from PIL import Image
from io import BytesIO

def save_response(response):
    """save the JSON data so we don't constantly spam the API every time we run the program, and so we can use the JSON data later. Use in dev only"""
    with open('temp/data.json', 'w') as outfile:
        json.dump(response, outfile, indent=4)
        print('Saved JSON response')


def save_images(image_urls):
    headers = {
        'user-agent': 'drawer script'
    }
    for i, image_url in enumerate(image_urls):
        response = requests.get(image_url, headers=headers)
        save_response(response)
        img_data = response.content

        with Image.open(BytesIO(img_data)) as im:
            im.save('input/test{}.png'.format(i + 1))


def main():
    # App dashboard: https://www.reddit.com/prefs/apps
    USERNAME = "3th4n01s"
    PASSWORD = "edc08102005"
    SECRET = "aW8rqXQ_nZBAtxucX9kW0gWqeyY"
    CLIENT_ID = "e7Eo9j4KojcrGA"

    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=SECRET,
        password=PASSWORD,
        username=USERNAME,
        user_agent='drawer by /u/3th4n01s'
    )
    reddit.read_only = True

    subreddit = input('what subreddit would you like to go to? \n')


    submissions = reddit.subreddit(subreddit).hot(limit=5)
    submission_ids = [submission_id for submission_id in submissions]
    image_urls = []

    for i, submission_id in enumerate(submission_ids):
        submission = praw.models.Submission(reddit=reddit, id=submission_id)
        if submission.selftext == '':
            image_urls.append(submission.url)
        else:
            print('Post "{}" was not an image post, and was skipped.'.format(submission.title))

    save_images(image_urls)
    

if __name__ == '__main__':
    main()