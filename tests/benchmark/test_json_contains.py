import random
import string

import pytest

from aiida import orm
from aiida.orm.querybuilder import QueryBuilder

GROUP_NAME = 'json-contains'


COMPLEX_JSON_DEPTH_RANGE = [2**i for i in range(4)]
COMPLEX_JSON_BREADTH_RANGE = [2**i for i in range(4)]
LARGE_TABLE_SIZE_RANGE = [2**i for i in range(1, 11)]


def gen_json(depth: int, breadth: int):
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
        gen_dict = random.choice([True, False])
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
    lhs = gen_json(depth, breadth)
    rhs = extract_component(lhs, p=1.0 / depth)
    assert 0 == len(QueryBuilder().append(orm.Dict).all())

    orm.Dict(
        {
            'id': f'{depth}-{breadth}',
            'data': lhs,
        }
    ).store()
    qb = QueryBuilder().append(
        orm.Dict,
        filters={
            'attributes.data': {'contains': rhs},
        },
        project=['attributes.id'],
    )
    qb.all()
    result = benchmark(qb.all)
    assert len(result) == 1


@pytest.mark.benchmark(group=GROUP_NAME)
@pytest.mark.parametrize('depth', [2])
@pytest.mark.parametrize('breadth', [1, 10, 100])
@pytest.mark.usefixtures('aiida_profile_clean')
def test_wide_json(benchmark, depth, breadth):
    lhs = gen_json(depth, breadth)
    rhs = extract_component(lhs, p=1.0 / depth)
    assert 0 == len(QueryBuilder().append(orm.Dict).all())

    orm.Dict(
        {
            'id': f'{depth}-{breadth}',
            'data': lhs,
        }
    ).store()
    qb = QueryBuilder().append(
        orm.Dict,
        filters={
            'attributes.data': {'contains': rhs},
        },
        project=['attributes.id'],
    )
    qb.all()
    result = benchmark(qb.all)
    assert len(result) == 1


@pytest.mark.benchmark(group=GROUP_NAME)
@pytest.mark.parametrize('num_entries', LARGE_TABLE_SIZE_RANGE)
@pytest.mark.usefixtures('aiida_profile_clean')
def test_large_table(benchmark, num_entries):
    data = gen_json(2, 10)
    rhs = extract_component(data)
    assert 0 == len(QueryBuilder().append(orm.Dict).all())

    for i in range(num_entries):
        orm.Dict(
            {
                'id': f'N={num_entries}, i={i}',
                'data': data,
            }
        ).store()
    qb = QueryBuilder().append(
        orm.Dict,
        filters={
            'attributes.data': {'contains': rhs},
        },
        project=['attributes.id'],
    )
    qb.all()
    result = benchmark(qb.all)
    assert len(result) == num_entries
