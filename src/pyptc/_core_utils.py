from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterator

from loguru import logger
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.core import Device, DeviceType

if TYPE_CHECKING:
    import numpy as np


class AvailableDevice:
    def __init__(
        self,
        adapter: str,
        device: str,
        dtype: DeviceType | int | None = None,
        core: CMMCorePlus | None = None,
    ):
        self.adapter = adapter
        self.device = device
        self.dtype = DeviceType(dtype) if dtype is not None else None
        self.core = core or CMMCorePlus.instance()

    def __repr__(self) -> str:
        return f"AvailableDevice({self.adapter!r}, {self.device!r})"

    def load(self, device_label: str = "") -> Device:
        """Load a device from the adapter as the specified label."""
        if not device_label:
            taken = set(self.core.getLoadedDevices())
            device_label = self.adapter
            if device_label in taken:
                i = 1
                while device_label + str(i) in taken:
                    i += 1
                device_label += str(i)

        dev = Device(device_label, self.core)
        dev.load(self.adapter, self.device)
        return dev


class DeviceAdapter:
    def __init__(self, adapter_name: str, core: CMMCorePlus | None = None):
        self._core = core or CMMCorePlus.instance()
        self._adapter_name = adapter_name

    @property
    def works(self) -> bool:
        """Return whether the adapter works."""
        try:
            self._core.getAvailableDevices(self._adapter_name)
            return True
        except RuntimeError:
            return False

    def iterAvailableDevices(
        self, dtype: DeviceType | None = None
    ) -> Iterator[AvailableDevice]:
        """Get available devices from the specified device library."""
        for dev_type, dev in zip(
            self._core.getAvailableDeviceTypes(self._adapter_name),
            self._core.getAvailableDevices(self._adapter_name),
        ):
            if dtype is not None and dev_type != dtype:
                continue
            yield AvailableDevice(
                self._adapter_name, dev, DeviceType(dev_type), self._core
            )

    def __repr__(self) -> str:
        return f"DeviceAdapter({self._adapter_name!r})"


def iter_adapters(core: CMMCorePlus) -> Iterator[DeviceAdapter]:
    for adapter_name in core.getDeviceAdapterNames():
        yield DeviceAdapter(adapter_name, core)


def load_all_cameras(core: CMMCorePlus) -> list[Device]:
    already_loaded = core.getLoadedDevicesOfType(DeviceType.CameraDevice)
    loaded = [Device(dev, core) for dev in already_loaded]
    for adapter in iter_adapters(core):
        try:
            for camera in adapter.iterAvailableDevices(DeviceType.CameraDevice):
                if camera.adapter not in already_loaded:
                    try:
                        logger.debug(f"Loading camera {camera!r}")
                        dev = camera.load()
                        loaded.append(dev)
                    except RuntimeError:
                        continue
        except RuntimeError:
            continue
    return loaded
