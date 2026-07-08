import praw
import pandas as pd
from tqdm import tqdm
import time
from dotenv import load_dotenv, dotenv_values
import os

def preparation():
    load_dotenv()
    
    reddit = praw.Reddit(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        user_agent=os.getenv('CLIENT_USER_AGENT'),
    )
    return reddit
    
    
def fetch_current_scores(post_ids, reddit, sleep=0.3):
    results = []

    for pid in tqdm(post_ids):
        try:
            submission = reddit.submission(id=pid)

            results.append({
                "post_id": pid,
                "current_score": submission.score,
                "current_num_comments": submission.num_comments,
                "current_upvote_ratio": submission.upvote_ratio
            })

            time.sleep(sleep)  # avoid rate limits

        except Exception as e:
            results.append({
                "post_id": pid,
                "current_score": None,
                "error": str(e)
            })

    return pd.DataFrame(results)

def fetch_selftext(post_ids, reddit, sleep=0.3):
    results = []

    for pid in tqdm(post_ids):
        try:
            submission = reddit.submission(id=pid)

            results.append({
                "post_id": pid,
                "selftext": submission.selftext
            })

            time.sleep(sleep)

        except Exception as e:
            results.append({
                "post_id": pid,
                "selftext": None,
                "error": str(e)
            })

    return pd.DataFrame(results)

df = pd.read_csv("data/posts_by_time.csv")
post_ids = df["post_id"].dropna().unique().tolist()

df_selftext = fetch_selftext(post_ids, reddit=preparation())
df_selftext.to_csv('data/post_selftext.csv', index=False)