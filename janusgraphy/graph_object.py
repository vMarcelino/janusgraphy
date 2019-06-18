import gremlin_python
from . import helpers

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
    #known_objects = dict()
    Label = None  # just because the linter was giving errors due to not detecting metaclass
    Structure = None

    def __init__(self, *args, add_to_graph=True, fully_initialize=True, **kwproperties):
        #self.Label = type(self).__name__.lower()
        #self.known_objects[self.Label] = type(self)

        import inspect
        init_func = getattr(self, 'init', None)
        if init_func:
            init_parameter_names = inspect.getfullargspec(init_func)[0][1:]

            init_parameters = {}
            for parameter in init_parameter_names:
                if parameter in kwproperties:
                    init_parameters[parameter] = kwproperties[parameter]
                    del kwproperties[parameter]

        if 'Label' in kwproperties:
            del kwproperties['Label']

        if self.Structure:
            helpers.check_structure(self.Structure, kwproperties)

        self.Properties = kwproperties
        self.graph_value = None

        if add_to_graph:
            self.add_to_graph()

        if init_func and fully_initialize:
            getattr(self, 'init')(**init_parameters, **kwproperties)
            # init_func(**init_parameters, **kwproperties) # disabled as linter was giving problems

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
            result = GraphObject.known_objects.get(label, GraphObject)(add_to_graph=False,
                                                                       fully_initialize=False,
                                                                       **values)
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
        from .query import Query  # late imports to avoid circular imports
        from .traversal import Traversal

        if self:
            return Query(helpers.get_traversal(self.graph_value), verbose=verbose)
        else:
            return Query(Traversal.vertices(), verbose=verbose).filter_by_property(Label=cls.Label)

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
