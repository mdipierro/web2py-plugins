"""
In the page you want to lock

{{=plugin_locking('tablename',record_id)}}

"""

db.define_table('plugin_locking_lock',
                Field('tablename'),
                Field('record_id','integer'),
                Field('created_by',db.auth_user,default=auth.user_id),
                Field('created_on','datetime',default=request.now),
                Field('modified_on','datetime',default=request.now))

def plugin_locking(
    tablename,record_id=0,
    locktime=60, expiration=3600):
    import datetime
    locks = db(db.plugin_locking_lock.tablename==tablename)\
        (db.plugin_locking_lock.record_id==record_id)
    lock = locks.select().first()
    if lock and lock.created_by!=auth.user_id \
            and lock.modified_on+datetime.timedelta(seconds=locktime)>request.now \
            and lock.created_on+datetime.timedelta(seconds=expiration)>request.now:
        return None
    else:
        if lock: locks.delete()
        lock_id = db.plugin_locking_lock.insert(tablename=tablename,
                                           record_id=record_id)
        return SCRIPT("""function plugin_locking(){ajax("%(callback)s",[],false);setTimeout("plugin_locking()",%(delta)s);};setTimeout("plugin_locking()",%(delta)s);""" % dict(callback=URL(r=request,c='plugin_locking',f='relock',args=lock_id),delta=locktime*300))
