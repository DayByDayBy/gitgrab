import requests
import time
import sqlite3
import csv
from datetime import datetime
import json 
import os

TIME_STAMP = datetime.now().strftime("%Y%m%d_%H%M")

NUM_REPOS = 200
NUM_CONTRIBUTORS = 5 
with open('config.json') as f:
    config = json.load(f)
api_key = config['GITHUB_TOKEN']
HEADERS = {"Authorization": f"token {api_key}"}
LANGUAGES = ["java", "c#", "typescript", "javascript"]
LOCAL_DB_FILE = 'new_github_repos.db'
CSV_OUTPUT_FILE = f'{TIME_STAMP}_github_repos.csv'
MAX_RETRIES = 5



# create tables (if they don't exist)
def create_tables(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repositories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        url TEXT,
        stars INTEGER,
        forks INTEGER,
        language TEXT,
        owner TEXT,
        created_at TEXT,
        updated_at TEXT
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contributors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo_id INTEGER,
        contributor TEXT,
        contributions INTEGER,
        FOREIGN KEY (repo_id) REFERENCES repositories (id)
        );
    ''')
    
# fetch repos:
def fetch_repos(language, sort_by="stars", per_page=100, page=1):
    retries = MAX_RETRIES
    url = f"https://api.github.com/search/repositories?q=stars:>1+language:{language}&sort={sort_by}&order=desc&per_page={per_page}&page={page}"
    
    while retries > 0:
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 403 and 'X-RateLimit-Reset' in response.headers:
            reset_time = int(response.headers['X-RateLimit-Reset'])
            sleep_time = max(reset_time - time.time(), 0)
            print(f'rate limited, bro. sleeping it off for {sleep_time / 60:.2f} minutes')
            time.sleep(sleep_time + 5)
            continue
        
        if response.status_code == 200:
            return response.json().get('items', [])
        
        print(f' error {response.status_code}: {response.text}')
        retries -= 1
        if retries > 0:
            time.sleep(2)

    print('retry limit reached, likely error/issue')
    return []



# fetch contributors for a repo:
def fetch_contributors(owner, repo, limit):
    retries = MAX_RETRIES
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page={limit}"
    rate_limit_retries = 0
    while retries > 0:
        response = requests.get(url, headers=HEADERS)
        retries -= 1
        if response.status_code == 403 and 'X-RateLimit-Reset' in response.headers:
            rate_limit_retries += 1
            if rate_limit_retries > MAX_RETRIES:
                print("Max rate limit retries reached. exiting.")
                return []
            reset_time = int(response.headers['X-RateLimit-Reset'])
            sleep_time = max(reset_time - time.time(), 0)
            print(f'  rate limited, bro. sleeping it off for {sleep_time / 60:.2f}  minutes')
            time.sleep(sleep_time + 5)
            continue
        elif response.status_code == 200:
            contributors = response.json()[:limit]
            return contributors
        else:
            print(f'error: {response.status_code}: {response.text}')  
            return []
    return []      

# insert repositories into db
def insert_repo(cursor, repo_data):
    cursor.execute('''
            INSERT OR REPLACE INTO repositories (id, name, url, stars, forks, language, owner, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
        repo_data['id'], repo_data['name'], repo_data['html_url'], repo_data['stargazers_count'],
        repo_data['forks_count'], repo_data['language'], repo_data['owner']['login'],
        repo_data['created_at'], repo_data['updated_at']
    ))

# send contributors into db

def insert_contributors(cursor, repo_id, contributors):
    cursor.executemany('''
        INSERT OR REPLACE INTO contributors (repo_id, contributor, contributions)
        VALUES (?, ?, ?);
    ''', [(repo_id, contributor['login'], contributor['contributions']) for contributor in contributors])


# grabbing starred/forked repos:
def fetch_and_store_repos_by_criteria(cursor, language, sort_by, num_repos=NUM_REPOS):
    per_page = 30
    pages = (num_repos // per_page) + 1
    
    for page in range(1, pages+1):
        repos = fetch_repos(
            language,
            sort_by=sort_by, 
            per_page=per_page, 
            page=page)
        
        for repo in repos:
            insert_repo(cursor, repo)
            print(f"inserted repo: {repo['name']}")
            
            # fetch/insert contributors:
            contributors = fetch_contributors(repo['owner']['login'], repo['name'], NUM_CONTRIBUTORS)
            if contributors:
                insert_contributors(cursor, repo['id'], contributors)
                print(f"inserted contributors for: {repo['name']}")
                

def export_to_csv(cursor, filename):
    cursor.execute("SELECT * FROM repositories")
    repos = cursor.fetchall()
    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([i[0] for i in cursor.description])
        csv_writer.writerows(repos)
    

# the bit that does the thing:

def main():
    
    conn = sqlite3.connect(LOCAL_DB_FILE)
    cursor = conn.cursor()
    

    
    try:
        create_tables(cursor)
        conn.commit()

        for language in LANGUAGES:
                print(f'grabbing forky repos with {language}...')
                fetch_and_store_repos_by_criteria(cursor, language, "forks", num_repos= NUM_REPOS)
                conn.commit()
                print(f'grabbing starry repos with {language}...')
                fetch_and_store_repos_by_criteria(cursor, language, "stars", num_repos= NUM_REPOS)
                conn.commit()
        export_to_csv(cursor, CSV_OUTPUT_FILE)
        print(f'CSV exported to {CSV_OUTPUT_FILE}')
        
    except Exception as e:
        print(f'error: {e}')
        conn.rollback()
    else:
        conn.commit()
    finally:
        cursor.close()
        conn.close()
                

            
            
if __name__ == "__main__":
    main()
