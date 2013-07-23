def plugin_multiselect_include():
    response.files.append(URL(r=request,c='static',f='plugin_multiselect/jquery.dimensions.js'))
    response.files.append(URL(r=request,c='static',f='plugin_multiselect/jquery.multiselect.js'))
    response.files.append(URL(r=request,c='static',f='plugin_multiselect/jquery.multiselect.css'))

def plugin_multiselect(*a,**b):
    return SCRIPT("jQuery(document).ready(function(){jQuery('[multiple]').multiSelect({maxHeight:400});});")

plugin_multiselect_include()
