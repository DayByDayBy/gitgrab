import tweepy
import pandas as pd
import json
from datetime import datetime
import time
from collections import defaultdict
import os

time_stamp = datetime.now().strftime("%Y%m%d_%H%M")
output_file = f'{time_stamp}_twitter_users.csv'

with open('config.json') as f:
    config = json.load(f)

client = tweepy.Client(
    bearer_token=config['BEARER_TOKEN'],
    consumer_key=config['API_KEY'],
    consumer_secret=config['API_SECRET_KEY'],
    access_token=config['ACCESS_TOKEN'],
    access_token_secret=config['ACCESS_TOKEN_SECRET']
)

def rate_limited_request(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except tweepy.TooManyRequests:
        print("Rate limit reached. Waiting for 15 minutes.")
        time.sleep(15 * 60)
        return func(*args, **kwargs)
    except tweepy.TwitterServerError:
        print("Twitter server error. Waiting for 1 minute.")
        time.sleep(60)
        return func(*args, **kwargs)

def fetch_users(usernames):
    users = rate_limited_request(
        client.get_users,
        usernames=usernames,
        user_fields=['description', 'public_metrics']
    )
    return users.data if users else []

def search_users(keywords, max_users=200):
    all_users = []
    user_set = set()
    
    for keyword in keywords:
        query = f"{keyword} -is:retweet"
        for tweet in tweepy.Paginator(client.search_recent_tweets, query=query, 
                                      tweet_fields=['author_id'], max_results=100).flatten(limit=1000):
            if tweet.author_id not in user_set:
                user_set.add(tweet.author_id)
                all_users.append(tweet.author_id)
            
            if len(all_users) >= max_users:
                break
        
        if len(all_users) >= max_users:
            break
    
    return all_users[:max_users]


def process_users(user_ids, keywords, save_batch_size=20):
    users_data = []
    api_calls = 0
    for i in range(0, len(user_ids), 100):
        batch = user_ids[i:i+100]
        users = fetch_users(batch)
        api_calls += 1
        
        for user in users:
            user_data = {
                'username': user.username,
                'name': user.name,
                'description': user.description,
                'followers_count': user.public_metrics['followers_count'],
                'keywords': [kw for kw in keywords if kw.lower() in user.description.lower()],
            }
            
            users_data.append(user_data)
            
            if len(users_data) % save_batch_size == 0:
                save_to_csv(users_data[-save_batch_size:], output_file, append=(len(users_data) > save_batch_size))
                print(f'saved batch of {save_batch_size} users.  processed so far: {len(users_data)}')
                      
    remaining = len(users_data) % save_batch_size
    if remaining > 0:
        save_to_csv(users_data[-remaining:], output_file, append=True)
        print(f'saved final batch of {remaining} users.  total processed: {len(users_data)}')
        
    print(f'total API calls for user-search: {api_calls}')
    return users_data

def save_to_csv(data, filename, append=False):
    df = pd.DataFrame(data)
    df['keywords'] = df['keywords'].apply(lambda x: ', '.join(set(x)))
    mode = 'a' if append else 'w'
    header = not append
    df.to_csv(filename, mode=mode, header=header, index=False)


def rank_users(users):
    for user in users:
        user['relevance_score'] = (
            len(user['keywords']) * 10 +
            min(user['followers_count'], 10000) / 100
        )
    return sorted(users, key=lambda x: x['relevance_score'], reverse=True)



def main():
    
    keywords = ['Java', 'TypeScript', 'C#', 'open source', 'coding', 'programming']
    max_users = 200
    save_batch_size = 20


    print("Searching for users...")
    user_ids = search_users(keywords, max_users)
    print(f"Found {len(user_ids)} unique users")

    print("Fetching user details...")
    users = process_users(user_ids, keywords)
    print(f"Processed {len(users)} users")

    print("Ranking users...")
    ranked_users = rank_users(users)


# save and rank
    save_to_csv(ranked_users, output_file)
    print(f"Final ranked user data saved to {output_file}")

    print('\nTop ten users:')
    df = pd.read_csv(output_file)
    print(df[['username', 'name', 'followers_count', 'keywords', 'relevance_score']].head(10).to_string(index=False))

if __name__ == "__main__":
    main()