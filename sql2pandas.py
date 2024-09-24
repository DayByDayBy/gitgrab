import sqlite3
import pandas as pd

conn = sqlite3.connect('github_repos.db')
query = "SELECT * FROM contributors WHERE contributor IS NOT NULL"
df = pd.read_sql_query(query, conn)
conn.close()

pd.set_option('display.max_columns', None)

df_unique = df.drop_duplicates(subset='contributor', keep='first')
df_sorted = df_unique.sort_values(by='contributions', ascending=False)
df_filtered = df_sorted[df_sorted['contributions'] >= 100]


df_filtered.to_csv('contributors_long_list.csv')

