def plugin_wmd():
    src = URL(r=request,c='static',f='plugin_wmd/wmd.js')
    return TAG[''](DIV(_class="wmd-preview"),SCRIPT(_src=src))
