
from typing import Type, List, Dict, Tuple, NoReturn

from re import compile
from dataclasses import dataclass
from inspect import getmembers, isfunction, signature, Parameter, Signature

from py2puml.domain.umlitem import UmlItem
from py2puml.domain.umlclass import UmlClass, UmlAttribute, UmlMethod, UmlParam
from py2puml.domain.umlrelation import UmlRelation, RelType
from py2puml.parsing.parseclassconstructor import parse_class_constructor
from py2puml.utils import inspect_domain_definition

CONCRETE_TYPE_PATTERN = compile("^<(?:class|enum) '([\\.|\\w]+)'>$")

def extract_type_name(raw_type_name: str) -> str:
    """Converts something like "<class 'str'>" into just "str"
    """
    concrete_type_match = CONCRETE_TYPE_PATTERN.search(raw_type_name)
    if concrete_type_match:
        return concrete_type_match.group(1)
    return raw_type_name


def get_type_name(type: Type, root_module_name: str):
    if type.__module__.startswith(root_module_name):
        return type.__name__
    else:
        return f'{type.__module__}.{type.__name__}'

def handle_inheritance_relation(
    class_type: Type,
    class_fqn: str,
    root_module_name: str,
    domain_relations: List[UmlRelation]
):
    for base_type in getattr(class_type, '__bases__', ()):
        base_type_fqn = f'{base_type.__module__}.{base_type.__name__}'
        if base_type_fqn.startswith(root_module_name):
            domain_relations.append(
                UmlRelation(base_type_fqn, class_fqn, RelType.INHERITANCE)
            )

def inspect_static_attributes(
    class_type: Type,
    class_type_fqn: str,
    root_module_name: str,
    domain_items_by_fqn: Dict[str, UmlItem],
    domain_relations: List[UmlRelation]
) -> Tuple[List[UmlAttribute], List[UmlMethod]]:
    definition_attrs: List[UmlAttribute] = []
    methods: List[UmlMethod] = []
    uml_class = UmlClass(
        name=class_type.__name__,
        fqn=class_type_fqn,
        attributes=definition_attrs,
        methods=methods
    )
    domain_items_by_fqn[class_type_fqn] = uml_class
    # inspect_domain_definition(class_type)
    type_annotations = getattr(class_type, '__annotations__', None)
    if type_annotations is not None:
        for attr_name, attr_class in type_annotations.items():
            attr_raw_type = str(attr_class)
            concrete_type_match = CONCRETE_TYPE_PATTERN.search(attr_raw_type)
            if concrete_type_match:
                concrete_type = concrete_type_match.group(1)
                if attr_class.__module__.startswith(root_module_name):
                    attr_type = attr_class.__name__
                    domain_relations.append(
                        UmlRelation(uml_class.fqn, f'{attr_class.__module__}.{attr_class.__name__}', RelType.COMPOSITION)
                    )
                else:
                    attr_type = concrete_type
            else:
                composition_rel = getattr(attr_class, '_name', None)
                component_classes = getattr(attr_class, '__args__', None)
                if composition_rel and component_classes:
                    component_names = [
                        get_type_name(component_class, root_module_name)
                        for component_class in component_classes
                        # filters out forward refs
                        if getattr(component_class, '__name__', None) is not None
                    ]
                    domain_relations.extend([
                        UmlRelation(uml_class.fqn, f'{component_class.__module__}.{component_class.__name__}', RelType.COMPOSITION)
                        for component_class in component_classes
                        if component_class.__module__.startswith(root_module_name)
                    ])
                    attr_type = f"{composition_rel}[{', '.join(component_names)}]"
                else:
                    attr_type = attr_raw_type
            uml_attr = UmlAttribute(attr_name, attr_type, static=True)
            definition_attrs.append(uml_attr)

    return definition_attrs, methods

def inspect_methods(
    class_type: Type
) -> List[UmlMethod]:
    methods = []
    print(class_type.__dict__)
    for method_name, method_obj in getmembers(class_type, isfunction):
        method_signature = signature(method_obj)

        params = []
        static = True
        for param in method_signature.parameters.values():
            # Don't include "self" param in UML
            param_name = param.name
            if param_name == "self":
                static = False
                continue
            param_type = param.annotation
            if param_type == Parameter.empty:
                param_type = None
            param_type_name = extract_type_name(str(param_type))

            params.append(UmlParam(param_name, param_type_name))

        return_type = method_signature.return_annotation
        return_type_name = None
        if (return_type != Signature.empty
            and return_type is not None
            and return_type is not NoReturn):
            return_type_name = extract_type_name(str(return_type))

        uml_method = UmlMethod(method_name, return_type_name, static, params)
        methods.append(uml_method)

    return methods

def inspect_class_type(
    class_type: Type,
    class_type_fqn: str,
    root_module_name: str,
    domain_items_by_fqn: Dict[str, UmlItem],
    domain_relations: List[UmlRelation]
):
    attributes, methods = inspect_static_attributes(
        class_type, class_type_fqn, root_module_name,
        domain_items_by_fqn, domain_relations
    )
    methods.extend(inspect_methods(class_type))
    instance_attributes, compositions = parse_class_constructor(class_type, class_type_fqn, root_module_name)
    attributes.extend(instance_attributes)
    domain_relations.extend(compositions.values())

    handle_inheritance_relation(class_type, class_type_fqn, root_module_name, domain_relations)

def inspect_dataclass_type(
    class_type: Type[dataclass],
    class_type_fqn: str,
    root_module_name: str,
    domain_items_by_fqn: Dict[str, UmlItem],
    domain_relations: List[UmlRelation]
):
    for attribute in inspect_static_attributes(
        class_type,
        class_type_fqn,
        root_module_name,
        domain_items_by_fqn,
        domain_relations
    ):
        attribute.static = False

    handle_inheritance_relation(class_type, class_type_fqn, root_module_name, domain_relations)