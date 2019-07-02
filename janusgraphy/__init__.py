__version__ = '0.1.0'

import re
import gremlin_python
from gremlin_python.driver.client import Client

from .traversal import Traversal
from .graph_object import GraphObject
from . import helpers

traversal_verbose = False
master_client = None


class Edge(GraphObject):
    pass


class Vertex(GraphObject):
    def add_to_graph(self):
        if not self.in_graph():
            self.graph_value = add_vertex(self.Label, **self.Properties).run()[0]
        return self.graph_value

    def add_edge(self, edge, to, two_way=False, **kwproperties):
        self.add_to_graph()
        to.add_to_graph()

        if hasattr(edge, 'Label'):
            edge = edge.Label

        if hasattr(edge, 'Structure'):
            helpers.check_structure(edge.Structure, kwproperties)

        traversal = add_edge(self.graph_value, edge, to.graph_value, both_directions=two_way, **kwproperties)
        return run(traversal)


class LoggedVertex(Vertex):
    link_start_property_name = 'link_start'
    link_end_property_name = 'link_end'

    def remove_from_graph(self, **kwargs):
        edges = self.query().to_edge()
        if self.link_end_property_name in kwargs:
            add_property(edges, **{self.link_end_property_name: kwargs[self.link_end_property_name]}).run()
        else:
            add_property(edges, **{self.link_end_property_name: helpers.str_time()}).run()

    def add_edge(self, *args, **kwargs):
        if self.link_start_property_name in kwargs:
            super().add_edge(*args, **kwargs)
        else:
            super().add_edge(*args, **{self.link_start_property_name: helpers.str_time()}, **kwargs)


def run(traversal, verbose=None) -> list:
    if type(traversal) is Traversal:
        traversal = [traversal]

    r = []
    for trav in traversal:
        r += trav.run(verbose=verbose)

    return r


def connect(url='ws://localhost:8182/gremlin', name='g') -> Client:
    return Client(url, name)


def connect_master(url='ws://localhost:8182/gremlin', name='g') -> Client:
    global master_client
    master_client = Client(url, name)
    return master_client


def add_property(target, **properties) -> Traversal:
    target = helpers.get_traversal(target)
    for key, value in properties.items():
        target.add('property', key, value)

    return target


def add_vertex(Label, **properties) -> Traversal:
    v = Traversal.graph().add('addV', Label)
    return add_property(v, **properties)


def add_edge(source, Label, destination, both_directions=False, **properties) -> list:
    def _add(_source, _label, _destination, _properties):
        _source = helpers.get_traversal(_source)
        _destination = helpers.get_traversal(_destination)

        _source.add('addE', _label).add('to', _destination)
        result = add_property(_source, **_properties)
        return result

    r = [_add(_source=source, _label=Label, _destination=destination, _properties=properties)]

    if both_directions:
        r += [_add(_source=destination, _label=Label, _destination=source, _properties=properties)]

    return r
