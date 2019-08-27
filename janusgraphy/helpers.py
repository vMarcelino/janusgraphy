import re
import gremlin_python
from functools import wraps
from datetime import datetime


str_time = lambda: datetime.now().strftime('%Y-%m-%d at %H:%M:%S.%f')


class classinstancemethod:
    def __init__(self, method, instance=None, owner=None):
        self.method = method
        self.instance = instance
        self.owner = owner

    def __get__(self, instance, owner=None):
        return wraps(self.method)(type(self)(self.method, instance=instance, owner=owner))

    def __call__(self, *args, **kwargs):
        return self.method(self.instance, self.owner, *args, **kwargs)


def camel_to_snake(string, sep='_', lower=True):
    string = re.sub('(.)([A-Z][a-z]+)', fr'\1{sep}\2', string)
    string = re.sub('(.)([0-9]+)', fr'\1{sep}\2', string)
    string = re.sub('([a-z0-9])([A-Z])', fr'\1{sep}\2', string)
    if lower:
        return string.lower()
    else:
        return string


def check_structure(structure, kwproperties):
    missing_args = []
    for var in structure:
        if var not in kwproperties:
            missing_args.append(var)

    if missing_args:
        raise TypeError(f"missing {len(missing_args)} required positional argument{'' if len(missing_args) == 1 else 's'}: " +
                        ', '.join(missing_args))


def get_traversal(x) -> 'Traversal':
    from janusgraphy.traversal import Traversal # late import to avoid circular import
    from janusgraphy.query import Query
    
    if type(x) is gremlin_python.structure.graph.Vertex:
        x = Traversal(t_query=[['g'], ['V', [x.id]]])
    elif type(x) is gremlin_python.structure.graph.Edge:
        edge_id = x.id['@value']['value']
        x = Traversal(t_query=[['g'], ['E', [edge_id]]])
    #elif type(x) is list:
    #    x = Traversal([['g'], [mapping[type(x)], [] + list(map(lambda gobj: gobj.id, x))]])
    elif type(x) is Traversal:
        x = x.clone()
    elif type(x) is Query:
        x = Traversal(t_query=x.query)
    else:
        print('Unrecognized type in get_traversal:', type(x))
    return x
