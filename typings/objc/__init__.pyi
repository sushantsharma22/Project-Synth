"""Type stubs for objc (PyObjC)"""
from typing import Any, TypeVar

_T = TypeVar('_T')

def super(cls: type[_T], instance: _T) -> Any: ...
