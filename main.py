from email import header
from wsgiref import headers
import sqlalchemy
import pandas as pd
from sqlalchemy.orm import sessionmaker
import requests
import json
from datetime import date, datetime
import datetime
import sqlite3

DATABASE_LOCATION = "sqlite:///my_played_tracks.sqlite"
USER_ID = "ur0r7ox89uc9dyoxk5br8joc1"
TOKEN = "BQDAiVAGGBXhPjGbe2Z1QQapj5kh_U6oZnmI9zmZBZrTEy8iQ9zZ2h3YnyxIx6AKfzSX01e29rwLLpq6Mb9ftvN1jxvSK3m1EDwJ_YhseJPMd-61jc0TWQULZxidU4XDYRyPSSp13oI88XQfg1eemW9vC90Z-TAE9XUJorQSU0FAvLFWA7HdxpFD-3Jt-SnFbbvc"


def check_if_valid_data(df: pd.DataFrame) -> bool:
    if df.empty:
        print("No songs downloaded. Finishing execution!")
        return False

    if pd.Series(df["played_at"]).is_unique:
        pass
    else:
        raise Exception("Primary Key Check is violated!")

    if df.isnull().values.any():
        raise Exception("Null values found!")

    #yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    #yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

    #timestamps = df["timestamp"].tolist()
    # for timestamp in timestamps:
        # if datetime.datetime.strptime(timestamp, "%Y-%m-%d") != yesterday:
        # raise Exception(
        # "At least one of the returned songs does not come from withing the last 24 hours")

    # return True


if __name__ == "__main__":

    # Extract part of the ETL process

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer {token}".format(token=TOKEN)
    }

    # Convert time to Unix timestamp in miliseconds
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=60)
    yesterday_unix_timestamp = int(yesterday.timestamp()) * 1000

    # Download all songs you've listened to "after yesterday", which means in the last 24 hours
    r = requests.get("https://api.spotify.com/v1/me/player/recently-played?after={time}".format(
        time=yesterday_unix_timestamp), headers=headers)

    data = r.json()

    print("############ Unsorted messy data ############")
    print(data)

    song_names = []
    artist_names = []
    played_at_list = []
    timestamps = []

    print("############ Relevant good data ############")
    # Extracting only the relevant bits of data from the json object
    for song in data["items"]:
        song_names.append(song["track"]["name"])
        artist_names.append(song["track"]["album"]["artists"][0]["name"])
        played_at_list.append(song["played_at"])
        timestamps.append(song["played_at"][0:10])

    # Prepare a dictionary in order to turn it into a pandas dataframe below
    song_dict = {
        "song_name": song_names,
        "artist_name": artist_names,
        "played_at": played_at_list,
        "timestamp": timestamps
    }

    song_df = pd.DataFrame(song_dict, columns=[
                           "song_name", "artist_name", "played_at", "timestamp"])

    if check_if_valid_data(song_df):
        print("Data valid, proceed to Load stage.")

    engine = sqlalchemy.create_engine(DATABASE_LOCATION)
    conn = sqlite3.connect("my_played_tracks.sqlite")
    cursor = conn.cursor()

    sql_query = """
    CREATE TABLE IF NOT EXISTS my_played_tracks(
        song_name VARCHAR(200),
        artist_name VARCHAR(200),
        played_at VARCHAR(200),
        timestamp VARCHAR(200),
        CONSTRAINT primary_key_constrain PRIMARY KEY (played_at)
    )
    """

    cursor.execute(sql_query)
    print("Opened database succesfully!")

    try:
        song_df.to_sql("my_played_tracks", engine,
                       index=False, if_exists="append")
    except:
        print("Data already exists in the database")

    conn.close()
    print("Database closed succesfully!")

    print(song_df)
