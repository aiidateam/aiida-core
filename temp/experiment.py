import pathlib
from typing import cast
import zipfile
import time
import statistics
from abc import ABC, abstractmethod
import random

import disk_objectstore as dostore
from disk_objectstore.utils import StreamSeekBytesType

random.seed(42)

REPO_FILE = pathlib.Path(__file__).parent.parent / ".." / "datasets" / "small.aiida"
print("handling", REPO_FILE, "...")
ADD_MAX = 10000
REPO = zipfile.ZipFile(REPO_FILE)
NAMELIST = list(filter(lambda name: name.startswith("repo/"), REPO.namelist()))
SELECTED_NAMELIST = list(random.sample(NAMELIST, ADD_MAX))

print(f"Number of files in the .aiida file: {len(NAMELIST)}")

CONTAINER = dostore.Container("test")


class Experiment(ABC):
    @abstractmethod
    def __call__(self): ...

    def __str__(self):
        return self.__class__.__name__


class Baseline(Experiment):
    def __call__(self):
        for fname in SELECTED_NAMELIST:
            with REPO.open(fname) as fh:
                data = fh.read()
            CONTAINER.add_object(data)


class DirectPackedOnce(Experiment):
    def __call__(self):
        fhs = []
        for fname in SELECTED_NAMELIST:
            fhs.append(REPO.open(fname))
        CONTAINER.add_streamed_objects_to_pack(fhs)
        for fh in fhs:
            fh.close()


class DirectPackedOneByOne(Experiment):
    def __init__(self, do_commit: bool = True, do_fsync: bool = True):
        self.do_commit = do_commit
        self.do_fsync = do_fsync

    def __call__(self):
        for fname in SELECTED_NAMELIST:
            with REPO.open(fname) as fh:
                CONTAINER.add_streamed_object_to_pack(
                    cast(StreamSeekBytesType, fh),
                    do_commit=self.do_commit,
                    do_fsync=self.do_fsync,
                )
        if not self.do_commit:
            CONTAINER._get_container_session().commit()

    def __str__(self):
        return f"{self.__class__.__name__} (do_commit={self.do_commit}, do_fsync={self.do_fsync})"


for exp in [
    Baseline(),
    DirectPackedOnce(),
    DirectPackedOneByOne(),
    DirectPackedOneByOne(do_commit=False),
    DirectPackedOneByOne(do_fsync=False),
    DirectPackedOneByOne(do_commit=False, do_fsync=False),
]:
    ts = []
    for t in range(1):
        CONTAINER.init_container(clear=True)
        begin = time.perf_counter()
        exp()
        end = time.perf_counter()
        ts.append(end - begin)
        container_count = CONTAINER.count_objects().loose + CONTAINER.count_objects().packed
        assert container_count == ADD_MAX, f"file count miss match: ADD_MAX={ADD_MAX}, count={CONTAINER.count_objects()}"
    print(f"{str(exp)}:\tmean={statistics.mean(ts):.2f}s\tmedian={statistics.median(ts):.2f}s")
