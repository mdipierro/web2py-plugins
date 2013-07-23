db.define_table('shout',
                Field('message'),
                Field('client',default=request.client,writable=False,readable=False))

if not db(db.shout.id>0).count():
    db.shout.insert(message='Hi there!')
