# -*- coding: utf-8 -*-

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.generic_patterns = ['plugins.json']
response.title = 'plugins'
response.subtitle = T('web2py plugins')

##########################################
## this is here to provide shortcuts
## during development. remove in production
##########################################


response.menu=[
    [T('Utils'), False, URL(request.application, 'default', 'utils')],
    [T('Sortable Table'), False, URL(request.application, 'default', 'datatable')],
    [T('Sortable Lists'), False, URL(request.application, 'default', 'sortable')],
    [T('Multiselect'), False, URL(request.application, 'default', 'multiselect')],
    [T('jqGrid'), False, URL(request.application, 'default', 'jqgrid')],
    [T('Translate'), False, URL(request.application, 'default', 'translate')],
    [T('Simple Comments'), False, URL(request.application, 'default', 'simple_comments')],
    [T('Threaded Comments'), False, URL(request.application, 'default', 'comments')],
    [T('Tagging'), False, URL(request.application, 'default', 'tagging')],
    [T('Rating'), False, URL(request.application, 'default', 'rating')],
    [T('Locking'), False, URL(request.application, 'default', 'locking')],
#    [T('Markitup'), False, URL(request.application, 'default', 'markitup')],
#    [T('Flat Pages'), False, URL(request.application, 'default', 'flatpages')],
    [T('Minimal Modal'), False, URL(request.application, 'default', 'mmodal')],
    [T('Dropdown'), False, URL(request.application, 'default', 'dropdown')],
    [T('Attachments'), False, URL(request.application, 'default', 'attachments')],
#    [T('Calendar'), False, URL(request.application, 'default', 'calendar')],
#    [T('Google Map'), False, URL(request.application, 'default', 'gmap')],
    [T('Latex'), False, URL(request.application, 'default', 'latex')],
    [T('Flash Video'), False, URL(request.application, 'default', 'mediaplayer')],
    [T('Layouts'), False, 'http://web2py.com/layouts'],
    [T('ZenGardern'), False, 'http://web2py.com/zengarden'],
    [T('Google Checkout'),False,
     URL('static','web2py.plugin.google_checkout.w2p')],
    [T('OpenID'),False,'http://bitbucket.org/bottiger/web2py-openid/'],
    [T('Facebook'),False,'http://wiki.github.com/jonromero/fbconnect-web2py/'],
    [T('RPX'),False,'http://www.web2pyslices.com/main/slices/take_slice/28'],
    ]
