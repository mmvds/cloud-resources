import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

from src.db.db import get_connect, get_best_db


def get_data_from_db():
    conn = get_connect(get_best_db('../../'), '../../')
    query = '''SELECT timestamp, vm_ram_load, db_ram_load, vm_ram, db_ram FROM statistics 
                 ORDER BY  timestamp desc limit 50'''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


data_df = get_data_from_db()
data_df['timestamp'] = pd.to_datetime(data_df['timestamp'])

plt.figure(figsize=(12, 7))
last_datetime = data_df['timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')
plt.subplot(2, 1, 1)
plt.plot(data_df['timestamp'], data_df['vm_ram_load'], marker='o', linestyle='-', label='vm_ram_load')
plt.plot(data_df['timestamp'], data_df['db_ram_load'], marker='x', linestyle='-', label='db_ram_load')
plt.title(f'vm_ram_load and db_ram_load {last_datetime}')
plt.xlabel('Datetime')
plt.ylabel('RAM Load')
plt.grid(True)
plt.xticks(rotation=45)
plt.legend()

last_vm_ram_load = data_df['vm_ram_load'].iloc[0]
last_db_ram_load = data_df['db_ram_load'].iloc[0]

plt.text(data_df['timestamp'].iloc[0], last_vm_ram_load, f'vm_ram_load: {last_vm_ram_load}', va='bottom')
plt.text(data_df['timestamp'].iloc[0], last_db_ram_load, f'db_ram_load: {last_db_ram_load}', va='bottom')

plt.subplot(2, 1, 2)
plt.plot(data_df['timestamp'], data_df['vm_ram'], marker='s', linestyle='-', label='vm_ram')
plt.plot(data_df['timestamp'], data_df['db_ram'], marker='^', linestyle='-', label='db_ram')
plt.title(f'vm_ram and db_ram {last_datetime}')
plt.xlabel('Datetime')
plt.ylabel('RAM Usage')
plt.grid(True)
plt.xticks(rotation=45)
plt.legend()

last_vm_ram = data_df['vm_ram'].iloc[0]
last_db_ram = data_df['db_ram'].iloc[0]
last_timestamp = data_df['timestamp'].iloc[0]

plt.text(data_df['timestamp'].iloc[0], last_vm_ram, f'vm_ram: {last_vm_ram}', va='bottom')
plt.text(data_df['timestamp'].iloc[0], last_db_ram, f'db_ram: {last_db_ram}', va='bottom')
plt.text(data_df['timestamp'].iloc[0], last_timestamp, f'timestamp: {last_timestamp}', va='bottom')

plt.tight_layout()
plt.show()
