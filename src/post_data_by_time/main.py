from dotenv import load_dotenv, dotenv_values
import os
import praw
import time
import heapq
import pickle

def preparation(sub):
    load_dotenv()
    
    reddit = praw.Reddit(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        user_agent=os.getenv('CLIENT_USER_AGENT'),
    )
    
    subreddit = reddit.subreddit(sub)
    
    heapq = None
    
    try:
        with open("heap.pkl", "rb") as f:
            heap = pickle.load(f)
            print("heap loaded:", heap)
    except FileNotFoundError:
        heap = []  # start with empty heap
        print("Starting new heap")    
        
    SERVICE_ACCOUNT_FILE = "service_account.json"
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1jBydaYtBvAHnDw-208FHfe61kNmHrSBMEtPgH5oX_io')
    worksheet = spreadsheet.worksheet("Data")
    submissions = worksheet.get("A2:A20") # 10 most recent posts
    submissions = [str(cell[0]) if cell else "" for cell in submissions]
    comment_worksheet = spreadsheet.worksheet("Comments")    
    
    return subreddit, worksheet, heap, submissions, reddit, comment_worksheet
            
### 1. find new submissions

def find_submissions(subreddit, worksheet, submissions, heap):
    for submission in subreddit.new(limit=10):
        if submission.id not in submissions and submission.link_flair_text == '[Deal/Sale]':
            # add to spreadsheet
           print(submission.id)
           time_posted = submission.created_utc
           worksheet.insert_row([submission.id, submission.title, time_posted], 2)
            # add the corresponding times in a queue
           add_times(heap, submission.id, time_posted)

### 2. add times

def add_times(heap, id, time_posted):
      for delay in [1800, 3600, 7200, 18000, 86400]: # 0.5, 1, 2, 5, 24 hours in seconds since time_posted is in unix.
        scheduled = time_posted + delay
        heapq.heappush(heap, (scheduled, id))
    

### 3. check if times have elapsed.
def check_times(heap, reddit, worksheet, comment_worksheet):
    print(heap)
    while heap and heap[0][0] <= time.time():
        scheduled_time, id = heapq.heappop(heap)
        save_heap(heap)
        record_stats(id, reddit, worksheet, comment_worksheet)
        print(f'popped {scheduled_time, id}')
    

### 4. record stats
def record_stats(id, reddit, worksheet, comment_worksheet):
    col_values = worksheet.col_values(1)
    for i, val in enumerate(col_values, start=2):  # start=2 because Sheets rows start at 1
        if str(val) == str(id):
            print(f"Found {id} in row {i-1}")
            submission = reddit.submission(id=id)
            # check which timeslot it belongs to
            for timeslot in [f'D{i-1}',f'G{i-1}', f'J{i-1}', f'M{i-1}', f'P{i-1}']:
                cell_value = worksheet.acell(timeslot).value
                if not cell_value:
                    write_relative(worksheet,timeslot, [submission.score, submission.upvote_ratio, submission.num_comments])
                    if(timeslot == f'P{i-1}'):
                      get_comments(submission, comment_worksheet=comment_worksheet)
                    break
            break
    

def write_relative(worksheet, start_cell, values):
     start_row, start_col = a1_to_rowcol(start_cell)
     end_col = start_col + len(values) - 1
     range_str = f"{rowcol_to_a1(start_row, start_col)}:{rowcol_to_a1(start_row, end_col)}"
     print(f'doing {values} at {range_str}')
     worksheet.update([values], range_str)   

# get the comments of the post
def get_comments(submission, comment_worksheet):
    submission.comments.replace_more(limit=None)
    rows = []
    for comment in submission.comments.list():
     rows.append([
        comment.id,
        comment.link_id,
        comment.parent_id,
        comment.score,
        comment.body,
     ])
    comment_worksheet.append_rows(rows)

def save_heap(heap):
    with open("heap.pkl", "wb") as f:
        pickle.dump(heap, f)
        print("heap saved to disk")   
        
## compiling 
def run(sub='frugalmalefashion'):
    subreddit, worksheet, heap, submissions, reddit, comment_worksheet = preparation(sub=sub)
    find_submissions(subreddit=subreddit, worksheet=worksheet, submissions=submissions, heap=heap) # finds new submissions, if so adds to queue.
    check_times(heap=heap, reddit=reddit,worksheet=worksheet,comment_worksheet= comment_worksheet) # checks to see if any of the times are up. If so, adds current stats to data. If 24 hours is up, adds all comment data.
    save_heap(heap)
run()
    
    
    








