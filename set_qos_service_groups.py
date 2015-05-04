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
import tintri

"""
 This Python script sets the QoS of the VMs in the first TGC service group with
 more than 2 VMs.  The script first invokes the service group API on the TGC,
 then for each VM, the script invokes config QoS for each VMstore.

 This script assumes Tintri Global Center and VMstores have same user names
 and passwords.
     
 Command usage:
 set_qos_service_group.py server_name user_name password min_value max_value
 Where:"
     server_name - name of a TGC server
     user_name   - user name used to login into the TGC server
     password    - password for the user
     min_value   - the QoS minimum value for the VM
     max_value   - the QoS maximum value for the VM

"""

# Holds the VM information.
class VmInfo:
    def __init__(self, name, uuid, vmstore):
        self.name = name
        self.uuid = uuid
        self.vmstore = vmstore

    def __str__(self):
        return ("VM name: " + self.name + " UUID: " + self.uuid +
               " (" + self.vmstore + ")")


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


# Return a list of VmInfo obects that are in the specified service group.
def get_sg_members(server_name, session_id, sg_uuid):
    sg_members = []

    # Create filter to obtain live VMs and VMs that belong in specified
    # the service group.
    sg_filter = {'live': 'TRUE',
                 'serviceGroupIds' : sg_uuid}

    url = "/v310/vm"

    r = tintri.api_get_query(server_name, url, sg_filter, session_id)
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
    
    member_paginated_result = r.json()
    num_members = int(member_paginated_result["filteredTotal"])
    if num_members == 0:
        print_debug("No Service Groups members present")
        return sg_members
    
    print_debug(str(num_members) + " Service Group Members present")
    
    # For each live VM, create a VM info object
    items = member_paginated_result["items"]
    for vm in items:
        if not vm["isLive"]:
            continue
        member_vm = vm["vmware"]["name"]
        member_vmstore = vm["vmstoreName"]
        member_vm_uuid = vm["uuid"]["uuid"]
        print_debug("   " + member_vm + " (" + member_vmstore + ")")

        vm_info = VmInfo(member_vm, member_vm_uuid, member_vmstore)
        sg_members.append(vm_info)

    return sg_members


# Sets the min/max QoS values from a list of VM UUIDs.
# Returns "OK" or "Error".
def set_qos(server_name, user_name, password, vm_uuids, new_min_value, new_max_value):

    # Get the preferred version
    r = tintri.api_get(server_name, '/info')
    json_info = r.json()
    preferred_version = json_info['preferredVersion']
    
    # Verify the correct major and minor versions.
    versions = preferred_version.split(".")
    major_version = versions[0]
    minor_version = int(versions[1])
    if major_version != "v310":
        print_error("Incorrect major version: " + major_version + ".  Should be v310.")
        return "Error"
    if minor_version < 21:
        print_error("Incorrect minor Version: " + str(minor_version) + ".  Should be 21 or greater")
        return "Error"

    # Login into the appropriate VMstore
    session_id = tintri.api_login(server_name, user_name, password)
    if session_id is None:
        return "Error"
    print_info("Logged onto " + server_name)

    # Create new QoS object with the fields to be changed
    modify_qos_info = {'minNormalizedIops': int(new_min_value),
                       'maxNormalizedIops': int(new_max_value),
                       'typeId': 'com.tintri.api.rest.v310.dto.domain.beans.vm.VirtualMachineQoSConfig'
                      }
                      
    # Create the MultipleSelectionRequest object
    MS_Request = {'typeId': 'com.tintri.api.rest.v310.dto.MultipleSelectionRequest',
                  'ids': vm_uuids,
                  'newValue': modify_qos_info,
                  'propertyNames': ["minNormalizedIops", "maxNormalizedIops"]
                 }
    
    print_debug("Changing min and max QOS values to (" + str(new_min_value) + ", " + str(new_max_value) + ")")
    
    # Update the min and max QoS IOPs
    modify_qos_url = "/v310/vm/qosConfig"
    r = tintri.api_put(server_name, modify_qos_url, MS_Request, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)
    
    # if HTTP Response is not 204 then raise an exception
    if r.status_code != 204:
        print_error("The HTTP response for the put invoke to the server " +
              server_name + " is not 204, but is: " + str(r.status_code))
        print_error("url = " + modify_qos_url)
        print_error("payload = " + str(MS_Request))
        print_error("response: " + r.text)
        tintri.api_logout(server_name, session_id)
        print_info("Error log off " + server_name)
        return "Error"

    tintri.api_logout(server_name, session_id)
    print_info("Sucesss log off " + server_name)
    return "OK"


# main
if len(sys.argv) < 6:
    print("\nsets the QoS of the VMs in a TGC service group with more than 2 VMs.\n")
    print("Usage: " + sys.argv[0] + " server_name user_name password min_value max_value\n")
    print("Where:")
    print("    server_name - name of a TGC server")
    print("    user_name   - user name used to login into the TGC and VMstore servers")
    print("    password    - password for the TGC and VMstore users")
    print("    min_value   - the QoS minimum value for the VM")
    print("    max_value   - the QoS maximum value for the VM")
    sys.exit(-1)

server_name = sys.argv[1]
user_name = sys.argv[2]
password = sys.argv[3]
new_min_value = sys.argv[4]
new_max_value = sys.argv[5]

# Could make this an input parameter
# Get the preferred version
r = tintri.api_get(server_name, '/info')
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
    print_error("Incorrect major version: " + major_version + ".  Should be v310.")
    sys.exit(-8)
if minor_version < 21:
    print_error("Incorrect minor Version: " + minor_version + ".  Should be 21 or greater")
    sys.exit(-8)

# Login to VMstore
session_id = tintri.api_login(server_name, user_name, password)
if session_id is None:
    sys.exit(-7)

# Get a list of service groups
url = "/v310/servicegroup"
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

sg_paginated_result = r.json()
num_sgs = int(sg_paginated_result["filteredTotal"])
if num_sgs == 0:
    print_error("No Service Groups present")
    tintri.api_logout(server_name, session_id)
    exit(88)

print_info(str(num_sgs) + " Service Groups present")

# Initialze the member list
sg_uuid = ""
found = False

# Look for a qualifying service group
items = sg_paginated_result["items"]
count = 1
for sg in items:
    sg_name = sg["name"]
    sg_uuid = sg["uuid"]["uuid"]
    sg_member_count = sg["memberCount"]
    print_info(str(count) + ": " + sg_name + "(" + str(sg_member_count) + "): " + sg_uuid)
    if sg_member_count >= 2: 
        found = True
        break

    count += 1

if not found:
    print_error("No service groups matching the crieria.")
    tintri.api_logout(server_name, session_id)
    sys.exit(-15)

# Get the VMs in the service group
sg_members = get_sg_members(server_name, session_id, sg_uuid)

# Set the QoS for each VM member in the service group
count = 1
for vm_member in sg_members:
    vms = []
    print(str(count) + ": " + vm_member.name + " on " + vm_member.vmstore)
    vms.append(vm_member.uuid)
    status = set_qos(vm_member.vmstore, user_name, password,
                     vms, new_min_value, new_max_value)
    if status != "OK":
        break
    count += 1

# All pau, log out
tintri.api_logout(server_name, session_id)

