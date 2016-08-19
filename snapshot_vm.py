#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2016 Tintri, Inc.
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
import datetime
import tintri_1_1 as tintri

"""
 This Python script takes a snapshot for the specified VM.

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


# Take a manual snapshot.
def take_snapshot(vm_uuid, snapshot_name, consistency_type, server_name, session_id):
    snapshot_spec = {
        'typeId' : "com.tintri.api.rest.v310.dto.domain.beans.snapshot.SnapshotSpec",
        'consistency' : consistency_type,
        'retentionMinutes' : 240,  # 4 hours
        'snapshotName' : snapshot_name,
        'sourceVmTintriUUID' : vm_uuid }
        
    # The API needs a list of snapshot specifications.
    snapshot_specs = [snapshot_spec]

    ss_url = "/v310/snapshot"
    r = tintri.api_post(server_name, ss_url, snapshot_specs, session_id)
    if (r.status_code != 200):
        msg = "The HTTP response for the post invoke to the server is " + \
              server_name + "not 200, but is: " + str(r.status_code) + "."
        raise tintri.TintriApiException(msg, r.status_code, vm_url, str(snapshot_specs), r.text)

    print_debug("The JSON response of the post invoke to the server " +
                server_name + " is: " + r.text)
    
    # The result is a liset of snapshot UUIDs.
    snapshot_result = r.json()
    print_info(snapshot_name + ": " + snapshot_result[0])
    return


# main
if len(sys.argv) < 5:
    print("\nSnapshot a VM.\n")
    print("Usage: " + sys.argv[0] + " server_name user_name password vm_name [consistency type]\n")
    print("    consistency type can be 'crash' or 'vm'. The default is 'crash'.")
    sys.exit(-1)

server_name = sys.argv[1]
user_name = sys.argv[2]
password = sys.argv[3]
vm_name = sys.argv[4]
if (len(sys.argv) == 6):
    consistency_type = sys.argv[5]
else:
    consistency_type = "crash"

try:
    # Confirm the consistency type.
    if (consistency_type == "crash"):
        consistency_type = "CRASH_CONSISTENT"
    elif (consistency_type == "vm"):
        consistency_type = "VM_CONSISTENT"
    else:
        raise tintri.TintriRequestException("consistency_type is not 'crash' or 'vm': " + consistency_type)

    # Get the preferred version
    r = tintri.api_version(server_name)
    json_info = r.json()

    print_info("API Version: " + json_info['preferredVersion'])

    # Login to VMstore or TGC
    session_id = tintri.api_login(server_name, user_name, password)

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    sys.exit(-10)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    sys.exit(-11)
    

try:
    # Create query filter to get the VM specified by the VM name.
    q_filter = {'name': vm_name}

    # Get the UUID of the specified VM
    vm_url = "/v310/vm"
    r = tintri.api_get_query(server_name, vm_url, q_filter, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)

    vm_paginated_result = r.json()
    num_vms = int(vm_paginated_result["filteredTotal"])
    if num_vms == 0:
        raise tintri.TintriRequestsException("VM " + vm_name + " doesn't exist")

    # Get the information from the first item and hopefully the only item.
    items = vm_paginated_result["items"]
    vm = items[0]
    vm_name = vm["vmware"]["name"]
    vm_uuid = vm["uuid"]["uuid"]

    print_info(vm_name + ": " + vm_uuid)

    # Get the time for the snapshot description.
    now = datetime.datetime.now()
    now_sec = datetime.datetime(now.year, now.month, now.day,
                                now.hour, now.minute, now.second)
    snapshot_name = vm_name + now_sec.isoformat()

    # Take a manual snapshot.
    take_snapshot(vm_uuid, snapshot_name, consistency_type, server_name, session_id)

    # All pau, log out.
    tintri.api_logout(server_name, session_id)

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    tintri.api_logout(server_name, session_id)
    sys.exit(-20)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    tintri.api_logout(server_name, session_id)
    sys.exit(-21)

