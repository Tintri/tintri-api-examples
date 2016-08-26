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
import argparse
import json
import tintri_1_1 as tintri

"""
 This Python script sets VM affinity for VM migration rules.

"""

# For exhaustive messages on console, make it to True; otherwise keep it False
debug_mode = False
beans = "com.tintri.api.rest.v310.dto.domain.beans."
page_size = 100


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


# Format JSON into something readable.
def format_json(json_to_format):
    return json.dumps(json_to_format, sort_keys=True, indent=4, separators=(',', ': '))


# Get a service group UUID by name.
def get_sg_by_name(server_name, session_id, service_group):
    url = "/v310/servicegroup"
    r = tintri.api_get(server_name, url, session_id)
    print_debug("The JSON response of the service group get invoke to the server " +
                server_name + " is: " + r.text)

    sg_paginated_result = r.json()
    num_sgs = int(sg_paginated_result["absoluteTotal"])
    if num_sgs == 0:
        raise tintri.TintriRequestsException("No service groups present")

    # Look for a qualifying service group
    items = sg_paginated_result["items"]
    for sg in items:
        if (sg["name"] == service_group):
            return sg["uuid"]["uuid"]

    return ""
    

# Return a list of VM UUIDs from a list of VM names
def get_vms_in_list(server_name, session_id, vms):
    vm_uuids = []
    vm_name_to_uuid = {}

    # Get a list of VMs, but return a page size at a time
    get_vm_url = "/v310/vm"
    vm_paginated_result = {'next' : "offset=0&limit=" + str(page_size)}
    vm_filter = {"includeFields"   : ["uuid", "vmware"] }
    
    # While there are more VMs, go get them, and build a dictionary
    # of name to UUID.
    while 'next' in vm_paginated_result:
        url = get_vm_url + "?" + vm_paginated_result['next']
    
        r = tintri.api_get_query(server_name, url, vm_filter, session_id)
        print_debug("The JSON response of the VM get invoke to the server " +
                    server_name + " is: " + r.text)
        
        # For each VM in the page, print the VM name and UUID.
        vm_paginated_result = r.json()
        print_debug("VMs:\n" + format_json(vm_paginated_result))
    
        # Build a dictionary
        items = vm_paginated_result["items"]
        for vm in items:
            vm_name_to_uuid[vm["vmware"]["name"]] = vm["uuid"]["uuid"]

    for vm in vms:
        if vm in vm_name_to_uuid:
            vm_uuids.append(vm_name_to_uuid[vm])
        else:
            print_info("VM, " + vm + ", is unknown to TGC, " + server_name)

    return vm_uuids


# Return VM items constrained by a filter.
def get_vms(server_name, session_id, vm_filter):
    vm_uuids = []

    # Get a list of VMs, but return a page size at a time
    get_vm_url = "/v310/vm"
    vm_paginated_result = {'next' : "offset=0&limit=" + str(page_size)}
    
    # While there are more VMs, go get them, and build a dictionary
    # of name to UUID.
    while 'next' in vm_paginated_result:
        url = get_vm_url + "?" + vm_paginated_result['next']
    
        r = tintri.api_get_query(server_name, url, vm_filter, session_id)
        print_debug("The JSON response of the VM get invoke to the server " +
                    server_name + " is: " + r.text)
        
        # For each VM in the page, print the VM name and UUID.
        vm_paginated_result = r.json()
        print_debug("VMs:\n" + format_json(vm_paginated_result))
    
        # Get the VMs
        items = vm_paginated_result["items"]
        for vm in items:
            vm_uuids.append(vm["uuid"]["uuid"])

    return vm_uuids


# Return a list of VM UUIDs based on a service group name.
def get_vms_by_sg(server_name, session_id, sg_uuid):
    vm_uuids = []

    # Get a list of VMs, but return a page size at a time
    vm_filter = {"includeFields"   : ["uuid", "vmware"],
                 "serviceGroupIds" : sg_uuid
                }
    
    vm_uuids = get_vms(server_name, session_id, vm_filter)

    return vm_uuids


# Return a list of VM UUIDs base of a string contained in VMs.
def get_vms_by_name(server_name, session_id, name):

    vm_filter = {"includeFields" : ["uuid", "vmware"],
                 "name" : name
                }
    
    vm_uuids = get_vms(server_name, session_id, vm_filter)

    return vm_uuids

# A helper function  that sets the VM affinity rule for migration recommendations.
def set_vm_affinity(server_name, session_id, vm_uuids, affinity_rule):
    url = "/v310/vm/"

    for vm_uuid in vm_uuids:
        rule_url = url + vm_uuid + "/affinity"

        r = tintri.api_put(server_name, rule_url, affinity_rule, session_id)
        if r.status_code != 204:
            tintri.api_logout(server_name, session_id)
            message = "The HTTP response for put affinity rule to the server is not 204."
            raise tintri.TintriApiException(message, r.status_code,
                                            rule_url, str(affinity_rule), r.text)
        sys.stdout.write(".")
    print("")


# Set the VM affinity rule to never for a list of VMs.
def set_vm_affinity_never(server_name, session_id, vm_uuids):
    print("Setting " + str(len(vm_uuids)) + " VMs to never migrate")

    affinity_rule = \
        {"typeId" : beans + "vm.VirtualMachineAffinityRule",
         "ruleType" : "NEVER"
        }

    set_vm_affinity(server_name, session_id, vm_uuids, affinity_rule)


# Clear the VM affinity rule for a list of VMs
def clear_vm_affinity(server_name, session_id, vm_uuids):
    print("Clearing " + str(len(vm_uuids)) + " VMs affinity rules")

    affinity_rule = \
        {"typeId" : beans + "vm.VirtualMachineAffinityRule",
        }

    set_vm_affinity(server_name, session_id, vm_uuids, affinity_rule)


# main

# Initialize some variables.
service_group = ""
vm_contains_name = ""
vms = []
vm_uuids = []
affinity = "never"

# Forge the command line argument parser.
parser = argparse.ArgumentParser(description="Set recommendation VM migration rule")

parser.add_argument("server_name", help="TGC server name")
parser.add_argument("user_name", help="TGC user name")
parser.add_argument("password", help="User name password")
parser.add_argument("--sg", help="server group name that contains VMs")
parser.add_argument("--vms", nargs='+', help="a list of VMs")
parser.add_argument("--name", help="matches VMs that contain name")
parser.add_argument("--affinity", choices=["never", "clear"],
                     help="affinity to set. Default is 'never'")
        

args = parser.parse_args()
to_do = False

# Check for a service group name.
if args.sg != None:
    service_group = args.sg
    to_do = True
    print_debug("service group: " + args.sg)

# Check for a list of VMs. There are 2 use cases:
# a comma separated list with no blanks or a list with blanks.
if args.vms != None:
    to_do = True
    if ',' in args.vms[0]:
        vms = args.vms[0].split(",") 
    else:
        vms = args.vms
    if debug_mode:
        print("VMs: ")
        count = 1
        for vm in vms:
            print("  " + str(count) + ": " + vm)
            count += 1

# Check for a string that is contained in VMs.
if args.name != None:
    vm_contains_name = args.name
    to_do = True

# If nothing to do, then exit.
if (not to_do):
    print_error("No VMs specified")
    sys.exit(1)

# Get the rule affinity
if args.affinity != None:
    affinity = args.affinity

# Collect the required parameters.
server_name = args.server_name
user_name = args.user_name
password = args.password

# Get the product name.
try:
    r = tintri.api_version(server_name)
    json_info = r.json()
    preferred_version = json_info['preferredVersion']
    product_name = json_info['productName']
    if json_info['productName'] != "Tintri Global Center":
        raise tintri.TintriRequestsException("server needs to be a TGC.")

    versions = preferred_version.split(".")
    major_version = versions[0]
    minor_version = int(versions[1])
    if major_version != "v310":
        raise tintri.TintriRequestsException("Incorrect major version: " + major_version + ".  Should be v310.")
    if minor_version < 51:
        raise tintri.TintriRequestsException("Incorrect minor Version: " + minor_version + ".  Should be 51 or greater")

    # Login to Tintri server
    session_id = tintri.api_login(server_name, user_name, password)

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    sys.exit(2)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    sys.exit(3)
    
# Let's get to work.
try:
    if (len(vms) > 0):
        print("Collecting VMs from list")
        vm_uuids += get_vms_in_list(server_name, session_id, vms)

    if (service_group != ""):
        print("Collecting VMs from service group")
        sg_uuid = get_sg_by_name(server_name, session_id, service_group)
        if (sg_uuid == ""):
            raise tintri.TintriRequestsException("Can't find service group " + service_group)

        vm_uuids += get_vms_by_sg(server_name, session_id, sg_uuid)

    if (vm_contains_name != ""):
        print("Collecting VMs from name")
        vm_uuids += get_vms_by_name(server_name, session_id, vm_contains_name)

    if (len(vm_uuids) == 0):
        raise tintri.TintriRequestsException("No VMs to set rules")

    if debug_mode:
        count = 1
        for uuid in vm_uuids:
            print(str(count) + ": " + uuid)
            count += 1

    # Process according to affinity
    if (affinity == "never"):
        set_vm_affinity_never(server_name, session_id, vm_uuids)

    elif (affinity == "clear"):
        clear_vm_affinity(server_name, session_id, vm_uuids)

    else:
        raise tintri.TintriRequestsException("Bad affinity rule: " + affinity)


except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    sys.exit(4)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    sys.exit(5)

# All pau, log out
tintri.api_logout(server_name, session_id)

