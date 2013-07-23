@auth.requires_login()
def index():
    a=db.plugin_attachments_attachment
    a.tablename.default=tablename=request.args(0)
    a.record_id.default=record_id=request.args(1)
    #if request.args(2): a.file.writable=False
    form=crud.update(a,request.args(2),
                     next=URL(r=request,args=request.args[:2]))
    rows=db(a.tablename==tablename)(a.record_id==record_id)\
        .select(orderby=a.name)
    return dict(form=form,rows=rows)

def attachment():
    a=db.plugin_attachments_attachment
    try:
        request.args[0]=a[request.args(0).split('.')[0]].file
    except:
        raise HTTP(400)
    return response.download(request,db)
