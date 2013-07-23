db.define_table('plugin_attachments_attachment',
                Field('tablename',writable=False,readable=False),
                Field('record_id','integer',writable=False,readable=False),
                Field('name',requires=IS_NOT_EMPTY()),
                Field('file','upload',requires=IS_NOT_EMPTY(),autodelete=True),
                Field('created_by',db.auth_user,default=auth.user_id or 1,
                      writable=False,readable=False),
                Field('created_on','datetime',default=request.now,
                      writable=False,readable=False),
                format='%(name)s')

class PluginAttachments:
    def __init__(self,tablename,record_id=0,caption='Attachments',close="Close",id=None,width=70,height=70):
        import uuid
        self.tablename=tablename
        self.record_id=record_id
        self.caption=caption
        self.close=close
        self.id=id or str(uuid.uuid4())
        self.width=width
        self.height=height
        self.source=URL(r=request,c='plugin_attachments',f='index',args=(tablename,record_id))
    def xml(self):
        return '<div id="%(id)s" style="display:none"><div style="position:fixed;top:0%%;left:0%%;width:100%%;height:100%%;background-color:black;z-index:1001;-moz-opacity:0.8;opacity:.80;opacity:0.8;"></div><div style="position:fixed;top:%(top)s%%;left:%(left)s%%;width:%(width)s%%;height:%(height)s%%;padding:16px;border:2px solid black;background-color:white;opacity:1.0;z-index:1002;overflow:auto;-moz-border-radius: 10px; -webkit-border-radius: 10px;"><span style="font-weight:bold">%(title)s</span><span style="float:right">[<a href="#" onclick="jQuery(\'#%(id)s\').hide();return false;">%(close)s</a>]</span><hr/><div style="width:100%%;height:90%%;" id="c%(id)s"><iframe id="attachments_modal_content" style="width:100%%;height:100%%;border:0">loading...</iframe></div></div></div><a href="#" onclick="jQuery(\'#attachments_modal_content\').attr(\'src\',\'%(source)s\');jQuery(\'#%(id)s\').fadeIn(); return false" style="padding: 0 10px 0 10px; position: fixed; right:0; bottom:0; background: #999; color: white; z-index: 100; clear: both;">%(title)s</a>' % dict(title=self.caption,source=self.source,close=self.close,id=self.id,left=(100-self.width)/2,top=(100-self.height)/2,width=self.width,height=self.height)
