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

import json
import sys
import tintri_1_1 as tintri

"""
 This Python script gets all the VMs in paged invocation.
 Paged invocations are useful so that the client doesn't have to suck-in
 all the information at one time.

 Command usage: get_vms_paged <server_name> <userName> <password>

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


def print_info(out):
    print_with_prefix("[INFO] : ", out)
    return


def print_error(out):
    print_with_prefix("[ERROR] : ", out)
    return


# main
if len(sys.argv) < 4:
    print("\nPrints VM information using pagination\n")
    print("Usage: " + sys.argv[0] + " server_name user_name password\n")
    sys.exit(-1)

server_name = sys.argv[1]
user_name = sys.argv[2]
password = sys.argv[3]

# Could make this an input parameter
page_size = 25

# Get the preferred version
r = tintri.api_version(server_name)
json_info = r.json()

print_info("API Version: " + json_info['preferredVersion'])

# Login to VMstore
session_id = tintri.api_login(server_name, user_name, password)

# Get a list of VMs, but return a page size at a time
get_vm_url = "/v310/vm"
count = 1
vm_paginated_result = {'next' : "offset=0&limit=" + str(page_size)}

# While there are more Vms, go get them
while 'next' in vm_paginated_result:
    url = get_vm_url + "?" + vm_paginated_result['next']
    print_debug("Next GET VM URL: " + str(count) + ": " + url)

    r = tintri.api_get(server_name, url, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)
    
    # if HTTP Response is not 200 then raise an error
    if r.status_code != 200:
        print_error("The HTTP response for the get invoke to the server " +
              server_name + " is not 200, but is: " + str(r.status_code))
        print_error("url = " + url)
        print_error("response: " + r.text)
        tintri.api_logout(server_name, session_id)
        sys.exit(-10)

    # For each VM in the page, print the VM name and UUID.
    vm_paginated_result = r.json()

    # Check for the first time through the loop and
    # print the total number of VMs.
    if count == 1:
        num_vms = vm_paginated_result["filteredTotal"]
        if num_vms == 0:
            print_error("No VMs present")
            break

        print_info(str(num_vms) + " VMs present")

    items = vm_paginated_result["items"]
    for vm in items:
        vm_name = vm["vmware"]["name"]
        vm_uuid = vm["uuid"]["uuid"]
        print(str(count) + ": " + vm_name + ", " + vm_uuid)
        count += 1

# All pau, log out
tintri.api_logout(server_name, session_id)

