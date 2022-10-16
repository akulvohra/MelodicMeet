import logging
import os
import psycopg
from psycopg.errors import ProgrammingError


class Database:
    def __init__(self, database_url):
        self.conn = psycopg.connect(database_url, application_name="$ docs_quickstart_python")
    
    def create_db_table(self):
        with self.conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS users (
                email STRING UNIQUE,
                username STRING,
                lat FLOAT,
                long FLOAT,
                acousticness FLOAT,
                danceability FLOAT,
                duration FLOAT,
                energy FLOAT,
                instrumentalness FLOAT,
                key FLOAT,
                loudness FLOAT,
                mode FLOAT,
                speechiness FLOAT,
                tempo FLOAT,
                timesig FLOAT,
                valence FLOAT,
                toke STRING
            )""")
            self.conn.commit()


    
    def show_values(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM users")
            rows = cur.fetchall()
            for row in rows:
                print([str(cell) for cell in row])

    def return_values(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM users")
            rows = cur.fetchall()
            return rows

    def return_value_for_email(self, email, column):
        rv = self.return_values()
        for user in rv:
            if user[0] == email:
                return user[column]


    def add_user(self, email, username, lat, long, feat_avgs, toke):
        email = email.replace("@", "_at_")
        with self.conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO users
                (
                    email,
                    username,
                    lat,
                    long,
                    acousticness,
                    danceability,
                    duration,
                    energy,
                    instrumentalness,
                    key,
                    loudness,
                    mode,
                    speechiness,
                    tempo,
                    timesig,
                    valence,
                    toke
                )
                VALUES
                (
                    '{email}',
                    '{username}',
                    {lat},
                    {long},
                    {feat_avgs['acousticness']},
                    {feat_avgs['danceability']},
                    {feat_avgs['duration_ms']},
                    {feat_avgs['energy']},
                    {feat_avgs['instrumentalness']},
                    {feat_avgs['key']},
                    {feat_avgs['loudness']},
                    {feat_avgs['mode']},
                    {feat_avgs['speechiness']},
                    {feat_avgs['tempo']},
                    {feat_avgs['time_signature']},
                    {feat_avgs['valence']},
                    '{toke}'
                )
                ON CONFLICT (email)
                DO UPDATE SET (
                    username,
                    lat,
                    long,
                    acousticness,
                    danceability,
                    duration,
                    energy,
                    instrumentalness,
                    key,
                    loudness,
                    mode,
                    speechiness,
                    tempo,
                    timesig,
                    valence,
                    toke
                ) = 
                (
                    excluded.username,
                    excluded.lat,
                    excluded.long,
                    excluded.acousticness,
                    excluded.danceability,
                    excluded.duration,
                    excluded.energy,
                    excluded.instrumentalness,
                    excluded.key,
                    excluded.loudness,
                    excluded.mode,
                    excluded.speechiness,
                    excluded.tempo,
                    excluded.timesig,
                    excluded.valence,
                    excluded.toke
                )
            """)
            self.conn.commit()








def exec_statement(conn, stmt):
    with conn.cursor() as cur:
        cur.execute(stmt)
        # row = cur.fetchone()
        conn.commit()
        # if row: print(row[0])



def showall():

    datab = Database(os.environ["DATABASE_URL"])
    datab.show_values()
# #     # Connect to CockroachDB
#      connection = psycopg.connect(os.environ["DATABASE_URL"], application_name="$ docs_quickstart_python")
#      statements = [
# #         # Clear out any existing data
#         "DROP TABLE IF EXISTS users",
# #         # # CREATE the messages table
# #         # "CREATE TABLE IF NOT EXISTS messages (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), message STRING)",
# #         # # INSERT a row into the messages table
# #         # "INSERT INTO messages (message) VALUES ('Hello world!')",
# #         # # SELECT a row from the messages table
# #         # "SELECT message FROM messages"
#      ]

#      for statement in statements:
#          exec_statement(connection, statement)

# #     # Close communication with the database
#      connection.close()

def clear_table():
    connection = psycopg.connect(os.environ["DATABASE_URL"], application_name="$ docs_quickstart_python")
    statements = [
        "DROP TABLE IF EXISTS users"
    ]
    for statement in statements:
        exec_statement(connection, statement)

    connection.close()



if __name__ == "__main__":
    #showall()
    clear_table()