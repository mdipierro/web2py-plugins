#@auth.requires_login()
def create():
    table,field = request.args(0).split('.')
    refereed=db[db[table][field].type[10:]]
    form=crud.create(db[refereed])
    if form.vars.id: session['_plugin_dropbox:%s' % request.args(0)]=form.vars.id
    options = UL(*[LI(v) for k,v in db[table][field].requires.options() if k==str(form.vars.id)])
    return dict(form=form,options=options)

def select():
    if not auth.user_id or not session.get('_plugin_dropbox:%s' % request.args(0),None): raise HTTP(400)
    table,field = request.args(0).split('.')
    return TAG[''](*[OPTION(v,_value=k,_selected=(k==str(session['_plugin_dropbox:%s' % request.args(0)])))\
                                for k,v in db[table][field].requires.options()])
