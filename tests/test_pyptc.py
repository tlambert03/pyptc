from concurrent.futures.process import BrokenProcessPool
from pyptc._core_utils import _Core
import pytest
from concurrent.futures import ProcessPoolExecutor


@pytest.fixture
def core():
    core = _Core()
    yield core
    core.unloadAllDevices()

