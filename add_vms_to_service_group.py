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
 This Python script adds VMs from a file that contains a VM name per line
 to a servcie group.

 Command usage:
 qos_on_service_group.py server_name user_name password service_group file_name
 Where:"
     server_name   - name of a TGC server
     user_name     - user name used to login into the TGC server
     password      - password for the user
     service_group = The service group to add VMs to
     file_name     - file name of VMs to be placed in the service group

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


# Return the service group ID for the service group
def get_service_group(server_name, session_id, service_group):

    # Get a list of service groups
    url = "/v310/servicegroup"
    r = tintri.api_get(server_name, url, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)
    
    sg_paginated_result = r.json()
    num_sgs = int(sg_paginated_result["absoluteTotal"])
    if num_sgs == 0:
        raise tintri.TintriRequestsException("No Service Groups present")
    
    print_debug(str(num_sgs) + " Service Groups present")
    
    # Initialze the member list
    sg_uuid = ""
    found = False
    
    # Look for service group that matches the input name
    items = sg_paginated_result["items"]
    count = 1
    for sg in items:
        sg_name = sg["name"]
        sg_uuid = sg["uuid"]["uuid"]
        sg_member_count = sg["memberCount"]
        print_debug(str(count) + ": " + sg_name + "(" + str(sg_member_count) + "): " + sg_uuid)
        if sg_name == service_group: 
            found = True
            break
        count += 1
    
    if not found:
        raise tintri.TintriRequestsException("Service Group " + service_group + " not found.")
    
    return sg_uuid


# Return a dictionary of VMs key by VM name.
def get_vms(server_name, session_id):

    vms = {}
    
    # Get a list of VMs, but return a page size at a time
    get_vm_url = "/v310/vm"
    count = 1
    page_size = 100
    vm_paginated_result = {'next' : "offset=0&limit=" + str(page_size)}
    
    print_info("Collecting VMs from TGC.")

    # While there are more Vms, go get them
    while 'next' in vm_paginated_result:
        url = get_vm_url + "?" + vm_paginated_result['next']
        print_debug("Next GET VM URL: " + str(count) + ": " + url)
    
        r = tintri.api_get(server_name, url, session_id)
        print_debug("The JSON response of the get invoke to the server " +
                    server_name + " is: " + r.text)
        
        # For each VM in the page, print the VM name and UUID.
        vm_paginated_result = r.json()
    
        # Check for the first time through the loop and
        # print the total number of VMs.
        if count == 1:
            num_vms = vm_paginated_result["filteredTotal"]
            if num_vms == 0:
                raise tintri.TintriRequestsException("No VMs present")
    
            print_debug(str(num_vms) + " VMs present")
    
        items = vm_paginated_result["items"]
        for vm in items:
            vm_name = vm["vmware"]["name"]
            vm_uuid = vm["uuid"]["uuid"]
            print_debug(str(count) + ": " + vm_name + ", " + vm_uuid)
            count += 1
            vms[vm_name] = vm_uuid
        print_info("Collected " + str(count) + " VMs.")

    print_info(str(count) + "VMs collected from TGC.")
    return vms


# Return a list of VMs read from a file
def read_vms_from_file(file_name):
    vms_from_file = []

    print("Opening file " + file_name + ".")
    with open(file_name, 'r') as f:
        vms = f.readlines()

    # Go through the VMs and string linefeed.
    # Skip lines that start with '#'.
    for vm in vms:
        if (vm[0] == '#'):
            continue

        # Strip linefeed and possible carriage return
        temp_vm = vm.rstrip('\n')
        temp_vm = temp_vm.rstrip('\r')

        vms_from_file.append(temp_vm)

    f.close()

    return vms_from_file


# main
if len(sys.argv) < 6:
    print("\nAdds VMs from a file to a service group.")
    print("The file format is one VM name per line.\n")
    print("Usage: " + sys.argv[0] + " server_name user_name password file_name\n")
    print("Where:")
    print("    server_name   - name of a TGC server")
    print("    user_name     - user name used to login into the TGC and VMstore servers")
    print("    password      - password for the TGC and VMstore users")
    print("    service_group - service group to add VMs to")
    print("    file_name     - the file name of VMs to be placed in the service group")
    sys.exit(-1)

server_name = sys.argv[1]
user_name = sys.argv[2]
password = sys.argv[3]
service_group = sys.argv[4]
file_name = sys.argv[5]

try:
    # Get the preferred version
    r = tintri.api_version(server_name)
    json_info = r.json()
    preferred_version = json_info['preferredVersion']
    product_name = json_info['productName']
    
    # Check for correct product
    if product_name != "Tintri Global Center":
        print_error("Tintri server needs to be Tintri Global Center, not a " + product_name)
        sys.exit(-8)
    
    # Check for the correct version
    versions = preferred_version.split(".")
    major_version = versions[0]
    minor_version = int(versions[1])
    if major_version != "v310":
        raise TintriRequestsException("Incorrect major version: " + major_version + ".  Should be v310.")
    if minor_version < 31:
        raise TintriRequestsException("Incorrect minor Version: " + minor_version + ".  Should be 31 or greater")

    # Login to TGC
    session_id = tintri.api_login(server_name, user_name, password)

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    exit(-1)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    exit(-2)

try:
    sg_uuid = get_service_group(server_name, session_id, service_group)
    print("Service group '" + service_group + "' exists.")
    
    # Get a dictionary of VMs that are associated with the TGC
    vms = get_vms(server_name, session_id)

    # Get a list of VMs to be placed into the service group
    vms_from_file = read_vms_from_file(file_name)

    # Create the change requst and URL
    members_to_add = {'typeId': 'com.tintri.api.rest.v310.dto.CollectionChangeRequest',
                      'objectIdsAdded': ""
                     }
    add_members_url = "/v310/servicegroup/" + sg_uuid + "/members/static"

    # For each vm from the file, validate it, and add it to
    # the service group.  If API error, stop.
    vm_count = 0
    for vm in vms_from_file:
        if (not(vm in vms)):
            print_info(vm + " not in TGC VM list.")
            continue

        members_to_add['objectIdsAdded'] = vms[vm]
        
        # Add VM to service group
        r = tintri.api_put(server_name, add_members_url, members_to_add, session_id) 
        if (r.status_code != 204):
            msg = "The HTTP response for the put invoke to the server " + \
                  server_name + " is not 204, but is: " + str(r.status_code) + "."
            raise tintri.TintriApiException(msg, r.status_code, add_members_url, str(members_to_add), r.text)
        print ("Added vm: " + vm)
        vm_count += 1
        
    print(str(vm_count) + " VMs added to service group '" + service_group + "'.")

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    tintri.api_logout(server_name, session_id)
    exit(-5)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    tintri.api_logout(server_name, session_id)
    exit(-6)

# All pau, log out
tintri.api_logout(server_name, session_id)

