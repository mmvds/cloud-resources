import time
from src.services.calculations import *
from src.services.services import *
from src.db.db import *


if __name__ == '__main__':
    wait_creation_minutes = 0
    time_to_refresh = 10
    while True:
        try:
            best_db = 'local'
            statistics = get_request('statistic')
            log.debug(statistics)
            resources = get_request('resource')

            save_new_stats(statistics=statistics, resources=resources, db_type='local')
            try:
                save_new_stats(statistics=statistics, resources=resources, db_type='remote')
            except psycopg2.Error as e:
                log.error(f'PG_DB Error {e}')
            try:
                best_db = get_best_db()
            except (sqlite3.Error, psycopg2.Error) as e:
                log.error(f'DB Error {e}')

            max_load = max(statistics['db_cpu_load'],
                           statistics['db_ram_load'],
                           statistics['vm_cpu_load'],
                           statistics['vm_ram_load'])

            minute_diff = calculate_requests_difference(best_db)

            calc_requests = max(statistics['requests'], 1)
            if minute_diff > 0:
                calc_requests = round(calc_requests + minute_diff * 10)
            else:
                calc_requests = max(calc_requests, get_avg_last_requests(4))

            optimal_resources = res_calc(calc_requests)
            print(optimal_resources)
            log.debug(f'requests = {statistics["requests"]}, {calc_requests=}')
            log.debug(f'{optimal_resources}')
            prices = get_request('price')

            log.debug(resources)
            res_with_prices = add_price_id(resources, prices)
            print(f'{res_with_prices=}')
            vm_servers, _ = minimize_cost(prices, optimal_resources['vm_cpu'], optimal_resources['vm_ram'], 'vm')
            # print(f'{vm_servers=}')
            db_servers, _ = minimize_cost(prices, optimal_resources['db_cpu'], optimal_resources['db_ram'], 'db')
            desired_servers = vm_servers + db_servers
            print(f'{desired_servers=}')
            prices = get_request('price')
            created_resources = create_resources_if_needed(res_with_prices, prices, desired_servers)
            if created_resources:
                wait_creation_minutes = 3
                resources = get_request('resource')
                res_with_prices = add_price_id(resources, prices)
                log.debug(created_resources)
            if wait_creation_minutes <= 0:
                check_and_delete_resources(res_with_prices, desired_servers)
        except Exception as err:
            log.error(f'Got error {err}')
            save_log_message(f'Got error {err}')
        time.sleep(time_to_refresh)
        wait_creation_minutes -= (time_to_refresh / 60)
