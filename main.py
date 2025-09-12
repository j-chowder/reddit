from dotenv import load_dotenv, dotenv_values
import os
import praw
from collections import deque
import time

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    user_agent=os.getenv('CLIENT_USER_AGENT'),
)

subreddit = reddit.subreddit("frugalmalefashion")

submissions = []
q = deque()


        
### 1. find new submissions

def find_submissions():
    for submission in subreddit.new(limit=5):
        print(submission.title), print(submission.id), print(submission.url)
        if submission.id not in submissions:
            submissions.append(submission.id)
            # add the corresponding times in a queue
            time_posted = submission.created_utc
            add_times(q, submission.id, time_posted)

### 2. add times

def add_times(q, id, time_posted):
    for times in [1800, 3600, 7200, 18000, 86400]: # 0.5, 1, 2, 5, 24 hours in seconds since time_posted is in unix.
        d = {id: time_posted + times}
        q.append(d)

### 3. check if times have elapsed.
def check_times():
    print(q)
    while time.time() >= list(q[0].values())[0]:
        record_stats(q[0])
        q.popleft()
    

### 4. record stats
def record_stats(d):
    id = next(iter(d))
    print(id)
    submission = reddit.submission(id=id)
    
    submission.score
    submission.upvote_ratio
    submission.num_comments






