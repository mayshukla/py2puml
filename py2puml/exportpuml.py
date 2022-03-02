from typing import List, Iterable

from py2puml.domain.umlitem import UmlItem
from py2puml.domain.umlclass import UmlClass, UmlParam, UmlMethod
from py2puml.domain.umlenum import UmlEnum
from py2puml.domain.umlrelation import UmlRelation

PUML_FILE_START = '@startuml\n'
PUML_FILE_END = '@enduml\n'
PUML_ITEM_START_TPL = '{item_type} {item_fqn} {{\n'
PUML_ATTR_TPL = '  {attr_name}: {attr_type}{staticity}\n'
PUML_METHOD_TPL = '  {method_name}({method_params}): {method_return_type}{staticity}\n'
PUML_PARAM_TPL = '{param_name}: {param_type}'
PUML_ITEM_END = '}\n'
PUML_COMPOSITION_TPL = '{source_fqn} {rel_type}-- {target_fqn}\n'

FEATURE_STATIC = ' {static}'
FEATURE_INSTANCE = ''

def to_puml_content(uml_items: List[UmlItem], uml_relations: List[UmlRelation]) -> Iterable[str]:
    yield PUML_FILE_START

    # exports the domain classes and enums
    for uml_item in uml_items:
        if isinstance(uml_item, UmlEnum):
            uml_enum: UmlEnum = uml_item
            yield PUML_ITEM_START_TPL.format(item_type='enum', item_fqn=uml_enum.fqn)
            for member in uml_enum.members:
                yield PUML_ATTR_TPL.format(attr_name=member.name, attr_type=member.value, staticity=FEATURE_STATIC)
            yield PUML_ITEM_END
        elif isinstance(uml_item, UmlClass):
            uml_class: UmlClass = uml_item
            yield PUML_ITEM_START_TPL.format(item_type='class', item_fqn=uml_class.fqn)
            for uml_attr in uml_class.attributes:
                yield PUML_ATTR_TPL.format(attr_name=uml_attr.name, attr_type=uml_attr.type, staticity=FEATURE_STATIC if uml_attr.static else FEATURE_INSTANCE)
            for uml_method in uml_class.methods:
                method_params = ", ".join([
                    PUML_PARAM_TPL.format(param_name=uml_param.name, param_type=uml_param.type) for uml_param in uml_method.params
                ])
                yield PUML_METHOD_TPL.format(method_name=uml_method.name, method_params=method_params, method_return_type=uml_method.return_type, staticity=FEATURE_STATIC if uml_method.static else FEATURE_INSTANCE)
            yield PUML_ITEM_END
        else:
            raise TypeError(f'cannot process uml_item of type {uml_item.__class__}')

    # exports the domain relationships between classes and enums
    for uml_relation in uml_relations:
        yield PUML_COMPOSITION_TPL.format(
            source_fqn=uml_relation.source_fqn,
            rel_type=uml_relation.type.value,
            target_fqn=uml_relation.target_fqn
        )

    yield PUML_FILE_END


# TODO remove this testing
if __name__ == "__main__":
    params = [UmlParam("param1", "type1"), UmlParam("param2", "type2")]
    method = UmlMethod("my_method", "return_type", False, params)
    uml_class = UmlClass("my_class", "my_class", [], [method])
    print("".join(to_puml_content([uml_class], [])))