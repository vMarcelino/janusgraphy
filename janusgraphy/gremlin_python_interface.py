'''
Please ignore this class
'''

traversal_verbose = False


def pformatter(l):
    return map(lambda i: f'==>{str(i)}', l)


def pprinter(l):
    print('\n'.join(pformatter(l)))


#connect()

qrm = lambda q: map(GraphObject.instantiate, client.submit(q).all().result())
qr = lambda q: list(qrm(q))
qrl = qr
qrp = lambda q: pprinter(qrm(q))


class Cls:
    def __repr__(*a, **k):
        import os
        os.system('clear')
        return ""


clear = Cls()

# returns a dict of {name:devicename, status:laststatus} from the selected client
'''
g.V().has("name", "Neuropsicocentro") # gets client
.in("From").has("type", "smartplug").order().by("name", incr) # gets devices sorted by name
.project("name", "status") # prepare projection: a list of dicts of type {name:value1, status:value2}
.by(values("name")) # sets first value
.by(                # sets second value
    coalesce(       # returns the first successfull query
        __.in("From").order().by("date", decr).limit(1).values("message"), # try to return this
         constant("not found")))'   # returns this if the first failed

or

q = Query(verbose=True).filter_by_property(name='Neuropsicocentro')
q.through_incoming_edge("From").filter_by_property(type="smartplug").sort('name')
status_q = Query.relation().through_incoming_edge('From').sort('date', descending=True)[0].get_values('message')
q.to_dictionary(name=Query.relation().get_values('name'), status=Query.relation().get(status_q, '-'))

pprinter(q.fetch_all())
'''

# returns a dict of {subtype:logCount}
"g.V().hasLabel('Log').out('From').has('type', 'smartplug').values('subtype').groupCount()"
#q = Query().filter_by_property(Label="Log").through_outgoing_edge('From').filter_by_property(
#    type='smartplug').get_values('name').group_and_count()
#pprinter(q.fetch_all())