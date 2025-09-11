from dotenv import load_dotenv, dotenv_values
import os
import praw

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    user_agent=os.getenv('CLIENT_USER_AGENT'),
)

subreddit = reddit.subreddit("frugalmalefashion")

submission = reddit.submission(id='1nef8bv')

print(submission.link_flair_text)

