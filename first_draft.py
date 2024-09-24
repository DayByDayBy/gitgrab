import requests
import os

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

def get_repo_contributors(repo_owner, repo_name):
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contributors'
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []

def get_user_profile(username):
    url = f'https://api.github.com/users/{username}'
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def main():
    repos = [
        ('DayByDayBy', 'leaky_windows'),
    ]
    
        
    
    
    
    for owner, repo in repos:
        print(f"Fetching contributors for {owner}/{repo}")
        contributors = get_repo_contributors(owner, repo)
        
        for contributor in contributors:
            username = contributor['login']
            profile = get_user_profile(username)
            
            if profile and profile.get('email'):
                print(f"User: {username}, Email: {profile['email']}")
            elif profile and profile.get('blog'):
                print(f"User: {username}, Website: {profile['blog']}")
            else:
                print(f"User: {username}, No public contact info available")

if __name__ == "__main__":
    main()
