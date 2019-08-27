import gremlin_python
from janusgraphy import helpers

traversal_verbose = False


class GraphObjectMeta(type):
    known_objects = dict()

    def __new__(cls, clsname, superclasses, attributedict):
        if traversal_verbose:
            print("clsname: ", clsname)
            print("superclasses: ", superclasses)
            print("attributedict: ", attributedict)
        new_class = type.__new__(cls, clsname, superclasses, attributedict)
        return new_class

    def __init__(cls, clsname, superclasses, attributedict):
        if traversal_verbose:
            print("clsname: ", clsname)
            print("superclasses: ", superclasses)
            print("attributedict: ", attributedict)

        if not attributedict.get('Label'):
            cls.Label = helpers.camel_to_snake(clsname, sep=' ', lower=False)

        if cls.Label in GraphObjectMeta.known_objects:
            raise Exception(f"Class label '{cls.Label}' is already defined")

        GraphObjectMeta.known_objects[cls.Label] = cls

    '''def __new__(cls, clsname, superclasses, attributedict):
        print("clsname: ", clsname)
        print("superclasses: ", superclasses)
        print("attributedict: ", attributedict)
        new_class = type.__new__(cls, clsname, superclasses, attributedict)
        new_class.Label = clsname.lower()
        return new_class
    '''


class GraphObject(metaclass=GraphObjectMeta):
    """The base graph object

    The object's label is converted by default from CamelCase to snake_case.
    When extending, the object must implement add_to_graph method and can set
    a custom label through Label property and some mandatory properties

    The kwarguments passed in the __init__ method will be set in the database
    as properties
    
    Raises:
        NotImplementedError: on add_to_graph
    """
    #known_objects = dict()
    Label = None  # set by metaclass but can be set by extending class
    Structure = None  # properties that are mandatory. Can be set by extending class

    Properties: dict  # current object properties
    graph_value: 'Any'=None  # the value in the graph

    def __new__(cls, *args, add_to_graph: bool = True, set_properties:bool=False, **kwproperties):
        self = super(GraphObject, cls).__new__(cls)
        self.graph_value = None

        if set_properties:
            self.__set_properties(**kwproperties)
            if add_to_graph:
                self.add_to_graph()

        return self

    def __init__(self, *args, add_to_graph: bool = True,  **kwproperties):
        """Initializes a GraphObject

        The kwarguments passed are set as properties of the database object
        (the logic that sets the properties is in __new__)
        
        Keyword Arguments:
            add_to_graph {bool} -- Whether to add the object to the graph already (default: {True})
        """
        self.__set_properties(**kwproperties)

        if add_to_graph:
            self.add_to_graph()

    def __set_properties(self, **properties):
        if self.Structure:
            helpers.check_structure(self.Structure, properties)

        self.Properties = properties


    @staticmethod
    def instantiate(obj):
        gremlin_vertex = gremlin_python.structure.graph.Vertex
        gremlin_edge = gremlin_python.structure.graph.Edge

        if type(obj) in [gremlin_vertex, gremlin_edge]:
            traversal = helpers.get_traversal(obj)
            label = obj.label

            values = (traversal + [['valueMap', []]]).run()[0]
            if type(obj) is gremlin_vertex:
                values = {k: v[0] for k, v in values.items()}

            cls = GraphObject.known_objects.get(label, GraphObject)
            result = cls.__new__(cls, add_to_graph=False, set_properties=True, **values)
            result.graph_value = obj
            return result

        if type(obj) is list:
            for i, e in enumerate(obj):
                obj[i] = GraphObject.instantiate(e)

            return obj

        if type(obj) is dict:
            inst = GraphObject.instantiate
            result = dict()
            for k, v in obj.items():
                result[inst(k)] = inst(v)

            return result

        else:
            return obj

    @helpers.classinstancemethod
    def query(self=None, cls=None, verbose=None):
        from janusgraphy.query import Query  # late imports to avoid circular imports
        from janusgraphy.traversal import Traversal

        if self:
            return Query(query_space=helpers.get_traversal(self.graph_value), verbose=verbose)
        else:
            return Query(query_space=Traversal.vertices(), verbose=verbose).filter_by_property(Label=cls.Label)

    def remove_from_graph(self):
        if self.in_graph():
            helpers.get_traversal(self.graph_value).add('drop', None).run()
            return True
        else:
            return False

    def in_graph(self):
        return self.graph_value is not None

    def __repr__(self):
        return f'<{self.Label}: {str(self.__dict__)}>'

    def add_to_graph(self):
        raise NotImplementedError()
