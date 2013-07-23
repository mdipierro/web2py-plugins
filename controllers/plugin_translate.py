def translate():
    lang = session.plugin_translate_language = request.args(0).split('.')[0]
    return "jQuery(document).ready(function(){jQuery('body').translate('%s');});" % lang
