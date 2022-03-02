from typing import List
from dataclasses import dataclass

from py2puml.domain.umlitem import UmlItem

@dataclass
class UmlAttribute(object):
    name: str
    type: str
    static: bool

@dataclass
class UmlParam(object):
    name: str
    type: str

@dataclass
class UmlMethod(object):
    name: str
    return_type: str
    static: bool
    params: List[UmlParam]

@dataclass
class UmlClass(UmlItem):
    attributes: List[UmlAttribute]
    methods: List[UmlMethod]
