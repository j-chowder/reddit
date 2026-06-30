import praw
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("CLIENT_USER_AGENT"),
)

subreddit = reddit.subreddit("frugalmalefashion")


def collect_posts_from_listing(listing_name, limit=200):
    data = []

    if listing_name == "new":
        posts = subreddit.new(limit=limit)
    elif listing_name == "hot":
        posts = subreddit.hot(limit=limit)
    elif listing_name == "top":
        posts = subreddit.top(time_filter="year", limit=limit)
    else:
        raise ValueError("Invalid listing")

    for post in posts:
        data.append({
            "post_id": post.id,
            "source": listing_name,   # VERY IMPORTANT FEATURE
            "title": post.title,
            "selftext": post.selftext,
            "created_utc": post.created_utc,
            "score": post.score,
            "num_comments": post.num_comments,
            "upvote_ratio": post.upvote_ratio,
            "scraped_at": datetime.utcnow().timestamp()
        })
        
        print(data[len(data) - 1])

    return pd.DataFrame(data)


def collect_all(limit=500):
    df_new = collect_posts_from_listing("new", limit)
    df_hot = collect_posts_from_listing("hot", limit)
    df_top = collect_posts_from_listing("top", limit)

    df = pd.concat([df_new, df_hot, df_top], ignore_index=True)

    # deduplicate (CRITICAL)
    df = df.drop_duplicates(subset=["post_id"])

    return df


df = collect_all(limit=1000)
df.to_csv("./data/historical_data.csv", index=False)