import pandas as pd
import matplotlib.pyplot as plt

from src.db.db import get_connect, get_best_db


def get_data_from_db():
    conn = get_connect(get_best_db('../../'), '../../')
    query = '''SELECT timestamp, vm_cpu_load, db_cpu_load, vm_cpu, db_cpu FROM statistics 
                 ORDER BY  timestamp desc limit 200'''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


data_df = get_data_from_db()
data_df['timestamp'] = pd.to_datetime(data_df['timestamp'])

plt.figure(figsize=(12, 7))
last_datetime = data_df['timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')
plt.subplot(2, 1, 1)
plt.plot(data_df['timestamp'], data_df['vm_cpu_load'], marker='o', linestyle='-', label='vm_cpu_load')
plt.plot(data_df['timestamp'], data_df['db_cpu_load'], marker='x', linestyle='-', label='db_cpu_load')
plt.title(f'vm_cpu_load and db_cpu_load {last_datetime}')
plt.xlabel('Datetime')
plt.ylabel('RAM Load')
plt.grid(True)
plt.xticks(rotation=45)
plt.legend()

last_vm_cpu_load = data_df['vm_cpu_load'].iloc[0]
last_db_cpu_load = data_df['db_cpu_load'].iloc[0]

plt.text(data_df['timestamp'].iloc[0], last_vm_cpu_load, f'vm_cpu_load: {last_vm_cpu_load}', va='bottom')
plt.text(data_df['timestamp'].iloc[0], last_db_cpu_load, f'db_cpu_load: {last_db_cpu_load}', va='bottom')

plt.subplot(2, 1, 2)
plt.plot(data_df['timestamp'], data_df['vm_cpu'], marker='s', linestyle='-', label='vm_cpu')
plt.plot(data_df['timestamp'], data_df['db_cpu'], marker='^', linestyle='-', label='db_cpu')
plt.title(f'vm_cpu and db_cpu {last_datetime}')
plt.xlabel('Datetime')
plt.ylabel('RAM Usage')
plt.grid(True)
plt.xticks(rotation=45)
plt.legend()

last_vm_cpu = data_df['vm_cpu'].iloc[0]
last_db_cpu = data_df['db_cpu'].iloc[0]
last_timestamp = data_df['timestamp'].iloc[0]

plt.text(data_df['timestamp'].iloc[0], last_vm_cpu, f'vm_cpu: {last_vm_cpu}', va='bottom')
plt.text(data_df['timestamp'].iloc[0], last_db_cpu, f'db_cpu: {last_db_cpu}', va='bottom')
plt.text(data_df['timestamp'].iloc[0], last_timestamp, f'timestamp: {last_timestamp}', va='bottom')

plt.tight_layout()
plt.show()
