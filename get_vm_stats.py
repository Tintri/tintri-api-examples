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
from prettytable import PrettyTable


"""
 This Python script displays VM stats.

 Displays key VM statistics.  The statistics are from the latest 
 historical statistics that were collected in the last 10 minutes
 or earlier. 

 Command usage: get_vm_status <server_name> <userName> <password>

"""

# For exhaustive messages on console, make it to True; otherwise keep it False
debug_mode = False


# Holds VM name, UUID, and statistics.
class VmStat:
    def __init__(self, name, uuid, stats):
        self.name = name
        self.uuid = uuid
        self.stats = stats

    def get_name(self):
        return self.name
    
    def get_uuid(self):
        return self.uuid

    def get_stats(self):
        return self.stats

    def get_stat(self, stat):
        if stat in self.stats:
            return self.stats[stat]
        return None
        
# print functions
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


# Returns a dictionary of live VM objects with statistics with
# the VM name as the key.
def get_vms(session_id):

    page_size = 25  # default

    # dictionary of VM objects
    vms = {}

    # Get a list of VMs a page size at a time
    get_vm_url = "/v310/vm"
    count = 1
    vm_paginated_result = {'live' : "TRUE",
                           'next' : "offset=0&limit=" + str(page_size)}
    
    # While there are more VMs, go get them
    while 'next' in vm_paginated_result:
        url = get_vm_url + "?" + vm_paginated_result['next']

        # This is a work-around for a TGC bug.
        chop_i = url.find("&replicationHasIssue")
        if chop_i != -1:
            url = url[:chop_i]
            print_debug("Fixing URL")

        print_debug("Next GET VM URL: " + str(count) + ": " + url)
    
        # Invoke the API
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
            num_filtered_vms = vm_paginated_result["filteredTotal"]
            if num_filtered_vms == 0:
                print_error("No VMs present")
                tintri.api_logout(server_name, session_id)
                sys_exit(-99)
    
        # Get and store the VM items and save in a VM object.
        items = vm_paginated_result["items"]
        for vm in items:
            vm_name = vm["vmware"]["name"]
            vm_uuid = vm["uuid"]["uuid"]
            vm_stats = VmStat(vm_name, vm_uuid, vm["stat"]["sortedStats"][0])
            print_debug(str(count) + ": " + vm_name + ", " + vm_uuid)
            count += 1
			
			# Store the VM stats object keyed by VM name.
            vms[vm_name] = vm_stats

    return vms


# main
if len(sys.argv) < 4:
    print("\nCollect VM stats")
    print("Usage: " + sys.argv[0] + " server_name user_name password");
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

vms = get_vms(session_id)

# Logout
tintri.api_logout(server_name, session_id)

# Define the statistic fields to display.  The fields can be changed
# without modifying the print code below.  See the API documentation
# for more statistic fields.
stat_fields = ['spaceUsedGiB', 'operationsTotalIops', 'latencyTotalMs']

# Create the table header with the fields
table_header = ["VM name"]
for field in stat_fields:
    table_header.append(field)

table = PrettyTable(table_header)
table.align["VM name"] = "l"

# Build the table rows based on the statistic fields
for key, value in sorted(vms.items()):
    print_debug(key + " " + value.get_uuid())

    row = [value.get_name()]
    for field in stat_fields:
        stat = value.get_stat(field)
        if stat is None:
            row.append("---")
        else:
            row.append(stat)
    table.add_row(row)

# Print the table
print(table)
