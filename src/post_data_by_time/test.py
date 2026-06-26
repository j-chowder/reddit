from dotenv import load_dotenv, dotenv_values
import os
import praw
from collections import deque
import time
import pickle

def preparation(sub = 'frugalmalefashion'):
    reddit = praw.Reddit(
        client_id='gQjbNsEWXE87igG_MOrZ6Q',
        client_secret='LpDE4VRU9lFcbxfYEp9nI2NJghXLCw',
        user_agent='r/fmf fetcher (by u/Daddypiuy)',
    )

    subreddit = reddit.subreddit(sub)

    submissions = []

    q = None
    
    try:
        with open("queue.pkl", "rb") as f:
            q = pickle.load(f)
            print("Queue loaded:", q)
    except FileNotFoundError:
        q = deque()  # start with empty queue
        print("Starting new queue")
    
    SERVICE_ACCOUNT_FILE = "service_account.json"
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1jBydaYtBvAHnDw-208FHfe61kNmHrSBMEtPgH5oX_io')
    worksheet = spreadsheet.worksheet("Data")
    comment_worksheet = spreadsheet.worksheet("Comments")    
    
    return subreddit, worksheet, q, submissions, reddit, comment_worksheet


def find_submissions(subreddit, worksheet, submissions, q):
    for submission in subreddit.new(limit=5):
        print(submission.title), print(submission.id), print(submission.url)
        if submission.id not in submissions:
            # add to spreadsheet
            time_posted = submission.created_utc
            worksheet.insert_row([submission.id, time_posted], 2)
            # add the corresponding times in a queue
            add_times(q, submission.id, time_posted)

### 2. add times

def add_times(q, id, time_posted):
    for times in [1800, 3600, 7200, 18000, 86400]: # 0.5, 1, 2, 5, 24 hours in seconds since time_posted is in unix.
        d = {id: time_posted + times}
        q.append(d)

### 3. check if times have elapsed.
def check_times(q, reddit, worksheet):
    print(q)
    while time.time() >= list(q[0].values())[0]:
        record_stats(q[0], reddit, worksheet)
        q.popleft()
    

### 4. record stats
def record_stats(d, reddit, worksheet, comment_worksheet):
    id = next(iter(d))
    print(id)
    
    col_values = worksheet.col_values(1)
    for i, val in enumerate(col_values, start=2):  # start=2 because Sheets rows start at 1
        if val == {id}:
            print(f"Found 'a' in row {i}")
            submission = reddit.submission(id=id)
            # check which timeslot it belongs to
            for timeslot in ['D2', 'G2', 'J2', 'M2', 'P2']:
                cell_value = worksheet.acell(timeslot).value
                if not cell_value:
                    write_relative(timeslot, [submission.score, submission.upvote_ratio, submission.num_comments])
                    if(timeslot == 'P2'):
                        get_comments(submission, comment_worksheet=comment_worksheet)
                    break
            break
    

def write_relative(start_cell, values):
     start_row, start_col = a1_to_rowcol(start_cell)
     end_col = start_col + len(values) - 1
     range_str = f"{rowcol_to_a1(start_row, start_col)}:{rowcol_to_a1(start_row, end_col)}"
     worksheet.update(range_str, [values])   

# get the comments of the post
def get_comments(submission, comment_worksheet):
    submission.comments.replace_more(limit=None)
    for comment in submission.comments.list():
        comment_worksheet.insert_row([comment.id, comment.link_id, comment.parent_id, comment.score, comment.body], 2)

def save_q(q):
    with open("queue.pkl", "wb") as f:
        pickle.dump(q, f)
        print("Queue saved to disk")   
     
## compiling 
def run():
    subreddit, worksheet, q, submissions, reddit, comment_worksheet = preparation()
    find_submissions(subreddit=subreddit, worksheet=worksheet, submissions=submissions, q=q) # finds new submissions, if so adds to queue.
    check_times(q=q, reddit=reddit, comment_worksheet=comment_worksheet) # checks to see if any of the times are up. If so, adds current stats to data. If 24 hours is up, adds all comment data.
    save_q(q) # saves the queue to disk