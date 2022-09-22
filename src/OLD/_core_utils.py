from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Iterator, List, Tuple

from loguru import logger
from pymmcore_plus.core import DeviceType

if TYPE_CHECKING:
    from pymmcore_plus import CMMCorePlus


def iter_available_devices(core: CMMCorePlus) -> Iterator[Tuple[str, str, DeviceType]]:
    for adapter_name in core.getDeviceAdapterNames():
        try:
            for dev_type, dev in zip(
                core.getAvailableDeviceTypes(adapter_name),
                core.getAvailableDevices(adapter_name),
            ):
                yield (adapter_name, dev, DeviceType(dev_type))
        except RuntimeError:
            pass


def get_cameras(core):
    for adapter, dev, dtype in iter_available_devices(core):
        if dtype == DeviceType.Camera:
            yield adapter, dev


def load_all_devices_of_type(
    core: CMMCorePlus, dev_type: DeviceType
) -> Iterator[Tuple[str, str]]:
    """Tries to load all available devices of a certain type.

    Returns list of tuples (adapter name, device name) of loaded devices.
    """
    already_loaded = core.getLoadedDevices()
    for adapter, dev, dtype in iter_available_devices(core):
        if dtype == dev_type and adapter not in already_loaded:
            try:
                logger.debug("loading device: {}", adapter)
                dev_label = adapter
                core.loadDevice(dev_label, adapter, dev)
                yield (dev_label, adapter, dev)
            except RuntimeError as e:
                logger.debug(str(e))


def load_cameras(core):
    return list(load_all_devices_of_type(core, DeviceType.Camera))


from pymmcore_plus.core import CMMCorePlus

core = CMMCorePlus()
