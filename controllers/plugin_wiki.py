def page():
    slug = request.args(0)
    w = db.plugin_wiki_page
    h = db.plugin_wiki_page_archive
    page = db(w.slug==slug).select().first()
    if not page and plugin_wiki_editor:
        w.slug.default=slug
        form=crud.create(w,onaccept=crud.archive,next=URL(r=request,args=request.args))
        history=None
    elif page and auth.user_id==page.created_by or plugin_wiki_editor:
        crud.settings.update_deletable=False
        form=crud.update(w,page,onaccept=crud.archive,next=URL(r=request,args=request.args))
        history = db(h.current_record==page.id).select(orderby=~h.modified_on)
    else:
        form=None
        history=None
    if page and not page.public and not auth.user_id:
        redirect(auth.settings.login_url)
    elif page and page.public and not page.active and not auth.user_id:
        page = None
    return dict(form=form,page=page,history=history)
