from typing import Any, Union
from PyQt5.QtWidgets import QLabel, QVBoxLayout
from qtpy.QtWidgets import (
    QLineEdit,
    QCheckBox,
    QComboBox,
    QSlider,
    QDoubleSpinBox,
    QWidget,
    QScrollArea,
    QFormLayout,
)
from qtpy.QtCore import Qt
from functools import partial
from superqt import QLabeledDoubleSlider, QLabeledSlider
import re

SchemaWidget = Union[QLineEdit, QCheckBox, QComboBox, QSlider, QDoubleSpinBox]

TYPE_MAP = {
    "boolean": QCheckBox,
    "integer": partial(QLabeledSlider, Qt.Horizontal),
    "number": QDoubleSpinBox,
    "string": QLineEdit,
    "enum": QComboBox,
}


def property_widget(prop_dict: dict):
    if "enum" in prop_dict:
        wdg = QComboBox()
        for e in prop_dict["enum"]:
            wdg.addItem(str(e), e)
    elif prop_dict.get("type") == "string" and prop_dict.get("readOnly"):
        wdg = QLabel()
        wdg.setEnabled(False)
        return wdg
    else:
        wdg = TYPE_MAP[prop_dict["type"]]()

    if "minimum" in prop_dict:
        min_ = prop_dict["minimum"]
        if prop_dict.get("type") == "integer":
            min_ = int(min_)
        wdg.setMinimum(min_)
    if "maximum" in prop_dict:
        max_ = prop_dict["maximum"]
        if prop_dict.get("type") == "integer":
            max_ = int(max_)
        wdg.setMaximum(max_)
    if prop_dict.get("readOnly"):
        wdg.setReadOnly(True)
        wdg.setEnabled(False)
    return wdg


def set_value(wdg: SchemaWidget, value: Any):
    if isinstance(wdg, QCheckBox):
        wdg.setChecked(bool(int(value)))
    elif isinstance(wdg, QComboBox):
        wdg.setCurrentText(str(value))
    elif isinstance(wdg, QSlider):
        wdg.setValue(int(value))
    elif isinstance(wdg, QLabeledDoubleSlider):
        wdg.setValue(float(value))
    elif hasattr(wdg, "setText"):
        wdg.setText(str(value))


def connect_to_core(core, wdg: SchemaWidget, device_label: str, prop_name: str):
    cb = partial(getattr(core, "setProperty"), device_label, prop_name)

    if isinstance(wdg, QComboBox):
        wdg.currentIndexChanged.connect(lambda i: cb(wdg.itemData(i)))
    elif isinstance(wdg, QCheckBox):
        wdg.toggled.connect(cb)
    elif isinstance(
        wdg, (QSlider, QLabeledSlider, QLabeledDoubleSlider, QDoubleSpinBox)
    ):
        wdg.valueChanged.connect(cb)
    elif isinstance(wdg, QLineEdit):
        wdg.textChanged.connect(cb)


def device_widget(core, device_label: str):
    schema = core.getDeviceSchema(device_label)
    props = core.getDeviceProperties(device_label)
    scroll = QScrollArea()
    scroll.setMinimumWidth(460)
    inner = QWidget()
    inner.setLayout(QFormLayout())
    for name, prop_dict in schema["properties"].items():
        wdg = property_widget(prop_dict)
        set_value(wdg, props[name])
        connect_to_core(core, wdg, device_label, name)
        name = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", name)
        inner.layout().addRow(name, wdg)
    scroll.setWidget(inner)
    return scroll
