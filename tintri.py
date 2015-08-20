#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2015 Tintri, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import requests
import json
import sys

"""
 Python functions to assist with Tintri API calls for the explict purpose
 of supporting Tintri's python examples.

 This library was NOT designed to be a general purpose Python library.

"""

API = "/api"


# Print errors
def print_error(out):
    print("[ERROR] : " + out)
    return


# API GET without query string.  The session ID can be 'None'.  This is for
# the info API.
def api_get(server_name, api, session_id=None):
    return api_get_query(server_name, api, None, session_id)


# API GET with query string.  The query and  session ID can be 'None'.
# The requests get allows for a query params set to 'None'.
def api_get_query(server_name, api, query, session_id):
    headers = {'content-type': 'application/json'}
    if session_id is not None:
        headers['cookie'] = 'JSESSIONID=' + session_id

    url = 'https://' + server_name + API + api

    try:
        # Invoke the API.
        r = requests.get(url, headers=headers, params=query, verify=False)
    except requests.ConnectionError:
        print_error("API Connection error occurred")
        sys.exit(-2)
    except requests.HTTPError:
        print_error("HTTP error occurred")
        sys.exit(-3)
    except requests.Timeout:
        print_error("Request timed out")
        sys.exit(-4)
    except:
        print_error("An unexpected error " + sys.exc_info()[0] + " occurred")
        sys.exit(-5)

    return r


# API DELETE.
def api_delete(server_name, api, session_id):
    #Header and URL for delete call
    headers = {'content-type': 'application/json',
               'cookie': 'JSESSIONID='+session_id }

    url = 'https://' + server_name + API + api

    try:
        # Invoke the API.
        r = requests.delete(url, headers=headers, verify=False)
    except requests.ConnectionError:
        print_error("API Connection error occurred")
        sys.exit(-2)
    except requests.HTTPError:
        print_error("HTTP error occurred")
        sys.exit(-3)
    except requests.Timeout:
        print_error("Request timed out")
        sys.exit(-4)
    except:
        print_error("An unexpected error " + sys.exc_info()[0] + " occurred")
        sys.exit(-5)

    return r


# PUT
def api_put(server_name, api, payload, session_id):
    headers = {'content-type': 'application/json',
               'cookie': 'JSESSIONID='+session_id }

    url = 'https://' + server_name + API + api

    try:
        # Invoke the API.
        r = requests.put(url, data=json.dumps(payload),
                          headers=headers, verify=False)
    except requests.ConnectionError:
        print_error("API Connection error occurred")
        sys.exit(-2)
    except requests.HTTPError:
        print_error("HTTP error occurred")
        sys.exit(-3)
    except requests.Timeout:
        print_error("Request timed out")
        sys.exit(-4)
    except:
        print_error("An unexpected error " + sys.exc_info()[0] + " occurred")
        sys.exit(-5)

    return r


# Login.
def api_login(server_name, user_name, password):
    # Payload, header and URL for login call
    headers = {'content-type': 'application/json'}
    payload = {'username': user_name,
               'password': password,
               'typeId': 'com.tintri.api.rest.vcommon.dto.rbac.RestApiCredentials'}
    url_login = 'https://'+ server_name + API + '/v310/session/login'

    try:
        # Invoke the login API.
        r = requests.post(url_login, data=json.dumps(payload),
                          headers=headers, verify=False)
    except requests.ConnectionError:
        print_error("Login: API Connection error occurred")
        sys.exit(-2)
    except requests.HTTPError:
        print_error("Login: HTTP error occurred")
        sys.exit(-3)
    except requests.Timeout:
        print_error("Login: Request timed out")
        sys.exit(-4)
    except:
        print_error("Login: An unexpected error " + sys.exc_info()[0] +
                    " occurred")
        sys.exit(-5)

    # if HTTP Response is not 200 then raise an exception
    if r.status_code != 200:
        print_error("The HTTP response for login call to the server " +
                    server_name + " is not 200, but is: " + str(r.status_code))
        print_error("url = " + url_login)
        print_error("payload = " + str(payload))
        print_error("response: " + r.text)
        sys.exit(-6)

    session_id = r.cookies['JSESSIONID']

    return session_id


# Logout
def api_logout(server_name, session_id):
    #Header and URL for logout call
    headers = {'content-type': 'application/json',
               'cookie': 'JSESSIONID='+session_id }
    url_logout = 'https://' + server_name + API + '/v310/session/logout'

    # Send the logout request.
    r = requests.get(url_logout, headers=headers, verify=False)

    # if HTTP Response is not 204 then raise an exception
    if r.status_code != 204:
        print_error("The HTTP response for logout call to the server " +
                    server_name+" is not 204")
        print_error("url = " + url_logout)
        print_error("response: " + r.text)
        sys.exit(-7)

    return


