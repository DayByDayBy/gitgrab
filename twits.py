import tweepy
import pandas as pd
import json
from collections import Counter
from datetime import datetime

time_stamp = datetime.now().strftime("%Y%m%d_%H%M")


with open('config.json') as f:
    config = json.load(f)
API_KEY =  config['API_KEY']
API_SECRET_KEY = config['API_SECRET_KEY']
ACCESS_TOKEN = config['ACCESS_TOKEN']
ACCESS_TOKEN_SECRET = config['ACCESS_TOKEN_SECRET']

auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

def search_users(keywords, users_per_keyword = 10, min_followers = 1000):
    users = {}
    for keyword in keywords:
        keyword_users = []
        for tweet in tweepy.Cursor(api.search_tweets, q=keyword, lang='en', tweet_mode='extended').items(20):
            user = tweet.user
            if user.followers_count >= min_followers and user.screen_name not in users:
                if any(keyword in user.description.lower() for keyword in ['open source', 'programmer', 'machine learning', 'developer']):
                    users[user.screen_name] = {
                        'username': user.screen_name,
                        'name': user.name,
                        'description': user.description,
                        'followers_count': user.followers_count,
                        'keywords': [keyword],
                        'tweet_count': 1,
                        'like_count': tweet.favorite_count
                    }
                    keyword_users.append(user.screen_name)
                
            elif user.screen_name in users:
                users[user.screen_name]['keywords'].append(keyword)
                users[user.screen_name]['tweet_count'] += 1
                users[user.screen_name]['quote_count'] += tweet.quote_count
                users[user.screen_name]['like_count'] += tweet.favorite_count
                              
            if len(keyword_users) >= users_per_keyword:
                break
    return list(users.values())

def rank_users(users):
    for user in users:
        user['relevance_score']=(
                len(set(user['keywords'])) * 10 + 
                user['tweet_count'] * 2 + 
                (min(user['followers_count'], 10000) / 100)     * 5 +
                user['quote_count'] * 3 +
                user['like_count'] * 1
                )
    return sorted(users, key=lambda x: x['relevance_score'], reverse=True)


def main():
    keywords = ['Java', 'JavaScript', 'Typescript', 'C#', 'open source', 'github repo', 'coding', 'programming']
    users_per_keyword = 10
    min_followers = 1000
    
    users = search_users(keywords, users_per_keyword, min_followers)
    ranked_users = rank_users(users)
        
    # dataframe for handling:
    df = pd.DataFrame(ranked_users)
    df['keywords'] = df['keywords'].apply(lambda x: ', '.join(set(x)))
    df = df.sort_values('relevance_score', ascending=False)
    
    # save to CSV:
    df.to_csv(f'{time_stamp}twitter_users.csv', index=False)
    print(f"User data saved to twitter_users.csv. total foound {len(df)}")
    
    print('\ntop ten users: "')
    print(df[['username', 'name', 'followers_count', 'keywords', 'relevance_score']].head(10).to_string(index=False))

if __name__ == "__main__":
    main()
