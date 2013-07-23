"""
Example of usage:
assume a model like

db.define_table('test',Field('name'),Field('sortable','integer'))

In a view you insert the sortable list as:

{{=plugin_sortable([(r.id,r.name) for r in db(db.test.id>0).select(orderby=db.test.sortable)],callback=URL(r=request,f='sort'))}}

And create a callback controller:

def sort():
    plugin_sortable_sort(db.test,sortable_field='sortable')
"""

response.files.append(URL(r=request,c='static',f='plugin_sortable/jquery.ui.core.js'))
response.files.append(URL(r=request,c='static',f='plugin_sortable/jquery.ui.sortable.js'))

def plugin_sortable(items,callback,_id='sortable',_class='sortable'):
    script=SCRIPT("""
function sortUpdate(a,b) {
    var dragEls = jQuery(".%s_item");
    var els ='';
    jQuery.each(dragEls, function () {
        var cur_id = jQuery(this).attr('id').split('_').shift();
        els += cur_id+",";
    });
    var url = '%s?order='+els;
    jQuery.get(url);
}
jQuery(document).ready(function() {
  jQuery("#%s").sortable({stop:sortUpdate });
});
""" % (_id,callback,_id))
    return TAG[''](UL(_id=_id,_class=_class,
                      *[LI(item,_id="%s_%s"%(id,_id),_class='%s_item'%_id) for (id,item) in items]),
                   script)


def plugin_sortable_sort(table,sortable_field='sortable',query=None):
    for i,id in enumerate(request.vars.order.split(',')[:-1]):
        if not query: db(table.id==id).update(**{sortable_field:i})
        else: db(table.id==id)(query).update(**{sortable_field:i})
