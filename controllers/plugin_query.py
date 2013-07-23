op = {
    '>':str(T('greater than')),
    '<':str(T('less than')),
    '>=':str(T('greater then or equal to')),
    '<=':str(T('less then or equal to')),
    '==':str(T('equal to')),
    '!=':str(T('not equal')),
    'startswith':str(T('starts with')),
    'endswith':str(T('end with')),
    'contains':str(T('contains')),
    'belongs':str(T('belongs')),
    'ascending':str(T('ascending')),
    'descending':str(T('descending')),
    'all':str(T('all fields')),
    'edit':str(T('edit')),
    'del':str(T('del')),
    'add':str(T('add')),
    'and':str(T('and')),
    'or':str(T('or')),
}

def parse_query(query,db,tables):
    if query[0] == 'or':
        return parse_query(query[1],db,tables)|parse_query(query[2],db,tables)
    elif query[0] == 'and':
        return parse_query(query[1],db,tables)&parse_query(query[2],db,tables)
    else:
        if not query[0] in tables:
            raise ValueError
        table=db[query[0]]
        if not query[1] in table.fields:
            raise ValueError
        field = table[query[1]]
        if len(query)>4:
            if not query[3] in tables:
                raise ValueError
            othertable = db[query[3]]
            if not query[4] in othertable.fields:
                raise ValueError
            value = othertable[query[4]]
        else:
            value = query[3]
        if not field.readable:
            raise ValueError
        if query[2] == '>':
            return field>value
        elif query[2] == '>=':
            return field>=value
        elif query[2] == '==':
            return field==value
        elif query[2] == '!=':
            return field!=value
        elif query[2] == '<':
            return field<value
        elif query[2] == '<=':
            return field<=value
        elif query[2] == 'startswith':
            return field.like(value+'%')
        elif query[2] == 'endswith':
            return field.like('%'+value)
        elif query[2] == 'contains':
            return field.like('%'+value+'%')
        elif query[2] == 'belongs':
            return field.belongs(value.split(','))

def parse_fields(f,db,tables):
    fields=[]
    for table,field in f:
        if table in db.tables and field in db[table].fields and db[table][field].readable:
            fields.append(db[table][field])
        elif table in db.tables and field=='*':
            fields.append(db[table].ALL)
        else:
            raise ValueError
    return fields

def parse_orderby(f,db,tables):
    fields=[]
    for table,field,asc in f:
        if table in db.tables and field in db[table].fields and db[table][field].readable:
            if asc:
                fields.append(db[table][field])
            else:
                fields.append(~db[table][field])
        else:
            raise ValueError
    if not fields:
        return None
    q = fields[0]
    for field in fields[1:]:
        q=q|field
    return q

def parse(p,db,tables):
    (q,f,o,l) = p
    query = parse_query(q,db,tables)
    fields = parse_fields(f,db,tables)
    orderby = parse_orderby(o,db,tables)
    limitby = l
    return query, fields, orderby, limitby

def get_fields(db,tables):
    def op(field):
        if field.type in ['string','text','upload']:
            return ('<','<=','==','!=','>','>=','startswith','endswith','contains','belongs')
        else:
            return ('<','<=','==','!=','>','>=')
    fields = []
    for table in tables:
        fields.append([table,[(f,db[table][f].label,op(db[table][f])) \
                                  for f in db[table].fields if db[table][f].readable]])
    return fields

def widget_query_rec(query,db,tables,counter):
    if query[0]=='or':
        return TABLE(TR(TD(op['or'],_rowspan=2,_class='st_wrap'),
                        widget_query_rec(query[1],db,tables,counter)),
                     TR(widget_query_rec(query[2],db,tables,counter)),_class='st_table')
    elif query[0]=='and':
        return TABLE(TR(TD(op['and'],_rowspan=2,_class='st_wrap'),
                        widget_query_rec(query[1],db,tables,counter)),
                     TR(widget_query_rec(query[2],db,tables,counter)),_class='st_table')
    else:
        counter[0]+=1
        return TD(query[0]+' '+query[1]+' '+op[query[2]]+' '+repr(query[3]),' [',A(op['edit']),'|',A(op['del'],_href=URL(r=request,f='delete_query',args=counter[0])),'|',A(op['and']),'|',A(op['or']),']',_class='st_in')

def widget_fields_rec(orderby):
    return TABLE(_class='st_table',*[TR(TD(row[0]+' '+(row[1] if row[1]!='*' else op['all']),' [',A(op['edit']),'|',A(op['del']),'|',A(op['add']),']',_class='st_in')) for row in orderby])

def widget_orderby_rec(fields):
    return TABLE(_class='st_table',*[TR(TD(row[0]+' '+row[1]+' '+(op['ascending'] if row[2] else op['descending']),' [',A(op['edit']),'|',A(op['del']),'|',A(op['add']),']',_class='st_in')) for row in fields])

def widget_limitby_rec(limitby):
    return TD('from %i to %i' % (limitby[0],limitby[1]+1), _class='st_in')

def widget(p,db,tables):
    counter= [0]
    t = TABLE(_class='st_out')
    t.append(TR(TD(T('select'),_class='st_wrap_top'),widget_query_rec(p[0],db,tables,counter)))
    t.append(TR(TD(T('fields'),_class='st_wrap_middle'),widget_fields_rec(p[1])))
    t.append(TR(TD(T('order by'),_class='st_wrap_middle'),widget_orderby_rec(p[2])))
    t.append(TR(TD(T('limit by'),_class='st_wrap_bottom'),widget_limitby_rec(p[3])))
    return t


def index():
    p = [
        ['or',
         ['auth_user','id','>',0],
         ['and',
          ['auth_user','id','==',0],
          ['auth_user','first_name','==', 'Mark'],
          ]
         ], [['auth_user','id'],['auth_user','first_name']], [['auth_user','id', True]], [0,10]]
    if not session.p: session.p=p
    p=session.p
    print get_fields(db,['auth_user'])
    (q,f,o,l) = parse(p,db,['auth_user'])
    return dict(t=widget(p,db,['auth_user']))

def edit_query(): return dict()
def del_query(): return dict()
def or_query(): return dict()
def and_query(): return dict()

def edit_field(): return dict()
def del_field(): return dict()
def add_field(): return dict()

def edit_orderby(): return dict()
def del_orderby(): return dict()
def add_orderby(): return dict()
