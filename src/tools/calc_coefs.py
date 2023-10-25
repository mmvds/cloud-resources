from src.db.db import *

# conn = get_connect(get_best_db('../../'), '../../')
conn = get_connect('remote')
cursor = conn.cursor()
query = '''
        SELECT t1.requests, 
               t1.vm_cpu, t1.db_cpu, 
               t1.vm_ram, t1.db_ram, 
               t1.vm_cpu_load, t1.db_cpu_load, 
               t1.vm_ram_load, t1.db_ram_load,
               t2.online_vm, t2.online_db
        FROM statistics t1, servers t2
        WHERE t1.timestamp=t2.timestamp 
        ORDER BY t1.timestamp DESC
        LIMIT 10
        '''
cursor.execute(query)
data = cursor.fetchall()
conn.close()

(requests1,
 vm_cpu1, db_cpu1, vm_ram1, db_ram1,
 vm_cpu_load1, db_cpu_load1, vm_ram_load1, db_ram_load1,
 online_vm1, online_db1) = data[0]
(requests2,
 vm_cpu2, db_cpu2, vm_ram2, db_ram2,
 vm_cpu_load2, db_cpu_load2, vm_ram_load2, db_ram_load2,
 online_vm2, online_db2) = data[3]

x_vm_ram = (((vm_ram_load2 * vm_ram2) / 100 - ((vm_ram_load1 * vm_ram1) / 100 * online_vm2 / online_vm1)) /
            (requests2 - (requests1 * online_vm2 / online_vm1)))

y_vm_ram = (vm_ram_load1 * vm_ram1 / 100 - x_vm_ram * requests1) / online_vm1

x_db_ram = (((db_ram_load2 * db_ram2) / 100 - ((db_ram_load1 * db_ram1) / 100 * online_db2 / online_db1)) /
            (requests2 - (requests1 * online_db2 / online_db1)))

y_db_ram = (db_ram_load1 * db_ram1 / 100 - x_db_ram * requests1) / online_db1

x_vm_cpu = (((vm_cpu_load2 * vm_cpu2) / 100 - ((vm_cpu_load1 * vm_cpu1) / 100 * online_vm2 / online_vm1)) /
            (requests2 - (requests1 * online_vm2 / online_vm1)))

y_vm_cpu = (vm_cpu_load1 * vm_cpu1 / 100 - x_vm_cpu * requests1) / online_vm1

x_db_cpu = (((db_cpu_load2 * db_cpu2) / 100 - ((db_cpu_load1 * db_cpu1) / 100 * online_db2 / online_db1)) /
            (requests2 - (requests1 * online_db2 / online_db1)))

y_db_cpu = (db_cpu_load1 * db_cpu1 / 100 - x_db_cpu * requests1) / online_db1

print(f'{x_vm_ram=:.5f}, {y_vm_ram=:.5f}')
print(f'{x_db_ram=:.5f}, {y_db_ram=:.5f}')
print(f'{x_vm_cpu=:.5f}, {y_vm_cpu=:.5f}')
print(f'{x_db_cpu=:.5f}, {y_db_cpu=:.5f}')
