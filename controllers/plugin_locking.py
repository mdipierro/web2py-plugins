def relock():
    lock = db.plugin_locking_lock[request.args(0)]
    if lock.created_by == auth.user_id:
        lock.update_record(modified_on=request.now)
        return 'true'
    return 'false'
