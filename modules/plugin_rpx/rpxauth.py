#!/usr/bin/env python 
# coding: utf8 

"""
   RPX Authentication for web2py 
   Developed by Nathan Freeze (Copyright © 2009)
   Email <nathan@freezable.com>
   License: GPL v2
   
   This file contains code to allow using RPXNow.com
   services with web2py
"""

import urllib
from gluon.html import *
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
from gluon.tools import fetch
from gluon.globals import Storage
import gluon.contrib.simplejson as json
from gluon.contrib.login_methods.cas_auth import CasAuth

class RPXAuth(CasAuth):
    def __init__(self, auth, api_key="",embed=False, 
                 auth_url = "https://rpxnow.com/api/v2/auth_info",
                 realm = "",
                 token_url = "",
                 prompt = "Choose a provider",
                 language= "en",
                 allow_local = False,
                 on_login_failure = None,
                 on_mapped = None
                 ):
        
        self.auth = auth
        self.db = auth.db
        self.environment = auth.environment                      
        self.api_key=api_key
        self.embed = embed
        self.auth_url = auth_url
        self.realm = realm
        self.token_url = token_url
        self.prompt = prompt
        self.language = language     
        self.profile = None   
        self.allow_local = allow_local
        self.on_login_failure = on_login_failure
        self.on_mapped = on_mapped
        self.mappings = Storage()
        self.mappings.Google= dict(identifier="identifier",
                                   username="preferredUsername",
                                   email="email",
                                   first_name="givenName",
                                   last_name="familyName")
        
        self.mappings.Yahoo = dict(identifier="identifier",
                                   username="preferredUsername",
                                   email="email",
                                   first_name="formatted",
                                   last_name="formatted")
        
    def search_profile(self, profile, field):
        if profile.has_key(field):
            return profile[field]
        for k,v in profile.items():
            if isinstance(v,dict):
                return self.search_profile(v,field)       
        return ''       
    
    def get_mapping(self,provider,field):
        mapping = self.mappings[provider]
        if field in mapping:
            key = mapping[field]
            value = self.search_profile(self.profile,key)
            return value
        return ''
    
    def get_user(self):
        import string
        request = self.environment.request
  
        if request.vars.token:
            user = Storage()
            data = urllib.urlencode(dict(apiKey=self.api_key,
                                         token=request.vars.token))
            auth_info_json = fetch("?".join([self.auth_url,data]))
            auth_info = json.loads(auth_info_json)
            if auth_info['stat'] == 'ok':
                self.profile = auth_info['profile']
                provider = self.profile['providerName']
                provider = ''.join(c for c in provider if c in string.ascii_letters)
                for field in self.auth.settings.table_user.fields:
                    user[field] = self.get_mapping(provider,field)
                if self.on_mapped and user:
                    user = self.on_mapped(user,provider)
                if self.allow_local:
                    db = self.db
                    user_table = self.auth.settings.table_user
                    if 'username' in user_table.fields:
                        username = 'username'
                    else:
                        username = 'email'
                    existing = db(user_table[username]==user[username]).select()
                    if len(existing):
                        dbuser = existing.first()
                        if dbuser[self.auth.settings.password_field] != None:
                            self.environment.session.flash = '%s already in use' % username.capitalize()
                            return None
                        if 'registration_key' in user_table.fields:
                            if dbuser['registration_key']:
                                self.environment.session.flash = '%s already in use' % username.capitalize()
                                return None
                return user
            else:
                return None
                #auth_info['err']['msg']                        
        return None
    
    def login_url(self,next=None):
        if not self.on_login_failure:
            return self.auth.settings.login_url
        return self.on_login_failure
        
    def __call__(self):
        request = self.environment.request
        args = request.args
        
        if not 'login' in args:
            if not self.allow_local:
                disabled = self.auth.settings.actions_disabled
                if not 'register' in disabled:
                    disabled.append('register')
                if not 'retrieve_password' in disabled:
                    disabled.append('retrieve_password') 
            return self.auth()
        
        if self.auth.is_logged_in():
            redirect(self.auth.settings.login_next)
            
        if request.vars.token:
            return self.auth() 
               
        rpxform = form = DIV()
        
        if self.allow_local:
           self.auth.settings.login_form = self.auth
           form = DIV(self.auth())
           self.auth.settings.login_form = self               
                               
        if self.embed:           
           rpxform = IFRAME(_src="https://%s.rpxnow.com/openid/embed?token_url=%s&language_preference=%s" % \
                                (self.realm, self.token_url, self.language),
                          _scrolling="no",
                          _frameborder="no",
                          _style="width:400px;height:240px;")
        else:            
            rpxform = DIV(A(self.prompt,_class="rpxnow",_onclick="return false;",
                          _href="https://%s.rpxnow.com/openid/v2/signin?token_url=%s" % \
                               (self.realm, self.token_url)),
                       SCRIPT(_src="https://rpxnow.com/openid/v2/widget",
                              _type="text/javascript"),
                       SCRIPT("RPXNOW.overlay = true;",
                              "RPXNOW.language_preference = '%s';" % self.language,
                              _type="text/javascript"))
        
        form.components.append(rpxform)
        return form