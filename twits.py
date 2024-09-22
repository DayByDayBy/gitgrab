import tweepy
import pandas as pd
import json

with open('config.json') as f:
    config = json.load(f)
API_KEY =  config['API_KEY']
API_SECRET_KEY = config['API_SECRET_KEY']
ACCESS_TOKEN = config['ACCESS_TOKEN']
ACCESS_TOKEN_SECRET = config['ACCESS_TOKEN_SECRET']

auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

def search_users(keywords, num_users=100):
    users = []
    for keyword in keywords:
        for tweet in tweepy.Cursor(api.search, q=keyword, lang='en').items(num_users):
            user = tweet.user
            if user.screen_name not in [u['username'] for u in users]:
                users.append({
                    'username': user.screen_name,
                    'name': user.name,
                    'description': user.description,
                    'followers_count': user.followers_count
                })
    return users

def main():
    # define keywords based on programming languages/open-source/etc
    keywords = ['Java', 'JavaScript', 'Typescript', 'C#', 'open source', 'github repo']
    
    users = search_users(keywords, num_users=100)
    
    # dataframe for easier handling:
    df = pd.DataFrame(users)
    
    # save to CSV:
    df.to_csv('twitter_users.csv', index=False)
    print("User data saved to twitter_users.csv")

if __name__ == "__main__":
    main()
