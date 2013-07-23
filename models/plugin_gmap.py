from gluon.storage import Storage
plugin_gmap=Storage()

plugin_gmap.key='ABQIAAAAnfs7bKE82qgb3Zc2YyS-oBT2yXp_ZAY8_ufC3CFXhHIE1NvwkxSySz_REpPq-4WZA27OwgbtyR3VcA' # key for localhost
plugin_gmap.set=db(db.auth_user.id>0) ### change this to a query that lists records with latitude and longitute
plugin_gmap.represent=lambda row: '%(first_name)s %(last_name)s' % row['auth_user']
# include plugin in views with {{=LOAD('plugin_gmap')}}
