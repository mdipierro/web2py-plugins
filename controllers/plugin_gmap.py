def index():
    width = request.vars.width or 400
    height = request.vars.height or 300
    rows = plugin_gmap.set.select()
    for row in rows:
        row.plugin_gmap_popup = plugin_gmap.represent(row)
    return dict(width=width,height=height,rows=rows,GOOGLEMAP_KEY=plugin_gmap.key)
