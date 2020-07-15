import multiprocessing
import os

import aiida
import cpuinfo
from pgtest.pgtest import PGTest
import psycopg2



def pytest_benchmark_update_machine_info(config, machine_info):

    # retrieve additional CPU information
    cpu_info = cpuinfo.get_cpu_info()
    cpu_count_system = os.cpu_count()

    # retrieve additional postgres information
    with PGTest() as pg:
        with psycopg2.connect(**pg.dsn) as conn:
            postgres_version = conn.server_version
            # with conn.cursor() as cursor:
            #     cursor.execute('SELECT VERSION()')
            #     postgres_version = cursor.fetchone()[0]

    machine_info["aiida"] = {
        "aiida_version": aiida.__version__,
        "processor_hz": cpu_info["hz_actual_friendly"],
        "cpu_count": cpu_count_system,
        "postgres_version": postgres_version
    }
