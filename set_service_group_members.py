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
#
# Adds VMs from a CSV file to an existing service group
# Usage: set_service_group_members.py  server_name service_group csv_file\n
# Where:
#   server_name   - TGC server name or IP
#   service_group - existing service group name
#   csv_file      - CSV file that contains VM names

# Standard python libraries
import tintri_1_1 as tt
import json
import csv
import sys
import operator
import os.path
import getpass

debug_mode = False

# Output functions
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


# Obtains VM UUIDs for all the VM names in a list.
# Returns a tuple of (VM UUID list, VM name list).
def get_vm_uuids(vm_list):
    uuid_list = []
    vms_found = []

    result = tt.api_get(server_name, "/v310/vm", session_id)
    all_vms = result.json()

    for vm in all_vms["items"]:
        if vm["vmware"]["name"] in vm_list:
            uuid_list.append(vm["uuid"]["uuid"])
            vms_found.append(vm["vmware"]["name"])
    return (uuid_list, vms_found)


# main
if len(sys.argv) < 3:
    print("\nAdds VMs from a file to a service group")
    print("Usage: " + sys.argv[0] + " server_name service_group csv_file\n")
    print("Where:")
    print("    server_name   - TGC server name")
    print("    service_group - existing service group name")
    print("    csv_file      - CSV file that contains VM names")
    sys.exit(0)

server_name = sys.argv[1]
service_group = sys.argv[2]
file_loc = sys.argv[3]

# List obtain by reading the input file.
vm_list = []

# Credentials Gathering - setup to support Python 2.X and 3.X
try: 
	user_name = raw_input("Enter user name: ")
except NameError:
	user_name = input("Enter user name: ")
passWord = getpass.getpass("Enter password: ")
print("")

try:
    if os.path.isfile(file_loc):
        with open(file_loc,'r') as csv_file:
            vm_csv_list = csv.reader(csv_file)

            # Gets a list of VMs from a CSV file.
            # Should be able to process both Windows and Linux files.
            for row in vm_csv_list:
                for item in row:
                    if item == "":
                        continue
                    vm_list.append(item.lstrip(' '))
    else:
        raise tt.TintriRequestsException("Could not find file " + file_loc)
    		
    # Get the API version and product.
    r = tt.api_version(server_name)
    json_info = r.json()
    preferred_version = json_info['preferredVersion']
    product_name = json_info['productName']
    
    # Check for correct product
    if product_name != "Tintri Global Center":
        raise tt.TintriRequestsException("Tintri server should be Tintri Global Center, not " + product_name)
    
    # Check API version.
    versions = preferred_version.split(".")
    major_version = versions[0]
    minor_version = int(versions[1])
    if major_version != "v310":
        raise tt.TintriRequestsException("Incorrect major version: " + major_version + ".  Should be v310.")
    if minor_version < 31:
        raise tt.TintriRequestsException("Incorrect minor Version: " + minor_version + ".  Should be 31 or greater")
    
    # Login
    session_id = tt.api_login(server_name, user_name, passWord)

except tt.TintriRequestsException as tre:
    print_error(tre.__str__())
    sys.exit(1)
except tt.TintriApiException as tae:
    print_error(tae.__str__())
    sys.exit(1)
    
print("")

try:
    # Get List of Service Groups
    api = "/v310/servicegroup"
    results = tt.api_get(server_name, api, session_id)
    service_groups = results.json()
    
    service_group_exists = False

    # setup API for adding VMs to proper Service Group
    for item in service_groups["items"]:
        if item["name"] == service_group:
            service_group_exists = True
            target_sg = item["uuid"]["uuid"]
            break
    		
    if service_group_exists:
    	target_sg_api = "/v310/servicegroup/" + target_sg + "/members/static"
    	print("Service Group Found")
    else:
    	raise tt.TintriRequestsException("Specified service group not found.\nAre you sure you typed it in correctly?")
    
    (uuid_list, vms_found) = get_vm_uuids(vm_list)
    
    if len(vms_found) != len(vm_list):
        print_error("VMs found: " + str(len(vms_found)) + " != VMs read: " + str(len(vm_list)))
    	print_error("VMs in list:\n   " + ", ".join(vm_list))
    	print_error("VMs found:\n   " + ", ".join(vms_found))
    	raise tt.TintriRequestsException("The servers specified do not match what was returned")
    
    payload = {'typeId': 'com.tintri.api.rest.v310.dto.CollectionChangeRequest', \
               'objectIdsAdded': uuid_list
              }
    
    # Set the static members.
    tt.api_put(server_name, target_sg_api, payload, session_id)
    
except tt.TintriRequestsException as tre:
    print_error(tre.__str__())
    sys.exit(1)
except tt.TintriApiException as tae:
    print_error(tae.__str__())
    sys.exit(1)

tt.api_logout(server_name, session_id)

print("These VMs: " + ", ".join(vms_found) + ", were found and added to " + service_group)
