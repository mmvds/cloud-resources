import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

from src.db.db import get_connect, get_best_db


def get_data_from_db():
    conn = get_connect('remote')
    query = "SELECT timestamp, requests, response_time FROM statistics ORDER BY timestamp desc limit 80"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


data_df = get_data_from_db()


data_df['timestamp'] = pd.to_datetime(data_df['timestamp'])

plt.figure(figsize=(12, 6))
plt.plot(data_df['timestamp'], data_df['requests'], marker='o', linestyle='-')
plt.title('Requests per time')
plt.xlabel('Datetime')
plt.ylabel('Requests')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
