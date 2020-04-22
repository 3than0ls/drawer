from googleapiclient.discovery import build
import praw
import json
import requests
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import os


def save_images(image_urls):
    headers = {
        'user-agent': 'drawer script'
    }
    for i, image_url in enumerate(image_urls):
        response = requests.get(image_url, headers=headers)
        img_data = response.content

        try:
            with Image.open(BytesIO(img_data)) as im:
                im.save(os.path.join('input', 'image_{}.png'.format(i + 1)))
        except UnidentifiedImageError:
            print('It appears that {} is not an image file type, so we were unable to save it.'.format(image_url))


def cse_download(query_word, limit=5):
    """offers guaranteed usually high quality images"""
    cse = build('customsearch', 'v1').cse()

    # i'm not exactly a security expert, thank you. It's better than writing my info straight into the code and posting it for github to revel at :)
    with open("settings.json", "r") as settings_file:
        cse_auth_settings = json.load(settings_file)["cse_auth"]

    # don't have an api key and search engine ID? register/create one for Custom Search Engine for free! (not an ad)
    API_KEY = cse_auth_settings['api_key'] # Custom Search API Key
    # customsearch engine dashboard: https://cse.google.com/cse/setup/basic?cx=005540582309688715671:vhsyr31pydb
    CX = cse_auth_settings['search_engine_id'] # Custom Search Engine ID

    # link for cse.list query parameters: https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list#request
    request = cse.list(
        q = query_word,
        cx = CX,
        key = API_KEY,
        searchType = "image",
        num = limit
    )
    response = request.execute()
    items = response["items"]
    image_urls = [item["link"] for item in items]

    save_images(image_urls)


def reddit_download(subreddit, popularity="hot", limit=5, random=False):
    """requires specification to correct subreddits that are image-only. Non-image posts aren't saved. However, reddit offers a wider variety and frequently changing content"""

    # App dashboard: https://www.reddit.com/prefs/apps
    with open("settings.json", "r") as settings_file:
        reddit_auth_settings = json.load(settings_file)["reddit_auth"]

    # don't have a reddit account? Get one... at reddit...
    # don't have a reddit application with a secret and client id? register/create one of those as well, for free (ty for inspiring me reddit)!
    USERNAME = reddit_auth_settings['username']
    PASSWORD = reddit_auth_settings['password']
    SECRET = reddit_auth_settings['secret']
    CLIENT_ID = reddit_auth_settings['client_id']

    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=SECRET,
        password=PASSWORD,
        username=USERNAME,
        user_agent='drawer from /u/{}'.format(USERNAME)
    )
    reddit.read_only = True

    if not random:
        submissions = getattr(reddit.subreddit(subreddit), popularity)(limit=limit)
        submission_ids = [submission_id for submission_id in submissions]
    else:
        submission_ids = [reddit.subreddit(subreddit).random() for _ in range(limit)]
        if submission_ids[0] is None:
            print('{} subreddit does not support random submissions.'.format(subreddit))
            return

    image_urls = []

    for i, submission_id in enumerate(submission_ids):
        submission = praw.models.Submission(reddit=reddit, id=submission_id)
        if submission.selftext == '':
            image_urls.append(submission.url)
            print('Downloaded image from post "{}" ({})'.format(submission.title, submission.permalink))
        else:
            print('Post "{}" was a text post, and was skipped. ({})'.format(submission.title, submission.permalink))

    if not image_urls:
        print('We downloaded {} posts from {} in {} but all of them were text posts, so nothing was downloaded.'.format(limit, popularity, subreddit))

    save_images(image_urls)
    

def download_from_cse(limit=5):
    query_word = input('What\'s on your mind today? \n')
    cse_download(query_word, limit=limit)


def download_from_reddit(limit=5, random=False):
    subreddit = input('What subreddit would you like to go to? \n')
    if not random:
        search_options = ['hot', 'new', 'rising', 'top', 'controversial']
        popularity = input('Do you want {}, {}, {}, {}, or {}? \n'.format(*search_options))
        if popularity not in search_options:
            print('"{}" is not an available search option. Defaulting to "hot"')
            popularity = 'hot'
        reddit_download(subreddit, popularity=popularity, limit=limit)
    else:
        reddit_download(subreddit, limit=limit, random=True)


if __name__ == '__main__':
    # download_from_cse()
    download_from_reddit()