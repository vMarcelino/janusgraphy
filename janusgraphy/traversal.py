import gremlin_python
import dataclasses


@dataclasses.dataclass
class TraversalLiteral:
    value: str


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

    def get_traversal_string(self) -> str:
        def dot_splt(q) -> str:
            rd = ''
            for part in q:
                rd += '.' + part[0]
                if len(part) > 1:
                    if len(part) == 2 and part[1] == []:
                        rd += '()'
                    else:
                        rd += '(' + comma_split(part[1]) + ')'

            return rd[1:]

        def comma_split(q) -> str:
            rc = []
            for part in q:
                if type(part) is TraversalLiteral:
                    rc.append(part.value)

                elif type(part) is str:
                    rc.append(f'"{part}"')

                elif type(part) is bool:
                    rc.append('true' if part else 'false')

                elif type(part) in [int, gremlin_python.statics.long]:
                    rc.append(str(part))

                elif type(part) is float:
                    rc.append(f'{str(part)}f')

                elif type(part) is type(self):
                    rc.append(part.get_traversal_string())

                elif type(part) is list:
                    rc.append(dot_splt(part))

                else:
                    print('unrecognized type:', str(type(part)))

            return ', '.join(rc)

        r = dot_splt(self.query)
        return r

    def run(self, client=None, verbose=False) -> list:
        ts = self.get_traversal_string().replace('\n', '\\n')

        if client is None:
            from janusgraphy import master_client
            client = master_client

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
