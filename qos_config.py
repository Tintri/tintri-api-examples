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
import json
import tintri_1_1 as tintri

"""
 This Python script configures QoS on the first 2 live VMs
 QoS configuration consists of mininum and maximum IOPs.

 Command usage: qos_config <server_name> <userName> <password> <min_iops> <max_iops>

"""

# For exhaustive messages on console, make it to True; otherwise keep it False
debug_mode = False

# Class to hold the VM name, UUID, and QOS information, min and max IOPs.
class VmQosInfo:
    def __init__(self, name, uuid, min_value, max_value):
        self.name = name
        self.uuid = uuid
        self.min_value = min_value
        self.max_value = max_value

    def get_name(self):
        return self.name

    def get_uuid(self):
        return self.uuid

    def get_min_value(self):
        return self.min_value

    def get_max_value(self):
        return self.max_value

    def set_min_value(self, new_value):
        self.min_value = new_value

    def set_max_value(self, new_value):
        self.max_value = new_value

    def __str__(self):
        return ("VM name: " + self.name + " UUID: " + self.uuid +
               " (" + str(self.min_value) + ", " + str(self.max_value) + ")")

# Helper print routines.
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
if len(sys.argv) < 6:
    print("\nSets the first 2 VMs QOS values\n")
    print("Usage: " + sys.argv[0] + " server_name user_name password min_value, max_value\n")
    sys.exit(-1)

server_name = sys.argv[1]
user_name = sys.argv[2]
password = sys.argv[3]
new_min_value = sys.argv[4]
new_max_value = sys.argv[5]

# Get the preferred version
r = tintri.api_version(server_name)
json_info = r.json()

print_info("API Version: " + json_info['preferredVersion'])

# Login to VMstore
session_id = tintri.api_login(server_name, user_name, password)

# Create filter to get the live VMs
q_filter = {'live': 'TRUE'}

# Get a list of live VMs
url = "/v310/vm"
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

vm_paginated_result = r.json()
num_vms = int(vm_paginated_result["filteredTotal"])
if num_vms == 0:
    print_error("No live VMs present")
    exit(77)

print_info(str(num_vms) + " live VMs present")

if num_vms < 2:
    print_error("Need at least 2 VMs")
    exit(77)

items = vm_paginated_result["items"]

# Create the first VM object.
vm1 = VmQosInfo(items[0]["vmware"]["name"],
                items[0]["uuid"]["uuid"],
                items[0]["qosConfig"]["minNormalizedIops"],
                items[0]["qosConfig"]["maxNormalizedIops"])
print_info("VM 1: " + str(vm1))

# Create the second VM object.
vm2 = VmQosInfo(items[1]["vmware"]["name"],
                items[1]["uuid"]["uuid"],
                items[1]["qosConfig"]["minNormalizedIops"],
                items[1]["qosConfig"]["maxNormalizedIops"])
print_info("VM 2: " + str(vm2))

# Create new QoS object with the fields to be changed
modify_qos_info = {'minNormalizedIops': int(new_min_value),
                   'maxNormalizedIops': int(new_max_value),
                   'typeId': items[0]["qosConfig"]["typeId"]
                  }
                  
# Create the MultipleSelectionRequest object
MS_Request = {'typeId': 'com.tintri.api.rest.v310.dto.MultipleSelectionRequest',
              'ids': [vm1.get_uuid(), vm2.get_uuid()],
              'newValue': modify_qos_info,
              'propertyNames': ["minNormalizedIops", "maxNormalizedIops"]
          }

print_info("Changing min and max QOS values to (" + str(new_min_value) + ", " + str(new_max_value) + ")")

# Update the min and max IOPs
modify_qos_url = "/v310/vm/qosConfig"
r = tintri.api_put(server_name, modify_qos_url, MS_Request, session_id)
print_debug("The JSON response of the get invoke to the server " +
            server_name + " is: " + r.text)

# if HTTP Response is not 204 then raise an exception
if r.status_code != 204:
    print_error("The HTTP response for the put invoke to the server " +
          server_name + " is not 200, but is: " + str(r.status_code))
    print_error("url = " + modify_qos_url)
    print_error("payload = " + str(MS_Request))
    print_error("response: " + r.text)
    tintri.api_logout(server_name, session_id)
    sys.exit(-10)


# Get VM 1 value to show that it changed.
vm1_url = "/v310/vm/" + vm1.get_uuid()
r = tintri.api_get(server_name, vm1_url, session_id)
print_debug("The JSON response of the get invoke to the server " +
            server_name + " is: " + r.text)

# if HTTP Response is not 200 then raise an exception
if r.status_code != 200:
    print_error("The HTTP response for the get invoke to the server " +
          server_name + " is not 200, but is: " + str(r.status_code))
    print_error("url = " + vm1_url)
    print_error("response: " + r.text)
    tintri.api_logout(server_name, session_id)
    sys.exit(-10)

vm1_info = r.json()

# Set the new values in the VM1 object
vm1.set_min_value(vm1_info["qosConfig"]["minNormalizedIops"])
vm1.set_max_value(vm1_info["qosConfig"]["maxNormalizedIops"])
print_info("VM 1: " + str(vm1))

# Get VM 2 value to show that it changed.
vm2_url = "/v310/vm/" + vm2.get_uuid()
r = tintri.api_get(server_name, vm2_url, session_id)
print_debug("The JSON response of the get invoke to the server " +
            server_name + " is: " + r.text)

# if HTTP Response is not 200 then raise an exception
if r.status_code != 200:
    print_error("The HTTP response for the get invoke to the server " +
          server_name + " is not 200, but is: " + str(r.status_code))
    print_error("url = " + vm2_url)
    print_error("response: " + r.text)
    tintri.api_logout(server_name, session_id)
    sys.exit(-10)

vm2_info = r.json()

# Set the new values in the VM2 object
vm2.set_min_value(vm2_info["qosConfig"]["minNormalizedIops"])
vm2.set_max_value(vm2_info["qosConfig"]["maxNormalizedIops"])
print_info("VM 2: " + str(vm2))

tintri.api_logout(server_name, session_id)

