def url(f,args=request.args,vars={}):
    return URL(r=request,f=f,args=args,vars=vars)

def goto(f,args=request.args,vars={},message='error'):
    session.flash=message
    redirect(url(f,args=args,vars=vars))

def error():
    goto('error')

def get(table, i=0, message='error'):
    try:
        id = int(request.args(i))
    except (ValueError, TypeError, KeyError):
        goto('error',message=message)
    return table[id] or goto('error',message=message)

created_by = Field('created_by',db.auth_user,default=auth.user_id,writable=False,readable=False)
created_on = Field('created_on','datetime',default=request.now,writable=False,readable=False,represent=lambda x: prettydate(x))
modified_by = Field('modified_by',db.auth_user,default=auth.user_id,update=auth.user_id,writable=False,readable=False)
modified_on = Field('modified_on','datetime',default=request.now,update=request.now,writable=False,readable=False,represent=lambda x: prettydate(x))
active = Field('active','boolean',default=True,writable=False,readable=False)

def link(a,b,*fields):
    db.define_table('%s_%s' % (a,b),
                    Field('%s' % a,a),
                    Field('%s' % b,b),
                    created_by,created_on,modified_by,modified_on,active,
                    *fields)
