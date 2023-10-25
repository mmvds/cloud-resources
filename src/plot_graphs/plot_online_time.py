import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

from src.services.services import *
from src.db.db import get_connect, get_best_db


def get_data_from_db():
    conn = get_connect(get_best_db('../../'), '../../')
    query = "SELECT timestamp, online_time FROM statistics ORDER BY timestamp desc limit 50"
    # query = "SELECT timestamp, online_time FROM statistics WHERE timestamp > '2023-10-18T09:00:00'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


data_df = get_data_from_db()

data_df['timestamp'] = pd.to_datetime(data_df['timestamp'])
print(data_df['online_time'].iloc[0])
plt.figure(figsize=(12, 6))
plt.plot(data_df['timestamp'], data_df['online_time'], marker='o', linestyle='-')
plt.title('online_time')
plt.xlabel('Datetime')
plt.ylabel('online_time')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

statistics = get_request('statistic')
print(statistics)

resource = get_request('resource')
for r in resource:
    print(r)
