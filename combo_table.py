import sqlite3
import pandas as pd

# Connect to the SQLite database
with sqlite3.connect('github_repos.db') as conn:
    query = '''
    SELECT r.id AS repo_id, 
           r.name AS repo_name, 
           r.url AS repo_url, 
           r.stars AS repo_stars, 
           r.forks AS repo_forks, 
           r.language AS repo_language, 
           r.owner AS repo_owner, 
           r.created_at AS repo_created_at, 
           r.updated_at AS repo_updated_at,
           c.contributor AS contributor_name,
           c.contributions AS contributor_contributions
    FROM repositories r
    LEFT JOIN contributors c ON r.id = c.repo_id
    '''
    
    df_combined = pd.read_sql_query(query, conn)
    df_unique = df_combined.drop_duplicates(keep='first')


print(df_combined.head())

df_unique.to_csv('combined_repos_contributors.csv', index=False)
