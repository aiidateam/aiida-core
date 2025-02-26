import random
import string

import pytest

from aiida import orm
from aiida.manage import get_manager
from aiida.orm import EntityTypes

GROUP_NAME = 'bulk-update'


def gen_json(depth: int, breadth: int, force_dict: bool = False):
    def gen_str(n: int, with_digits: bool = True):
        population = string.ascii_letters
        if with_digits:
            population += string.digits
        return ''.join(random.choices(population, k=n))

    if depth == 0:  # random primitive value
        # real numbers are not included as their equivalence is tricky
        return random.choice(
            [
                random.randint(-114, 514),  # integers
                gen_str(6),  # strings
                random.choice([True, False]),  # booleans
                None,  # nulls
            ]
        )

    else:
        gen_dict = True if force_dict else random.choice([True, False])
        data = [gen_json(depth - 1, breadth) for _ in range(breadth)]
        if gen_dict:
            keys = set()
            while len(keys) < breadth:
                keys.add(gen_str(6, False))
            data = dict(zip(list(keys), data))
        return data


def extract_component(data, p: float = -1):
    if random.random() < p:
        return data

    if isinstance(data, dict) and data:
        key = random.choice(list(data.keys()))
        return {key: extract_component(data[key])}
    elif isinstance(data, list) and data:
        element = random.choice(data)
        return [extract_component(element)]
    else:
        return data


@pytest.mark.benchmark(group=GROUP_NAME)
@pytest.mark.parametrize('depth', [1, 2, 4, 8])
@pytest.mark.parametrize('breadth', [1, 2, 4])
@pytest.mark.usefixtures('aiida_profile_clean')
def test_deep_json(benchmark, depth, breadth):
    nodes = []
    for _ in range(10):
        nodes.append(orm.Dict(gen_json(depth, breadth, force_dict=True)).store())

    updates = []
    for node in nodes:
        update = {'id': node.id, 'attributes': gen_json(depth, breadth, force_dict=True)}
        updates.append(update)

    backend = get_manager().get_backend()
    benchmark(lambda: backend.bulk_update(entity_type=EntityTypes.NODE, rows=updates, extend_json=True))


@pytest.mark.benchmark(group=GROUP_NAME)
@pytest.mark.parametrize('depth', [2])
@pytest.mark.parametrize('breadth', [1, 10, 100])
@pytest.mark.usefixtures('aiida_profile_clean')
def test_wide_json(benchmark, depth, breadth):
    nodes = []
    for _ in range(10):
        nodes.append(orm.Dict(gen_json(depth, breadth, force_dict=True)).store())

    updates = []
    for node in nodes:
        update = {'id': node.id, 'attributes': gen_json(depth, breadth, force_dict=True)}
        updates.append(update)

    backend = get_manager().get_backend()
    benchmark(lambda: backend.bulk_update(entity_type=EntityTypes.NODE, rows=updates, extend_json=True))


@pytest.mark.benchmark(group=GROUP_NAME)
@pytest.mark.parametrize('num_entries', [2**i for i in range(1, 10)])
@pytest.mark.usefixtures('aiida_profile_clean')
def test_large_table(benchmark, num_entries):
    nodes = []
    for _ in range(num_entries):
        nodes.append(orm.Dict(gen_json(2, 10, force_dict=True)).store())

    updates = []
    for node in nodes:
        update = {'id': node.id, 'attributes': gen_json(2, 10, force_dict=True)}
        updates.append(update)

    backend = get_manager().get_backend()
    benchmark(lambda: backend.bulk_update(entity_type=EntityTypes.NODE, rows=updates, extend_json=True))
