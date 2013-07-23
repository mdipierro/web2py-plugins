@auth.requires_login()
def commenton():
    tablename, record_id = request.args(0), request.args(1)
    table=db.plugin_simple_comments_comment
    form=SQLFORM(table)
    form.accepts(request.post_vars)
    comments=db(table.tablename==tablename)\
        (table.record_id==record_id).select()
    return dict(form = form,comments=comments)
