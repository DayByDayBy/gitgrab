import tweepy
import pandas as pd

# need to sign up for a dev account, if those are still a thing with 'nu-twitter'
API_KEY = 'api_key'
API_SECRET_KEY = 'api_secret_key'
ACCESS_TOKEN = 'access_token'
ACCESS_TOKEN_SECRET = 'access_token_secret'

# authenticate
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
    keywords = ['Java', 'JavaScript', 'Typescript', 'C#', 'open source', 'developer']
    
    users = search_users(keywords, num_users=100)
    
    # dataframe for easier handling:
    df = pd.DataFrame(users)
    
    # save to CSV:
    df.to_csv('twitter_users.csv', index=False)
    print("User data saved to twitter_users.csv")

if __name__ == "__main__":
    main()
