#from applications.[yourapp].modules.rpxauth import
rpxauth = local_import('plugin_rpx.rpxauth')
rpxauth = rpxauth.RPXAuth(auth)
#rpxAuth.embed = True
#rpxAuth.allow_local = True
rpxauth.api_key = "..."
rpxauth.realm = "..."
rpxauth.token_url = "http://127.0.0.1:8000/plugins/default/user/login"

"""
rpxauth.mappings.MyOpenID = dict(identifier="identifier",
                                 username="preferredUsername",
                                 email="email",
                                 first_name="givenName",
                                 last_name="familyName")
def split_name(user,provider):
    if provider=="Yahoo":
        user.first_name = user.first_name.split(" ")[0]
        user.last_name = user.last_name.split(" ")[1]
    return user

rpxauth.on_mapped = split_name
"""
