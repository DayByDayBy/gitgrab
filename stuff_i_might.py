
    
    
    
    
    
        # supabase_conn = psycopg2.connect(**supabase_params)
    # try:
    #     with supabase_conn.cursor() as supa_cursor:
    #         create_tables(supa_cursor)
    #     supabase_conn.commit()
    # except Exception as e:
    #     print(f'supabase setup error: {e}')
    #     supabase_conn.close()
    #     return
    
    # local_conn = sqlite3.connect(LOCAL_DB_FILE)
    # local_cursor = local_conn.cursor()
    
    
    # ----------------------------------------------------------------
    
    
#     supabase_params = {
#     "dbname": "postgres",   
#     "user": "postgres.wwksawhpoujfktuzghux",     
#     "password": "",  
#     "host": "aws-0-us-east-1.pooler.supabase.com",        
#     "port": "5432"
# }


# ------------------------------------------------


    #             try:
    #                 local_cursor.execute("SELECT * FROM repositories")
    #                 repos = local_cursor.fetchall()
    #                 for repo in repos:
    #                     supa_cursor.execute('''
    #                                             INSERT INTO repositories (id, name, url, stars, forks, language, owner, created_at, updated_at)
    #                                             VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
    #                                             ON CONFLICT (id) DO NOTHING;
    #                                             ''', repo)
    #                 local_cursor.execute("SELECT * FROM contributors")
    #                 contributors = local_cursor.fetchall()
    #                 for contributor in contributors:
    #                     supa_cursor.execute('''
    #                                             INSERT INTO contributors (repo_id, contributor, contributions)
    #                                             VALUES(%s, %s, %s);
    #                                             ''', contributor[1:])
    #                 supabase_conn.commit()
    #             except Exception as e:
    #                 print(f'error copying to supa: {e}')
    #                 supabase_conn.rollback()
    #             finally:
    #                 supa_cursor.close()
    

       
    # except Exception as e:
    #     print(f'error: {e}')
    #     local_conn.rollback()
    # else:
    #     local_conn.commit()