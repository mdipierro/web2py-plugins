db.define_table('plugin_wiki_page',
                Field('slug',requires=(IS_SLUG(),IS_NOT_IN_DB(db,'plugin_wiki_page.slug')),
                      represent=lambda slug: '%s' % slug,writable=False),
                Field('title',requires=(IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'plugin_wiki_page.title'))),
                Field('active','boolean',default=False),
                Field('public','boolean',default=False),
                Field('body','text'),
                Field('created_by',db.auth_user,default=auth.user_id,
                      writable=False,readable=False),
                Field('created_on','datetime',default=request.now,
                      writable=False,readable=False),
                Field('modified_by',db.auth_user,default=auth.user_id,update=auth.user_id,
                      writable=False,readable=False),
                Field('modified_on','datetime',default=request.now,update=request.now,
                      writable=False,readable=False),
                format = '%(slug)s')

db.define_table('plugin_wiki_page_archive',
                Field('current_record',db.plugin_wiki_page),
                db.plugin_wiki_page,
                format = '%(slug) %(modified_on)s')

if not 'plugin_wiki_editor' in globals():
    plugin_wiki_editor = auth.user_id


def plugin_wiki_render(text):
    import re
    from gluon.contrib.markdown import WIKI
    """
    [link](page:test.abc) -> <a href=".../plugin_wiki/page/this-is-a-slug">link</a>
    [link](attachment:123.abc) -> <a href=".../attachment/123.abc">link</a>
    ![wav file](attachment:test.wav) -> flash player
    ![mp3 file](attachment:test.mp3) -> flash player
    ![flv file](attachment:test.flv) -> flash player
    ![mp4 file](attachment:test.mp4) -> flash player
    """

    text=text or ''
    re_flv=re.compile('\<img\s+src="(?P<src>[^"]+\.(flv|wav|mp3|mpeg3|mp4|mpeg4|mov))"\s+alt="(?P<alt>[^"]*)"\s*/\>')
    re_youtube=re.compile('\<img\s+src="http://www.youtube.com/watch\?v=(?P<code>\w+)"\s+alt="(?P<alt>[^"]*)"\s*/\>')
    re_vimeo=re.compile('\<img\s+src="http://vimeo.com/(?P<code>\w+)"\s+alt="(?P<alt>[^"]*)"\s*/\>')
    text=text.replace('!(','![no name](')
    text=text.replace('](page:','](%s/' % URL(r=request,c='plugin_wiki',f='page'))
    text=text.replace('](attachment:','](%s/' % URL(r=request,c='plugin_attachments',f='attachment'))
    re_code = re.compile('<code>(?P<code>.*?)</code>',re.S)
    while True:
        match = re_code.search(text)
        if not match: break
        code='\n\n    %s\n\n' % '\n    '.join([line for line in match.group('code').split('\n')])
        text=text[:match.start()]+code+text[match.end():]
    html = WIKI(text).xml()
    html = re_flv.sub('<embed allowfullscreen="true" allowscriptaccess="always" flashvars="height=305&width=490&file=\g<src>" height="305px" src="%s" width="490px"></embed>' % URL(r=request,c='static',f='plugin_mediaplayer/mediaplayer.swf'),html)
    html = re_youtube.sub("""<object width="480" height="385"><param name="movie" value="http://www.youtube.com/v/\g<code>&hl=en_US&fs=1&"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="http://www.youtube.com/v/\g<code>&hl=en_US&fs=1&" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="480" height="385"></embed></object>""",html)
    html = re_vimeo.sub("""<object width="400" height="250"><param name="allowfullscreen" value="true" /><param name="allowscriptaccess" value="always" /><param name="movie" value="http://vimeo.com/moogaloop.swf?clip_id=\g<code>&amp;server=vimeo.com&amp;show_title=1&amp;show_byline=1&amp;show_portrait=0&amp;color=&amp;fullscreen=1" /><embed src="http://vimeo.com/moogaloop.swf?clip_id=\g<code>&amp;server=vimeo.com&amp;show_title=1&amp;show_byline=1&amp;show_portrait=0&amp;color=&amp;fullscreen=1" type="application/x-shockwave-flash" allowfullscreen="true" allowscriptaccess="always" width="400" height="250"></embed></object><p><a href="http://vimeo.com/\g<code>">web2py production deployment on vps.net</a> from <a href="http://vimeo.com/user315328">mdipierro</a> on <a href="http://vimeo.com">Vimeo</a>.</p>""",html)
    return XML(html)
