db.define_table('fruit',
    Field('sortable','integer',default=0,writable=False,readable=False),
    Field('client',default=request.client,writable=False,readable=False),
    Field('name',requires=IS_NOT_EMPTY()))

my_fruits = db.fruit.client==request.client

if not db(my_fruits).count():
    db.fruit.client.default=request.client
    db.fruit.insert(name='Apple')
    db.fruit.insert(name='Melon')
    db.fruit.insert(name='Banana')
    db.fruit.insert(name='Strawberry')
    db.fruit.insert(name='Raspberry')

db.define_table('preference',
                Field('name'),
                Field('fruit',db.fruit))
db.preference.fruit.requires=IS_IN_DB(db(db.fruit.client==request.client),'fruit.id','%(name)s')
