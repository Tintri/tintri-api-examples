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
 This Python script sets the QoS of the VMs in the first TGC service group with
 more than 2 VMs. 

 Command usage:
 qos_on_service_group.py server_name user_name password min_value max_value
 Where:"
     server_name - name of a TGC server
     user_name   - user name used to login into the TGC server
     password    - password for the user
     min_value   - the QoS minimum value for the VM
     max_value   - the QoS maximum value for the VM

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


# Sets the Minimum and maximum QoS values on a TGC service group.
def set_qos(server_name, session_id, sg_uuid, new_min_value, new_max_value):
    # Create new QoS object with the fields to be changed
    modify_qos_info = {'minNormalizedIops': int(new_min_value),
                       'maxNormalizedIops': int(new_max_value),
                       'typeId': 'com.tintri.api.rest.v310.dto.domain.beans.vm.VirtualMachineQoSConfig'
                      }
                          
    # Configure the QoS for the service group
    modify_qos_url = "/v310/servicegroup/" + sg_uuid + "/qosConfig"
    r = tintri.api_put(server_name, modify_qos_url, modify_qos_info, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)
    
    # if HTTP Response is not 204 then raise an exception
    if r.status_code != 204:
        print_error("The HTTP response for the put invoke to the server " +
              server_name + " is not 204, but is: " + str(r.status_code))
        print_error("url = " + modify_qos_url)
        print_error("payload = " + str(modify_qos_info))
        print_error("response: " + r.text)
        tintri.api_logout(server_name, session_id)
        print_info("Error log off " + server_name)
        sys.exit(-20)
    
    # Apply the QoS values that were for the service group that
    # were configured above.
    apply_qos_url = "/v310/servicegroup/" + sg_uuid + "/qos"
    r = tintri.api_post(server_name, apply_qos_url, None, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)
    
    # if HTTP Response is not 204 then raise an exception
    if r.status_code != 204:
        print_error("The HTTP response for the post invoke to the server " +
              server_name + " is not 204, but is: " + str(r.status_code))
        print_error("url = " + modify_qos_url)
        print_error("payload = None")
        print_error("response: " + r.text)
        tintri.api_logout(server_name, session_id)
        print_info("Error log off " + server_name)
        sys.exit(-21)


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
    print_error("Incorrect major version: " + major_version + ".  Should be v310.")
    sys.exit(-8)
if minor_version < 31:
    print_error("Incorrect minor Version: " + minor_version + ".  Should be 31 or greater")
    sys.exit(-8)

# Login to TGC
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
num_sgs = int(sg_paginated_result["absoluteTotal"])
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
    print_error("No service groups matching the criertia.")
    tintri.api_logout(server_name, session_id)
    sys.exit(-15)

set_qos(server_name, session_id, sg_uuid, new_min_value, new_max_value)

# All pau, log out
tintri.api_logout(server_name, session_id)

