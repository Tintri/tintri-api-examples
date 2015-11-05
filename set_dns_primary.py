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
 This scripts sets the primary DNS for a list of VMstores in a file.

 Command usage: set_dns_primary <file_name> <userName> <password> <new_dns_primary>

"""

# For exhaustive messages on console, make it to True; otherwise keep it False
debug_mode = False
APPLIANCE_URL = "/v310/appliance/default"


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

def print_dns_info(dns_info, description):
    print(description + dns_info['dnsPrimary'] + " (" + dns_info['dnsSecondary'] + ")")


# Return the DNS primary and secondary IP addresses.
def get_dns_info(server_name, session_id):
    url = APPLIANCE_URL + "/dns"
    
    # Make the get call
    r = tintri.api_get(server_name, url, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)
    
    # if HTTP Response is not 200 then raise an error
    if r.status_code != 200:
        message = "The HTTP response for the get invoke to the server is not 200."
        tintri.api_logout(server_name, session_id)
        raise tintri.TintriApiException(message, r.status_code, url, str(Request), r.text)
    
    appliance_dns = r.json()
    return appliance_dns


# Process each VMstore:
# 1. login
# 2. get the current DNS info
# 3. modify the DNS info
# 4. logout
#
# All API calls can raise exceptions and the function
# calling process_vmstore() is expected to handle it.

def process_vmstore(vmstore_name, user_name, password, new_dns_primary):

    server_name = vmstore_name

    # Get the server type
    r = tintri.api_version(server_name)
    json_info = r.json()
    if json_info['productName'] != "Tintri VMstore":
        this_error = "Server needs to be a VMstore"
        return this_error

    session_id = tintri.api_login(server_name, user_name, password)
        
    dns_info = get_dns_info(server_name, session_id)
    print_dns_info(dns_info, server_name + " current: ")
    
    new_dns_secondary = dns_info['dnsSecondary']
    
    # Create the ApplianceDns DTO.
    new_dns_info = \
        {'typeId': 'com.tintri.api.rest.v310.dto.domain.beans.hardware.ApplianceDns',
         'dnsPrimary': new_dns_primary,
         'dnsSecondary': new_dns_secondary
        }
    
    # Create the Appliance object wit the new ApplianceDns DTO.
    new_appliance = \
        {'typeId': 'com.tintri.api.rest.v310.dto.domain.Appliance',
         'dnsConfig': new_dns_info
        }
                 
    # Create the Request object with the Appliance DTO.
    Request = \
        {'typeId': 'com.tintri.api.rest.v310.dto.Request',
         'objectsWithNewValues': new_appliance,
         'propertiesToBeUpdated': ['dnsConfig']
        }
        
    url = APPLIANCE_URL
    r = tintri.api_put(server_name, url, Request, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)
        
    # if HTTP Response is not 204 then raise exception
    if r.status_code != 204:
        tintri.api_logout(server_name, session_id)
        message = "The HTTP response for put call to the server is not 204."
        raise tintri.TintriApiException(message, r.status_code, url, str(Request), r.text)
    
    dns_info = get_dns_info(server_name, session_id)
    print_dns_info(dns_info, server_name + " now: ")
    
    # All pau, log out
    tintri.api_logout(server_name, session_id)


# main
if len(sys.argv) < 5:
    print("\nSets allow complete snapshot flag\n")
    print("Usage: " + sys.argv[0] + " file_name user_name password dns_primary\n")
    sys.exit(-1)

file_name = sys.argv[1]
user_name = sys.argv[2]
password = sys.argv[3]
new_dns_primary = sys.argv[4]

print_info("file: " + file_name + "  DNS: " + new_dns_primary)

# Read the file with the VMstore names.
with open (file_name, "r") as in_file:
    vmstores = in_file.readlines()
print_debug("vmstores read: " + str(vmstores))

# create error file name and open error file
error_file_name = file_name + "_error"
error_file = open (error_file_name, "w")

count = 0
err_count = 0
for vmstore in vmstores:
    vmstore = vmstore[:-1]  # strip off linefeed

    try:
        status = process_vmstore(vmstore, user_name, password, new_dns_primary)
    except tintri.TintriRequestsException as tre:
        err_msg = "[ERROR] " + vmstore + ": " + tre.__str__() + "\n"
        error_file.write(err_msg)
        err_count += 1
    except tintri.TintriApiException as tae:
        err_msg = "[ERROR] " + vmstore + ": " + tae.__str__() + "\n"
        error_file.write(err_msg)
        err_count += 1
    count += 1

in_file.close()
error_file.close()

print_info("Processed " + str(count) + " vmstores with " + str(err_count) + " errors.")

