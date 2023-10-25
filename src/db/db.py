import sqlite3
from datetime import datetime
from logging import config as logging_config, getLogger

import psycopg2

from src.core.config import app_settings
from src.core.logger import LOGGING

logging_config.dictConfig(LOGGING)

log = getLogger(__name__)


def get_connect(db_type: str = 'local', db_path: str = '') -> sqlite3.Connection | psycopg2.extensions.connection:
    if db_type == 'local':
        conn = sqlite3.connect(db_path + app_settings.db_name)
    else:
        conn = psycopg2.connect(dbname=app_settings.pg_db_name, user=app_settings.pg_user,
                                password=app_settings.pg_password, host=app_settings.pg_host, connect_timeout=3)
        conn.set_client_encoding('UTF8')
    return conn


def get_placeholder(db_type: str = 'local') -> str:
    if db_type == 'local':
        return '?'
    return '%s'


def get_best_db(db_path: str = '') -> str:
    min_sqlite_ts_limit3 = None
    min_pg_ts_limit3 = None

    try:
        sqlite_connect = get_connect('local', db_path)
        cursor = sqlite_connect.cursor()
        cursor.execute('SELECT min(timestamp) '
                       'FROM (SELECT timestamp FROM statistics ORDER BY timestamp desc limit 3) as t1')
        min_sqlite_ts_limit3 = cursor.fetchone()[0]
        if sqlite_connect:
            sqlite_connect.close()
    except sqlite3.Error as e:
        log.debug(f'DB Error: {e}')

    try:
        pg_connect = get_connect('remote')
        cursor = pg_connect.cursor()
        cursor.execute('SELECT min(timestamp) '
                       'FROM (SELECT timestamp FROM statistics ORDER BY timestamp desc limit 3) as t1')
        min_pg_ts_limit3 = cursor.fetchone()[0]
        if pg_connect:
            pg_connect.close()
    except psycopg2.Error as e:
        log.debug(f'DB Error: {e}')

    if min_sqlite_ts_limit3 is not None:
        min_sqlite_ts_limit3_dt = datetime.strptime(min_sqlite_ts_limit3, '%Y-%m-%dT%H:%M:%S')
    else:
        return 'remote'

    if min_pg_ts_limit3 is not None:
        min_pg_ts_limit3_dt = datetime.strptime(min_pg_ts_limit3, '%Y-%m-%dT%H:%M:%S')
    else:
        return 'local'

    if min_sqlite_ts_limit3 and min_pg_ts_limit3:
        if min_pg_ts_limit3_dt > min_sqlite_ts_limit3_dt:
            return 'remote'
        else:
            return 'local'

    return 'local'


def calculate_requests_difference(db_type: str = 'local') -> float:
    try:
        conn = get_connect(db_type)
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(timestamp) FROM statistics')
        max_timestamp = cursor.fetchone()[0]

        if max_timestamp is not None:
            max_timestamp_dt = datetime.strptime(max_timestamp, '%Y-%m-%dT%H:%M:%S')
            cursor.execute(f'''
                SELECT requests 
                FROM statistics
                WHERE timestamp = {get_placeholder(db_type)}
            ''', (max_timestamp,))
            requests_last = cursor.fetchone()[0]

            cursor.execute(f'''
                SELECT MAX(timestamp)
                FROM statistics
                WHERE timestamp < {get_placeholder(db_type)}
            ''', (max_timestamp,))
            timestamp_minutes_1t_ago = cursor.fetchone()[0]

            if timestamp_minutes_1t_ago is not None:
                cursor.execute(f'''
                    SELECT requests 
                    FROM statistics
                    WHERE timestamp = {get_placeholder(db_type)}
                ''', (timestamp_minutes_1t_ago,))
                requests_minutes_1t_ago = cursor.fetchone()[0]

                cursor.execute(f'''
                                SELECT MAX(timestamp)
                                FROM statistics
                                WHERE timestamp < {get_placeholder(db_type)}
                            ''', (timestamp_minutes_1t_ago,))
                timestamp_minutes_2t_ago = cursor.fetchone()[0]

                requests_minutes_2t_ago = None
                if timestamp_minutes_2t_ago is not None:
                    cursor.execute(f'''
                                        SELECT requests 
                                        FROM statistics
                                        WHERE timestamp = {get_placeholder(db_type)}
                                    ''', (timestamp_minutes_2t_ago,))
                    requests_minutes_2t_ago = cursor.fetchone()[0]

                if ((requests_last is not None) and (requests_minutes_1t_ago is not None)
                        and (requests_minutes_1t_ago > 0)):
                    time_1t_ago_dt = datetime.strptime(timestamp_minutes_1t_ago, '%Y-%m-%dT%H:%M:%S')
                    time_difference_1t_ago = max_timestamp_dt - time_1t_ago_dt
                    minutes_1t_ago = time_difference_1t_ago.total_seconds() / 60
                    difference_1t_ago = (requests_last - requests_minutes_1t_ago) / minutes_1t_ago
                    if ((requests_minutes_2t_ago is not None) and (requests_minutes_2t_ago > 0)
                            and (difference_1t_ago >= 0)):
                        time_2t_ago_dt = datetime.strptime(timestamp_minutes_2t_ago, '%Y-%m-%dT%H:%M:%S')
                        time_difference_2t_ago = time_1t_ago_dt - time_2t_ago_dt
                        minutes_2t_ago = time_difference_2t_ago.total_seconds() / 60
                        difference_2t_ago = (requests_minutes_1t_ago - requests_minutes_2t_ago) / minutes_2t_ago
                        velocity_1t_2t = difference_1t_ago - difference_2t_ago
                        if velocity_1t_2t > 0:
                            log.debug(
                                f'{requests_last=}, {requests_minutes_1t_ago=}, {requests_minutes_2t_ago=},'
                                f'{difference_1t_ago=}, {difference_2t_ago=}, {velocity_1t_2t=}')
                            save_log_message(
                                f'{requests_last=}, {requests_minutes_1t_ago=}, {requests_minutes_2t_ago=},'
                                f'{difference_1t_ago=}, {difference_2t_ago=}, {velocity_1t_2t=}',
                                current_timestamp=max_timestamp)
                            return difference_1t_ago + velocity_1t_2t

                    log.debug(f'{requests_last=}, {requests_minutes_1t_ago=}, {difference_1t_ago=}')
                    save_log_message(f'{requests_last=}, {requests_minutes_1t_ago=}, {difference_1t_ago=}',
                                     current_timestamp=max_timestamp)
                    return difference_1t_ago
        return 0

    except (sqlite3.Error, psycopg2.Error) as e:
        log.error(f'DB error: {e}')

    finally:
        if conn:
            conn.close()


def create_table_if_not_exists(conn: sqlite3.Connection | psycopg2.extensions.connection) -> None:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
    timestamp TEXT PRIMARY KEY,
    availability REAL,
    cost_total INTEGER,
    db_cpu INTEGER,
    db_cpu_load REAL,
    db_ram INTEGER,
    db_ram_load REAL,
    id INTEGER,
    last1 INTEGER,
    last15 INTEGER,
    last5 INTEGER,
    lastDay INTEGER,
    lastHour INTEGER,
    lastWeek INTEGER,
    offline_time INTEGER,
    online INTEGER,
    online_time INTEGER,
    requests INTEGER,
    requests_total INTEGER,
    response_time INTEGER,
    user_id INTEGER,
    user_name TEXT,
    vm_cpu INTEGER,
    vm_cpu_load REAL,
    vm_ram INTEGER,
    vm_ram_load REAL
);
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
        timestamp TEXT PRIMARY KEY,
        log_message TEXT
    );
    ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS servers (
            timestamp TEXT PRIMARY KEY,
            online_vm INTEGER,
            online_db INTEGER,
            offline_vm INTEGER,
            offline_db INTEGER
        );
        ''')
    conn.commit()


def insert_data(conn: sqlite3.Connection | psycopg2.extensions.connection, data: dict, db_type: str) -> None:
    cursor = conn.cursor()

    default_values = {
        'timestamp': '',
        'id': 0,
        'availability': 0.0,
        'cost_total': 0,
        'db_cpu': 0,
        'db_cpu_load': 0.0,
        'db_ram': 0,
        'db_ram_load': 0.0,
        'last1': 0,
        'last15': 0,
        'last5': 0,
        'lastDay': 0,
        'lastHour': 0,
        'lastWeek': 0,
        'online_time': 0,
        'response_time': 0,
        'vm_cpu': 0,
        'vm_cpu_load': 0.0,
        'vm_ram': 0,
        'vm_ram_load': 0.0
    }

    for field, default_value in default_values.items():
        if field not in data:
            data[field] = default_value
    if db_type == 'local':
        ignore_text = 'OR IGNORE'
        on_conflict_text = ''

    else:
        ignore_text = ''
        on_conflict_text = 'ON CONFLICT DO NOTHING'

    cursor.execute(f'''
        INSERT {ignore_text} INTO statistics (
            timestamp, availability, cost_total, db_cpu, db_cpu_load,
            db_ram, db_ram_load, id, last1, last15, last5, lastDay, lastHour,
            lastWeek, offline_time, online, online_time, requests,
            requests_total, response_time, user_id, user_name, vm_cpu,
            vm_cpu_load, vm_ram, vm_ram_load
        ) VALUES ({', '.join([get_placeholder(db_type)] * 26)}) {on_conflict_text}
    ''', (
        data['timestamp'], data['availability'], data['cost_total'], data['db_cpu'],
        data['db_cpu_load'], data['db_ram'], data['db_ram_load'], data['id'],
        data['last1'], data['last15'], data['last5'], data['lastDay'], data['lastHour'],
        data['lastWeek'], data['offline_time'], int(data['online']), data['online_time'],
        data['requests'], data['requests_total'], data['response_time'], data['user_id'],
        data['user_name'], data['vm_cpu'], data['vm_cpu_load'], data['vm_ram'], data['vm_ram_load']
    ))
    conn.commit()


def insert_servers(conn: sqlite3.Connection | psycopg2.extensions.connection,
                   resources: dict,
                   timestamp: str,
                   db_type: str) -> None:
    cursor = conn.cursor()
    online_vm = 0
    online_db = 0
    offline_vm = 0
    offline_db = 0

    for resource in resources:
        if not resource['failed'] and resource['ram_load'] > 0.0:
            if resource['type'] == 'vm':
                online_vm += 1
            else:
                online_db += 1
        else:
            if resource['type'] == 'vm':
                offline_vm += 1
            else:
                offline_db += 1

    if db_type == 'local':
        ignore_text = 'OR IGNORE'
        on_conflict_text = ''
    else:
        ignore_text = ''
        on_conflict_text = 'ON CONFLICT DO NOTHING'

    cursor.execute(f'''
        INSERT {ignore_text} INTO servers(
            timestamp, online_vm, online_db, offline_vm, offline_db
        ) VALUES ({', '.join([get_placeholder(db_type)] * 5)}) {on_conflict_text}
    ''', (
        timestamp, online_vm, online_db, offline_vm, offline_db
    ))
    conn.commit()


def save_new_stats(statistics: dict, resources: dict, db_type: str = 'local') -> None:
    conn = get_connect(db_type)
    create_table_if_not_exists(conn)
    insert_data(conn, statistics, db_type)
    insert_servers(conn, resources, statistics['timestamp'], db_type)
    conn.close()


def get_avg_last_requests(requests_amount: int) -> float:
    conn = get_connect(get_best_db())
    cursor = conn.cursor()
    cursor.execute(f'''SELECT
    avg(requests)
    from (select requests from statistics order by timestamp desc limit {requests_amount}) as t1;''')
    return cursor.fetchone()[0]


def save_log_message(log_message,
                     db_type: str = 'remote',
                     current_timestamp: str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")):
    try:
        if db_type == 'local':
            ignore_text = 'OR IGNORE'
            on_conflict_text = ''
        else:
            ignore_text = ''
            on_conflict_text = 'ON CONFLICT DO NOTHING'
        conn = get_connect(db_type)
        cursor = conn.cursor()
        cursor.execute(f'INSERT {ignore_text} INTO logs (timestamp, log_message) '
                       f'VALUES ({get_placeholder(db_type)}, {get_placeholder(db_type)}) {on_conflict_text}',
                       (current_timestamp, log_message))
        conn.commit()
        conn.close()
    except (sqlite3.Error, psycopg2.Error) as e:
        log.error(f"DB error: {e}")
