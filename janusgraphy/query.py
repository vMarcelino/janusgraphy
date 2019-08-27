from janusgraphy.traversal import Traversal
from janusgraphy.graph_object import GraphObject
from janusgraphy import traversal_verbose, run


class Query():
    def __init__(self, query_space=None, verbose=None, return_clones=None):
        if query_space is None:
            query_space = Traversal.vertices()
        self.query = query_space
        self.verbose = verbose

    def __getitem__(self, s):
        start, stop = 0, 0
        if isinstance(s, slice):
            start = s.start
            stop = s.stop
        else:
            start = s
            stop = s + 1
            # could add step 'limit'
            # self.query.add("limit", s)

        self.query.add("range", start, stop)
        return self

    def __repr__(self):
        return f'<Query: {self.query.get_traversal_string()}>'

    @staticmethod
    def from_vertex_id(vertex_id: int):
        return Query(query_space=Traversal(t_query=[['g'], ['V', [vertex_id]]]))

    @staticmethod
    def from_edge_id(edge_id: int):
        return Query(query_space=Traversal(t_query=[['g'], ['E', [edge_id]]]))

    @staticmethod
    def relation(return_clones=None):
        return Query(query_space=Traversal().add('__'), return_clones=return_clones)

    @staticmethod
    def not_equal(val, return_clones=None):
        return Traversal().add('neq', val)

    @staticmethod
    def contains_word(val):
        return Traversal().add('textContains', val)

    @staticmethod
    def contains_regex_word(val):
        if type(val) is str:
            val = val.replace('*', '.*')
        return Traversal().add('textContainsRegex', val)

    @staticmethod
    def contains_similar_word(val):
        return Traversal().add('textContainsFuzzy', val)

    @staticmethod
    def regex(val):
        if type(val) is str:
            val = val.replace('*', '.*')
        return Traversal().add('textRegex', val)

    @staticmethod
    def is_similar(val):
        return Traversal().add('textFuzzy', val)

    @staticmethod
    def greater(val):
        return Traversal().add('gt', val)

    @staticmethod
    def greater_or_equal(val):
        return Traversal().add('gte', val)

    @staticmethod
    def less(val):
        return Traversal().add('lt', val)

    @staticmethod
    def less_or_equal(val):
        return Traversal().add('lte', val)

    def filter_by_property(self, *properties, Label=None, **kwproperties):

        if Label:
            if type(Label) is type(self):
                Label = Label.query
            elif hasattr(Label, 'Label'):
                Label = Label.Label
            self.query.add('hasLabel', Label)
        for key, value in kwproperties.items():
            self.query.add('has', key, value)
        for prop in properties:
            self.query.add('has', prop)

        return self

    def filter_by_relation(self, relation):
        import uuid
        temp_tag = str(uuid.uuid4())
        self.tag_as(temp_tag)
        self.query += relation.query
        self.select_with_tag(temp_tag)
        return self.remove_duplicates()

    def remove_duplicates(self):
        self.query.add('dedup', None)
        return self

    def filter_by_edge(self, *properties):
        for any_edge in properties:
            if hasattr(any_edge, 'Label'):
                any_edge = any_edge.Label
            self.query.add('bothE', any_edge).add('inV', None)

        return self

    def filter_by_incoming_edge(self, *properties):
        for in_edge in properties:
            if hasattr(in_edge, 'Label'):
                in_edge = in_edge.Label
            self.query.add('inE', in_edge).add('inV', None)

        return self

    def filter_by_outgoing_edge(self, *properties):
        for out_edge in properties:
            if hasattr(out_edge, 'Label'):
                out_edge = out_edge.Label
            self.query.add('inE', out_edge).add('inV')

        return self

    def tag_as(self, tag):
        self.query.add('as', tag)
        return self

    def select_with_tag(self, tag):
        self.query.add('select', tag)
        return self

    def through_outgoing_edge(self, Label=None):
        if Label:
            if hasattr(Label, 'Label'):
                Label = Label.Label
            self.query.add('out', Label)
        else:
            self.query.add('out', None)
        return self

    def through_incoming_edge(self, Label=None):
        if Label:
            if hasattr(Label, 'Label'):
                Label = Label.Label
            self.query.add('in', Label)
        else:
            self.query.add('in', None)
        return self

    def through_edge(self, Label=None):
        if Label:
            if hasattr(Label, 'Label'):
                Label = Label.Label
            self.query.add('both', Label)
        else:
            self.query.add('both', None)
        return self

    def to_outgoing_edge(self, Label=None):
        if Label:
            if hasattr(Label, 'Label'):
                Label = Label.Label
            self.query.add('outE', Label)
        else:
            self.query.add('outE', None)
        return self

    def to_incoming_edge(self, Label=None):
        if Label:
            if hasattr(Label, 'Label'):
                Label = Label.Label
            self.query.add('inE', Label)
        else:
            self.query.add('inE', None)
        return self

    def to_edge(self, Label=None):
        if Label:
            if hasattr(Label, 'Label'):
                Label = Label.Label
            self.query.add('bothE', Label)
        else:
            self.query.add('bothE', None)
        return self

    def to_destination_vertex(self):
        self.query.add('inV', None)
        return self

    def to_source_vertex(self):
        self.query.add('outV', None)
        return self

    def sort(self, *args, descending=False):
        order = 'decr' if descending else 'incr'
        if not args and not descending:
            self.query.add('order', None)
        else:
            self.query.add('order', None).add('by', *args, [[order]])

        return self

    def get(self, *queries):
        """Gets the first successful query
        """
        queries = list(queries)
        for i, q in enumerate(queries):
            if type(q) is type(self):
                queries[i] = q.query
            elif type(q) is not Traversal:
                queries[i] = Traversal(q)

        self.query.add('coalesce', *queries)
        return self

    def get_values(self, *values):
        self.query.add('values', *values)
        return self

    def group_and_count(self, key=None):
        '''
        counts the number of occourences of each item and 
        groups them into a dictionary.
        Same as group_by(key, Query.relation().count())
        '''
        self.query.add("groupCount", key)
        return self

    def group_by(self, key, value=None):
        """Groups the traversals and returns the
        value specified by 'value' parameter

        The traversals are first grouped and then the
        value is applied over each of the groups
        """
        if type(key) is type(self):
            key = key.query

        self.query.add('group', None).add('by', key)
        if value is not None:
            if type(value) is type(self):
                value = value.query

            self.query.add('by', value)

        return self

    def count(self):
        self.query.add('count', None)
        return self

    def delete(self):
        self.query.add('drop', None)
        return self

    def to_dictionary(self, **kwkeys):
        keys = list(kwkeys)
        self.query.add('project', *keys)
        for k in keys:
            trav = kwkeys[k]
            if type(trav) is type(self):
                trav = trav.query
            self.query.add('by', trav)
        return self

    @staticmethod
    def _get_properties(obj: GraphObject, props: list):
        ret_list = []
        for prop in props:
            r = obj.Properties.get(prop, None)
            if r is not None:
                ret_list.append(r)
        return ret_list

    def fetch_all(self, *args):
        try:
            if not args:
                r = self.fetch_raw()
                return map(GraphObject.instantiate, r)
            else:
                return self.get_values(*args).fetch_raw()
        except Exception as e:
            print(e)
            raise

    def fetch_raw(self, verbose_override=None):
        if verbose_override is not None:
            verb = verbose_override
        else:
            verb = self.verbose

        return run(self.query, verbose=verb)

    def fetch_first(self, *args, ensure_one=False):
        try:
            r = list(self.fetch_all(*args))
            #if len(r) > 0
            return r[0]
        except Exception as e:
            print(e)
            raise

    def clone(self):
        nq = Query(query_space=self.query.clone(), verbose=self.verbose)
        return nq

    #def fetch_one(self):
    #    return GraphObject.instantiate(self.query.next())
