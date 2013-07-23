# -*- coding: utf-8 -*-

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

def index():
    redirect(URL(r=request,f='sortable'))

def dropdown():
    db.preference.fruit.comment=PluginDropdown(db.preference.fruit)
    return dict(form=crud.create(db.preference))

def translate():
    return dict()

def sortable():
    response.flash='Hello from web2py'
    fruits = db(my_fruits).select(orderby=db.fruit.sortable)
    return dict(fruits = fruits)

def datatable():
    db(db.shout.message.like('%|%')).delete()
    if db(db.shout.id>0).count()>100:
        db(db.shout.id>1).delete()
    return dict()

def jqgrid():
    db(db.shout.message.like('%|%')).delete()
    if db(db.shout.id>0).count()>100:
        db(db.shout.id>1).delete()
    return dict()

def locking():
    lock = plugin_locking(request.session_id)
    return dict(lock=lock)

def multiselect():
    db.shout.message.requires=IS_IN_SET((1,2),('love you','hate you'),multiple=True)
    return dict()

def comments():
    return dict()

def tagging():
    return dict()

def rating():
    return dict()

def mediaplayer():
    return dict()

def layouts():
    redirect('/layouts')

def sort():
    plugin_sortable_sort(db.fruit,query=my_fruits)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    session.forget()
    return service()

def latex():
    return dict()

def simple_comments():
    return dict()

def mmodal():
    return dict()

def attachments():
    return dict()

def utils():
    return dict()

def markitup():
    return dict()

def wiki():
    return dict()

def flatpages():
    return dict()

def calendar():
    return dict()

def gmap():
    return dict()
