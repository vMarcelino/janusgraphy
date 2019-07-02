# tests


def test_version():
    from janusgraphy import __version__
    assert __version__ == '0.1.0'


def test_connection():
    import janusgraphy
    janusgraphy.connect_master()


def test_graph_object_creation():
    import janusgraphy
    from janusgraphy.query import Query
    janusgraphy.connect_master()

    c = lambda: Query(verbose=True).count().fetch_first()

    count_initial = c()

    class From(janusgraphy.Edge):
        pass

    class Category(janusgraphy.Vertex):
        Structure = ['name']

    class Document(janusgraphy.Vertex):
        Structure = ['name', 'contents']

        def __init__(self, category: Category, name: str, contents):
            super().__init__(name=name, contents=contents)
            self.add_edge(From, category)

    conf_cat = Category(name='config')
    gitignore_doc = Document(name='.gitignore', category=conf_cat, contents='.')

    count_after = c()

    conf_cat.remove_from_graph()
    gitignore_doc.remove_from_graph()

    count_final = c()
    assert count_initial == count_final and count_after == count_initial + 2
