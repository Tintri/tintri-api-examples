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
from datetime import datetime

"""
 This Python script deletes the oldest user generated snapshot.

 Command usage: delete_snapshot <server_name> <userName> <password>

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
    print("\nDelete the oldest user generated snapshot.\n")
    print("Usage: " + sys.argv[0] + " server_name user_name password\n")
    sys.exit(-1)

server_name = sys.argv[1]
user_name = sys.argv[2]
password = sys.argv[3]

# Get the preferred version
r = tintri.api_version(server_name)
json_info = r.json()

print_info("API Version: " + json_info['preferredVersion'])

# Login to VMstore
session_id = tintri.api_login(server_name, user_name, password)

# Create filter to get the oldest user generated snapshot
q_filter = {'queryType': 'TOP_DOCS_BY_TIME',
            'limit': '1',
            'type': 'USER_GENERATED_SNAPSHOT'}

# Get the oldest user generated snapshot
url = "/v310/snapshot"
r = tintri.api_get_query(server_name, url, q_filter, session_id)
print_debug("The JSON response of the get invoke to the server " +
            server_name + " is: " + r.text)

# if HTTP Response is not 200 then raise an exception
if r.status_code != 200:
    print_error("The HTTP response for the get invoke to the server " +
          server_name + " is not 200, but is: " + str(r.status_code))
    print_error("url = " + url)
    print_error("response: " + r.text)
    tintri.api_logout(server_name, session_id)
    sys.exit(-10)

snapshot_result = r.json()
number_of_snapshots = int(snapshot_result["filteredTotal"])
print_debug("Number of Snapshots fetched from get Snapshots call to the server " +
      server_name + " is : " + str(number_of_snapshots))

if number_of_snapshots == 0:
    print_error("Cannot proceed, since this are no user generated snapshots")
    tintri.api_logout(server_name, session_id)
    sys.exit(-11)

items = snapshot_result["items"]
snapshot = items[0]

# Collect useful information
vm_name = snapshot["vmName"]
snapshot_uuid = snapshot["uuid"]["uuid"]
raw_create_time = snapshot["createTime"]
formatted_time = datetime.fromtimestamp(int(raw_create_time) / 1000).strftime('%Y-%m-%d %H:%M:%S')
clone_ref_count = snapshot["cloneReferenceCount"]

print("Snapshot " + snapshot_uuid + " created on " + formatted_time + " for VM: " + vm_name)
if clone_ref_count > 0:
    print_error("Can't delete oldest snapshot because its clone reference count is greater than zero.")
    tintri.api_logout(server_name, session_id)
    sys.exit(-12)

# Let's make sure you want to delete the snapshot
answer = raw_input("Delete it? (y/n): ")
if answer != 'y':
    tintri.api_logout(server_name, session_id)
    sys.exit(0)

# Delete the snapshot
url = "/v310/snapshot/"
r = tintri.api_delete(server_name, url + snapshot_uuid, session_id)

# if HTTP Response is not 200 then raise an exception
if r.status_code != 200:
    print_error("The HTTP response for delete call to the server " +
          server_name + " is not 200, but is: " + str(r.status_code))
    print_error("url = " + url)
    print_error("response: " + r.text)
    tintri.api_logout(server_name, session_id)
    sys.exit(-12)


print_info("Successfully deleted " + snapshot_uuid)

tintri.api_logout(server_name, session_id)

 
