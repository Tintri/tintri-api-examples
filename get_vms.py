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
 This Python script prints the VM name and UUID for each VM.

 Command usage: get_vms <server_name> <userName> <password>

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
    print("\nPrints VM information\n")
    print("Usage: " + sys.argv[0] + " server_name user_name password\n")
    sys.exit(-1)

server_name = sys.argv[1]
user_name = sys.argv[2]
password = sys.argv[3]

# Get the preferred version
try:
    r = tintri.api_version(server_name)
    json_info = r.json()

    print_info("API Version: " + json_info['preferredVersion'])

    # Login to VMstore
    session_id = tintri.api_login(server_name, user_name, password)

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    exit(-1)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    exit(-2)
    
try:
    # Get a list of VMs, but only return a page size
    url = "/v310/vm"
    r = tintri.api_get(server_name, url, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)

    vm_paginated_result = r.json()
    num_vms = int(vm_paginated_result["filteredTotal"])
    if num_vms == 0:
        raise tintri.TintriRequestsException("No VMs present")

    print_info(str(num_vms) + " VMs present")

    # For each VM, print the VM name and UUID
    items = vm_paginated_result["items"]
    count = 1
    for vm in items:
        vm_name = vm["vmware"]["name"]
        vm_uuid = vm["uuid"]["uuid"]
        vcenter_name = vm["vmware"]["vcenterName"]
        print(str(count) + ": " + vm_name + ", " + vm_uuid + " - " + vcenter_name)
        count += 1

    # All pau, log out
    tintri.api_logout(server_name, session_id)

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    tintri.api_logout(server_name, session_id)
    exit(-5)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    tintri.api_logout(server_name, session_id)
    exit(-6)
