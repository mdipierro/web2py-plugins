def plugin_clickatell_send(text,
                           to = "13605555555",
                           send_as = "13605555556",
                           user = "your_username",
                           password = "your_password",
                           api_id = "your api key"):
    import urllib
    import sys
    url = "http://api.clickatell.com/http/sendmsg"
    config = {}
    config['user'] = user
    config['password'] = password
    config['api_id'] = api_id
    config['from'] = send_as
    config['to'] = to
    config['text'] = text
    query = urllib.urlencode(config)
    file = urllib.urlopen(url, query)
    output = file.read()
    file.close()
    return output
