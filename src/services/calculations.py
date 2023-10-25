from collections import Counter
from itertools import product
from logging import config as logging_config, getLogger

from src.core.logger import LOGGING
from src.services.services import *

logging_config.dictConfig(LOGGING)

log = getLogger(__name__)

plan_percent = 0.9

run_costs = {'vm': {'cpu': 0.05 / plan_percent, 'ram': 0.3 / plan_percent},
             'db': {'cpu': 0.05 / plan_percent, 'ram': 0.5 / plan_percent},
             }


def res_calc(requests_amount: float) -> dict:
    requests_amount = 50 + requests_amount / plan_percent
    required_resources = {'vm_ram': requests_amount * 0.005,
                          'vm_cpu': requests_amount * 0.001,
                          'db_ram': requests_amount * 0.001,
                          'db_cpu': requests_amount * 0.001,
                          }
    return required_resources


def minimize_cost(servers: list, cpu_req: float, ram_req: float, type_req: str) -> (list, float):
    # filtered_servers = [server for server in servers if server['type'] == type_req]
    filtered_servers = [server for server in servers
                        if (((server['type'] == type_req) and (server['type'] == 'vm')
                             and (server['cost'] in [3, 5, 10, 20, 40]))
                            or ((server['type'] == type_req) and (server['type'] == 'db')
                                and (server['cost'] in [4, 9, 17, 30, 44])))]
    for server in filtered_servers:
        server['cpu'] -= run_costs[type_req]['cpu']
        server['ram'] -= run_costs[type_req]['ram']
    best_cost = float('inf')
    best_solution = None

    def calculate_cost(calc_solution: list) -> float:
        total_cost = sum(server['cost'] * calc_solution[i] for i, server in enumerate(filtered_servers))
        return total_cost

    max_cpu = max(1, cpu_req // min(server['cpu'] for server in filtered_servers))
    max_ram = max(1, ram_req // min(server['ram'] for server in filtered_servers))
    max_quantities = [max(max_cpu // server['cpu'], max_ram // server['ram']) + 1 for server in
                      filtered_servers]

    for solution in product(*[range(int(max_qty) + 1) for max_qty in max_quantities]):
        total_cpu = sum(server['cpu'] * solution[i] for i, server in enumerate(filtered_servers))
        total_ram = sum(server['ram'] * solution[i] for i, server in enumerate(filtered_servers))

        if total_cpu >= cpu_req and total_ram >= ram_req:
            current_cost = calculate_cost(solution)
            if current_cost < best_cost:
                best_cost = current_cost
                best_solution = solution

    server_ids = [server['id'] for i, server in enumerate(filtered_servers) for _ in range(best_solution[i])]

    return server_ids, best_cost


def add_price_id(resources: list, prices: list) -> list:
    price_id_map = {}
    for price in prices:
        key = (price['cpu'], price['ram'], price['type'])
        price_id_map[key] = price['id']

    for resource in resources:
        key = (resource['cpu'], resource['ram'], resource['type'])
        price_id = price_id_map.get(key)
        if price_id is not None:
            resource['price_id'] = price_id
    return resources


def create_resources_if_needed(resources: list, prices: list, desired_servers: list) -> list:
    created_resources = []

    existing_resources = Counter(resource.get('price_id') for resource in resources)

    for price_id in desired_servers:
        count_in_resources = existing_resources.get(price_id, 0)
        if count_in_resources < desired_servers.count(price_id):
            new_resource_data = {
                'cpu': None,
                'ram': None,
                'type': None
            }

            for price in prices:
                if price['id'] == price_id:
                    new_resource_data['cpu'] = price['cpu']
                    new_resource_data['ram'] = price['ram']
                    new_resource_data['type'] = price['type']
                    break
            log.debug(f'Created {new_resource_data}')
            created_resources.append(new_resource_data)
            post_request('resource', new_resource_data)
            existing_resources[price_id] += 1
    return created_resources


def check_and_delete_resources(resources: list, desired_servers: list) -> dict:
    desired_counts = {}
    for price_id in desired_servers:
        desired_counts[price_id] = desired_counts.get(price_id, 0) + 1
    ids_to_delete = {'vm': [], 'db': []}

    for resource in resources:
        resource_price_id = resource.get('price_id')
        if resource_price_id and resource_price_id in desired_servers and desired_counts[resource_price_id] > 0:
            desired_counts[resource_price_id] -= 1
        else:
            resource_id = resource.get('id')
            if resource_id:
                ids_to_delete[resource['type']].append(resource_id)
                log.debug(f'To_remove {resource}')

    for resource in resources:
        if resource['failed'] and ids_to_delete[resource['type']]:
            log.debug(f'Cant remove {resource["type"]} right now')
            ids_to_delete[resource['type']] = []

    for res_type in ids_to_delete:
        if ids_to_delete[res_type]:
            log.debug(f'{ids_to_delete[res_type]=}')
            for resource_id in ids_to_delete[res_type]:
                delete_request('resource', resource_id)

    return ids_to_delete
