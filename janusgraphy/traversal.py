import gremlin_python
from janusgraphy import client
from janusgraphy import traversal_verbose


class Traversal:
    def __init__(self, t_query=None):
        #print('base query:', t_query)
        if type(t_query) in [str, int, float]:
            t_query = Traversal().add('constant', t_query).query
        self.query = (t_query or [])

    def add(self, *args):
        '''
        t.add('g') = g
        t.add('g', None) = g()
        t.add('g', []) = g()
        t.add('g', 'a') = g('a')
        t.add('g', 'a', 'b') = g('a', 'b')
        '''
        to_add = [args[0]]
        if len(args) > 1:
            if len(args) == 2 and args[1] is None:
                to_add.append([])
            else:
                to_add.append(args[1:])

        self.query.append(to_add)
        return self

    @staticmethod
    def graph():
        t = Traversal()
        t.add('g')
        return t

    @staticmethod
    def vertices():
        t = Traversal.graph()
        t.add('V', None)
        return t

    def __add__(self, other):
        r = None
        if type(other) is type(self):
            r = self.query + other.query

        elif type(other) is list:
            r = self.query + other

        elif type(other) is str:
            r = self.query + [other]

        return Traversal(r)

    def __radd__(self, other):
        r = None
        if type(other) is type(self):
            r = other.traversal_query + self.query

        elif type(other) is list:
            r = other + self.query

        elif type(other) is str:
            r = [other] + self.query

        return Traversal(r)

    def get_traversal_string(self):
        def dot_splt(q):
            rd = ''
            for part in q:
                rd += '.' + part[0]
                if len(part) > 1:
                    if len(part) == 2 and part[1] == []:
                        rd += '()'
                    else:
                        rd += '(' + comma_split(part[1]) + ')'

            return rd[1:]

        def comma_split(q):
            rc = ''
            for part in q:
                if type(part) is str:
                    rc += ', "' + part + '"'

                elif type(part) in [int, float, gremlin_python.statics.long]:
                    rc += ', ' + str(part)

                elif type(part) is type(self):
                    rc += ', ' + part.get_traversal_string()

                elif type(part) is list:
                    rc += ', ' + dot_splt(part)

                else:
                    print('unrecognized type:', str(type(part)))

            return rc[2:]

        r = dot_splt(self.query)
        return r

    def run(self, verbose=None) -> list:
        if verbose is None:
            verbose = traversal_verbose
        ts = self.get_traversal_string().replace('\n', '\\n')
        if verbose:
            print('traversal -->', ts)

        r1 = client.submit(ts)
        r2 = r1.all()
        r3 = r2.result()
        return r3

    def clone(self):
        from copy import deepcopy
        return deepcopy(self)

    @staticmethod
    def edges():
        return Traversal.graph().add('E', None)

    def __repr__(self):
        return f'<Traversal: {self.get_traversal_string()}>'
