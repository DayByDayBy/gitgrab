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
LOCAL_DB_FILE = 'github_repos.db'
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
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_repos (
            id INTEGER PRIMARY KEY,
            language TEXT,
            sort_by TEXT
            );
        ''')

def insert_processed_repo(cursor, repo_id, language, sort_by):
    cursor.execute('''
                INSERT OR REPLACE INTO processed_repos (id, language, sort_by)
                VALUES (?,?,?)
            ''', (repo_id, language, sort_by))    
    
def get_processed_repos(cursor, language, sort_by):
    cursor.execute('''
                SELECT id FROM processed_repos
                WHERE language = ? AND sort_by = ?
            ''', (language, sort_by))
    return set(row[0] for row in cursor.fetchall())
    
    
    
def api_call_and_retry(url, headers, max_retries=MAX_RETRIES):
    
    retries = max_retries
    while retries > 0:
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 403:
                if 'X-RateLimit-Reset' in response.headers:
                    reset_time = int(response.headers['X-RateLimit-Reset'])
                    current_time = int(time.time())
                    sleep_time = max((reset_time -  current_time), 0)
                    if sleep_time > 0:
                        sleep_minutes = sleep_time / 60
                        print(f'rate limited, bro. sleeping it off for {sleep_minutes:.2f} minutes')
                        time.sleep(sleep_time)
                        continue
                else:
                    print('403 forbidden received without rate limit info. retrying with backoff.')
                    backoff = 2 ** (max_retries - retries) 
                    print(f'Retrying in {backoff} seconds... ({retries} retries left)')
                    time.sleep(backoff)
                    retries -= 1
                    continue
            elif response.status_code == 200:
                return response.json()
            else:
                print(f'error: {response.status_code}: {response.text}')
                
        except requests.exceptions.RequestException as e:
            print(f'request failure: {e}')
            
        retries -= 1
        if retries > 0:
            backoff = 2 ** (max_retries - retries)     
            print(f'Retrying in {backoff} seconds... ({retries} retries left)')
            time.sleep(backoff)
            
           
    print('retries exhausted. script exit.')
    return None
    
    
    
# fetch repos:
def fetch_repos(language, sort_by="stars", per_page=100, page=1):
    url = f"https://api.github.com/search/repositories?q=stars:>1+language:{language}&sort={sort_by}&order=desc&per_page={per_page}&page={page}"
    response = api_call_and_retry(url, HEADERS)
    return response.get('items', []) if response else []


# fetch contributors for a repo:
def fetch_contributors(owner, repo, limit):
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page={limit}"
    response = api_call_and_retry(url, HEADERS)
    return response[:limit] if response else []
            

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
    processed_repos = get_processed_repos(cursor, language, sort_by)
    
    for page in range(1, pages+1):
        repos = fetch_repos(
            language,
            sort_by=sort_by, 
            per_page=per_page, 
            page=page)
        
        if not repos:
            break
        
        for repo in repos:
            if repo['id'] in processed_repos:
                print(f"skipping prev inserted repo: {repo['name']}")
                continue
            
            try:
                insert_repo(cursor, repo)
                print(f"inserted repo: {repo['name']}")       
                     
                contributors = fetch_contributors(repo['owner']['login'], repo['name'], NUM_CONTRIBUTORS)
                if contributors:
                    insert_contributors(cursor, repo['id'], contributors)
                    print(f"inserted contributors for: {repo['name']}")
                insert_processed_repo(cursor, repo['id'], language, sort_by)
                cursor.connection.commit()
            
            except Exception as e:
                print(f"error processing repo {repo['name']}: {e}")
                cursor.connection.rollback()  
                continue
                
                
# CSV save                
def export_to_csv(cursor, filename):
    cursor.execute("SELECT * FROM repositories")
    repos = cursor.fetchall()
    with open(filename, 'a', newline='') as csvfile:
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
            for sort_by in ["forks", "stars"]:
            
                print(f'grabbing high {sort_by} repos with {language}...')
                fetch_and_store_repos_by_criteria(cursor, language, sort_by, num_repos= NUM_REPOS)
        
        export_to_csv(cursor, CSV_OUTPUT_FILE)
        print(f'CSV exported to {CSV_OUTPUT_FILE}')
        
    except Exception as e:
        print(f'error: {e}')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
            
if __name__ == "__main__":
    main()
