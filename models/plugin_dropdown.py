class PluginDropdown:
    def __init__(self,field=None,caption='New',close="Close",id=None,width=70,height=70,
                 create=None,select=None):
        import uuid
        self.field=field
        self.caption=caption
        self.close=close
        self.id=id or str(uuid.uuid4()).replace('-','')
        self.width=width
        self.height=height
        self.create=create or URL(r=request,c='plugin_dropdown',f='create',args=str(field))
        self.select=select or URL(r=request,c='plugin_dropdown',f='select',args=str(field))
    def __str__(self):
        return self.xml()
    def xml(self):
        session['_plugin_dropbox:%s' % self.field]=None
        return '<div id="%(id)s" style="display:none"><div style="position:fixed;top:0%%;left:0%%;width:100%%;height:100%%;background-color:black;z-index:1001;-moz-opacity:0.8;opacity:.80;opacity:0.8;"></div><div style="position:fixed;top:%(top)s%%;left:%(left)s%%;width:%(width)s%%;height:%(height)s%%;padding:16px;border:2px solid black;background-color:white;opacity:1.0;z-index:1002;overflow:auto;-moz-border-radius: 10px; -webkit-border-radius: 10px;"><span style="font-weight:bold">%(title)s</span><span style="float:right">[<a href="#" onclick="jQuery.ajax({url:\'%(select)s\',success:function(data){jQuery(\'select[name=%(name)s]\').html(data);}});jQuery(\'#%(id)s\').hide();return false;">%(close)s</a>]</span><hr/><div style="width:100%%;height:90%%;" id="c%(id)s"><iframe id="attachments_modal_content" style="width:100%%;height:100%%;border:0">loading...</iframe></div></div></div><a href="#" onclick="jQuery(\'#attachments_modal_content\').attr(\'src\',\'%(create)s\');jQuery(\'#%(id)s\').fadeIn(); return false">%(title)s</a>' % dict(title=self.caption,create=self.create,select=self.select,close=self.close,id=self.id,left=(100-self.width)/2,top=(100-self.height)/2,width=self.width,height=self.height,name=self.field.name)
