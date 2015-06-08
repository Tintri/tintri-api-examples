#!/usr/bin/env/python
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

import json
import sys
import tintri_1_1 as tintri
from prettytable import PrettyTable

"""
 This Python script prints VMstore appliance info.

 Command usage: appliance_info <server_name> <userName> <password>

"""

# For exhaustive messages on console, make it to True; otherwise keep it False
debug_mode = False


def print_with_prefix(prefix, out):
    print(prefix + out)
    return


def print_debug(out):
    if debug_mode:
        print_with_prefix("[DEBUG] : ", out)
    return


def print_error(out):
    print_with_prefix("[ERROR] : ", out)
    return


# main
if len(sys.argv) < 4:
    print("\nPrints VM information\n")
    print("Usage: " + sys.argv[0] + " server_name user_name password\n")
    sys.exit(-1)

server_name = sys.argv[1]
user_name = sys.argv[2]
password = sys.argv[3]

product_name = None
json_info = None

# Get the preferred version and product name
try:
    r = tintri.api_get(server_name, '/info')
    json_info = r.json()
    product_name = json_info['productName']
except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    exit(-1)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    exit(-2)

# Check for correct product
if product_name != "Tintri VMstore":
    print_error("Tintri server needs to be Tintri VMstore, not a " + product_name)
    sys.exit(-8)

session_id = None

# Try to login into the VMstore.
try:
    session_id = tintri.api_login(server_name, user_name, password)
except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    exit(-1)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    exit(-2)
    
appliance_info = None

# Get the appliance information
try:
    url = "/v310/appliance/default/info"
    r = tintri.api_get(server_name, url, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)

    # if HTTP Response is not 200 then raise an error
    if r.status_code != 200:
        message = "The HTTP response for get appliance info call to the server is not 200."
        raise tintri.TintriApiException(message, r.status_code, url, str(Request), r.text)

    appliance_info = r.json()
except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    tintri.api_logout(server_name, session_id)
    exit(-3)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    tintri.api_logout(server_name, session_id)
    exit(-4)

# All pau, log out
tintri.api_logout(server_name, session_id)

print("")

# Now print the information in table form
table_header = ('Info', 'Value')
table = PrettyTable(table_header)
table.align['Info'] = "l"
table.align['Value'] = "l"

row = ('Model', appliance_info['modelName'])
table.add_row(row)

row = ('OS version', appliance_info['osVersion'])
table.add_row(row)

row = ('API version', json_info['preferredVersion'])
table.add_row(row)

print(table)
print("")

