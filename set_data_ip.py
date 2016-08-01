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
import argparse
import tintri_1_1 as tintri

"""
 This scripts sets data IP on a VMstore. It adds, deletes, or display

 Command usage: set_data_ip <vmstore> <userName> <password> <new_data_ip>

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


def dump_ip_config(ip_config):
    for key, value in ip_config.iteritems():
        print(key + ": " + str(value))


# Print IP configuration from the appliance.
def print_ip_configs(ip_configs, description):
    print("\n" + description + ":")
    for ip_config in ip_configs:
        print("   " + ip_config['ip'] + ": " + ip_config['serviceType'] + \
              ": " + ip_config['networkBond'] + ": " + ip_config['vlanId'])

        #dump_ip_config(ip_config)


# Return the IP addresses.
def get_ip_configs(server_name, session_id):
    url = APPLIANCE_URL + "/ips"
    
    try:
        # Make the get call
        r = tintri.api_get(server_name, url, session_id)
        print_debug("The JSON response of the get invoke to the server " +
                    server_name + " is: " + r.text)
    
    except tintri.TintriRequestsException as tre:
        message = "HTTP error for the get IP addresses invoke to the server."
        raise tintri.TintriApiException(message, r.status_code, url, str(Request), r.text)
    except tintri.TintriApiException as tae:
        message = "The HTTP response for the get IP addresses invoke to the server is not 200."
        raise tintri.TintriApiException(message, r.status_code, url, str(Request), r.text)

    ip_configs = r.json()
    return ip_configs


# Add a data IP to the list of current IPs and return new list.
def add_data_ip(ip_configs, new_data_ip):

    new_ip_configs = []
    
    # Find a data IP config to copy and copy only the data IP configs.
    for ip_config in ip_configs:
        if (ip_config['ip'] == new_data_ip):
            message = new_data_ip + " already configured."
            raise tintri.TintriRequestsException(message)

        if (ip_config['serviceType'] == "data"):
            ip_config_save = ip_config
            new_ip_configs.append(ip_config)

    if (not ip_config_save):
        message = "Data IP conifg does not exist."
        raise tintri.TintriRequestsException(message)

    data_ip_config = ip_config_save.copy()
    
    # Modify the save copy for our purposes.
    data_ip_config['ip'] = new_data_ip
    data_ip_config['vlanId'] = "untagged"  # For example only.
    
    new_ip_configs.append(data_ip_config)
    return new_ip_configs

    
# Delete a data IP from the list of current IPs and return new list.
def del_data_ip(ip_configs, data_ip_to_del):

    new_ip_configs = []
    
    # Append IP config if the data IP doesn't match.
    for ip_config in ip_configs:
        if (ip_config['serviceType'] == "data"):
            if (ip_config['ip'] != data_ip_to_del):
                new_ip_configs.append(ip_config)
    
    return new_ip_configs


# Set the data IP with new IP configuration.
def update_data_ip(server_name, session_id, new_ip_configs):

    # Create the Appliance object with the new configIps DTO.
    new_appliance = \
        {'typeId': 'com.tintri.api.rest.v310.dto.domain.Appliance',
         'configIps': new_ip_configs
        }
                 
    # Create the Request object with the Appliance DTO.
    Request = \
        {'typeId': 'com.tintri.api.rest.v310.dto.Request',
         'objectsWithNewValues': new_appliance,
         'propertiesToBeUpdated': ['configIps']
        }
        
    # Update the VMstore wit the new data IP configuration.
    url = APPLIANCE_URL
    r = tintri.api_put(server_name, url, Request, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)
        
    # if HTTP Response is not 204 then raise exception
    if r.status_code != 204:
        message = "The HTTP response for put call to the server is not 204."
        raise tintri.TintriApiException(message, r.status_code, url, str(Request), r.text)
    

# main
delete_ip = False
add_ip = False

parser = argparse.ArgumentParser(description="Optionally adds or deletes a data IP on a VMstore")

parser.add_argument("server_name", help="VMstore server name")
parser.add_argument("user_name", help="VMstore user name")
parser.add_argument("password", help="User name password")
parser.add_argument("--add", "-a",
                    nargs=1,
                    help="Add the specifed IP to the data IP configuration.")
parser.add_argument("--delete", "-d",
                    nargs=1,
                    help="Delete the specifed IP from the data IP configuration.")

args = parser.parse_args()

# Collect the required parameters.
server_name = args.server_name
user_name = args.user_name
password = args.password

# Collect the optional parameters.
if args.add != None:
    new_data_ip = args.add[0]
    add_ip = True
    print_info("Adding " + new_data_ip + " to " + server_name)

if args.delete != None:
    new_data_ip = args.delete[0]
    delete_ip = True
    print_info("Deleting " + new_data_ip + " from " + server_name)

# Get the server type and login
try:
    r = tintri.api_version(server_name)
    json_info = r.json()
    if json_info['productName'] != "Tintri VMstore":
        message = "Server needs to be a VMstore"
        raise tintri.TintriRequestsException(message)

    session_id = tintri.api_login(server_name, user_name, password)

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    exit(2)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    exit(3)

# Execute
try:
    ip_configs = get_ip_configs(server_name, session_id)
    print_ip_configs(ip_configs, "Current")
    
    if add_ip or delete_ip:
        if add_ip:
            new_ip_configs = add_data_ip(ip_configs, new_data_ip)
        if delete_ip:
            new_ip_configs = del_data_ip(ip_configs, new_data_ip)

        update_data_ip(server_name, session_id, new_ip_configs)
    
        # Display the changes
        ip_configs = get_ip_configs(server_name, session_id)
        print_ip_configs(ip_configs, "New")

except tintri.TintriRequestsException as tre:
    print_error(server_name + ": " + tre.__str__())
except tintri.TintriApiException as tae:
    print_error(server_name + ": " + tae.__str__())

# All pau, log out
tintri.api_logout(server_name, session_id)
print ""

