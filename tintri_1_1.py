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

import sys
import json
import requests
import urllib3

# disable security warnings
requests.packages.urllib3.disable_warnings()

"""
 Python functions to assist with Tintri API calls for the explict purpose
 of supporting Tintri's python examples.

 1.1 - added exceptions

 This library was NOT designed to be a general purpose Python library.

"""

API = "/api"


# Exception class for requests errors
class TintriRequestsException(Exception):
    def __init__(self, *args):
        self._message = args[0]


    def __str__(self):
        return self._message


# Exception class for API errors
class TintriApiException(Exception):
    def __init__(self, *args):
        self._message = args[0]
        self.status_code = args[1]
        self.url = args[2]
        self.payload = args[3]
        self.response = args[4]


    def __str__(self):
        return "%s status code=%d url:%s payload:%s response:%s" % \
            (self._message, self.status_code, self.url, self.payload, self.response)


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
        raise TintriRequestsException("GET: API Connection error occurred.")
    except requests.HTTPError:
        raise TintriRequestsException("HTTP error occurred.")
    except requests.Timeout:
        raise TintriRequestsException("Request timed out.")
    except:
        raise TintriRequestsException("An unexpected error " + sys.exc_info()[0] + " occurred.")

    # if HTTP Response is not 200 then raise an exception
    if r.status_code != 200:
        message = "The HTTP response for get call to the server is not 200."
        if (query is None):
            raise TintriApiException(message, r.status_code, url, "No Payload", r.text)
        else:
            raise TintriApiException(message, r.status_code, url, query, r.text)

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
        raise TintrRequestsiApiException("API Connection error occurred.")
    except requests.HTTPError:
        raise TintriRequestsException("HTTP error occurred.")
    except requests.Timeout:
        raise TintriRequestsException("Request timed out.")
    except:
        raise TintriRequestsException("An unexpected error " + sys.exc_info()[0] + " occurred.")

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
        raise TintriRequestsException("API Connection error occurred.")
    except requests.HTTPError:
        raise TintriRequestsException("HTTP error occurred.")
    except requests.Timeout:
        raise TintriRequestsException("Request timed out.")
    except:
        raise TintriRequestsException("An unexpected error " + sys.exc_info()[0] + " occurred.")

    return r


# POST
def api_post(server_name, api, payload, session_id):
    headers = {'content-type': 'application/json',
               'cookie': 'JSESSIONID='+session_id }

    url = 'https://' + server_name + API + api

    try:
        # Invoke the API.
        r = requests.post(url, data=json.dumps(payload),
                          headers=headers, verify=False)
    except requests.ConnectionError:
        raise TintriRequestsException("API Connection error occurred.")
    except requests.HTTPError:
        raise TintriRequestsException("HTTP error occurred.")
    except requests.Timeout:
        raise TintriRequestsException("Request timed out.")
    except:
        raise TintriRequestsException("An unexpected error " + sys.exc_info()[0] + " occurred.")

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
        raise TintriRequestsException("Login: API Connection error occurred.")
    except requests.HTTPError:
        raise TintriRequestsException("Login: HTTP error occurred.")
    except requests.Timeout:
        raise TintriRequestsException("Login: Request timed out.")
    except:
        raise TintriRequestsException("Login: An unexpected error " + sys.exc_info()[0] +
            " occurred.")

    # if HTTP Response is not 200 then raise an exception
    if r.status_code != 200:
        message = "The HTTP response for login call to the server is not 200."
        raise TintriApiException(message, r.status_code, url_login, str(payload), r.text)

    session_id = r.cookies['JSESSIONID']

    return session_id


# Logout
def api_logout(server_name, session_id):
    #Header and URL for logout call
    headers = {'content-type': 'application/json',
               'cookie': 'JSESSIONID='+session_id }
    url_logout = 'https://' + server_name + API + '/v310/session/logout'

    try:
        # Send the logout request.
        r = requests.get(url_logout, headers=headers, verify=False)
    except requests.ConnectionError:
        raise TintriRequestsException("Logout: API Connection error occurred.")
    except requests.HTTPError:
        raise TintrRequestsiApiException("Logout: HTTP error occurred.")
    except requests.Timeout:
        raise TintriRequestsException("Logout: Request timed out.")
    except:
        raise TintriRequestsException("Logout: An unexpected error " + sys.exc_info()[0] +
            " occurred.")

    # if HTTP Response is not 204 then raise an exception
    if r.status_code != 204:
        message = "The HTTP response for logout call to the server is not 204."
        raise TintriApiException(message, r.status_code, url_logout, "No Payload", r.text)

    return

# Return API version information
def api_version(server_name):

    r = api_get(server_name, '/info')
    return r


# Download a file
def download_file(server_name, report_url, session_id, file_name):
    headers = {'content-type': 'application/json'}

    try:
        r = requests.get(report_url, headers=headers, verify=False, stream=True)
        # if HTTP Response is not 200 then raise an exception
        if r.status_code != 200:
            message = "The HTTP response for get call to the server is not 200."
            raise TintriApiException(message, r.status_code, report_url, "No Payload", r.text)

        with open(file_name, 'w') as file_h:
            for block in r.iter_content(4096):
                file_h.write(block)

    except requests.ConnectionError:
        raise TintriRequestsException("API Connection error occurred.")
    except requests.HTTPError:
        raise TintriRequestsException("HTTP error occurred.")
    except requests.Timeout:
        raise TintriRequestsException("Request timed out.")
    except Exception as e:
        raise TintriRequestsException("An unexpected error: " + e.__str__())

