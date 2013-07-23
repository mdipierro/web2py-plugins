db.define_table('plugin_simple_comments_comment',
                Field('tablename',default=request.args(0),
                      writable=False,readable=False),
                Field('record_id','integer',default=request.args(1),
                      writable=False,readable=False),
                Field('body',requires=IS_NOT_EMPTY(),label='Your comment'),
                Field('created_by',db.auth_user,default=auth.user_id,
                      readable=False,writable=False),
                Field('created_on','datetime',default=request.now,
                      readable=False,writable=False))

def plugin_simple_comments(tablename=None,record_id=None):
    return LOAD('plugin_simple_comments','commenton',args=(tablename,record_id),ajax=True)
