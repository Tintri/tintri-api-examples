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
import time
import datetime
import tintri_1_1 as tintri

"""
 This scripts sets the maintenance mode for the VMstore

 Command usage: set_dns_primary <server> <userName> <password> 

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


def my_timezone():
    tz_hours = time.timezone / -3600
    tz_minutes = time.timezone % 3600
    return "{0:0=+3d}:{1:0=2d}".format(tz_hours, tz_minutes)


# Return the DNS primary and secondary IP addresses.
def get_maintenance_mode(server_name, session_id):
    url = APPLIANCE_URL + "/maintenanceMode"
    
    # Make the get call
    r = tintri.api_get(server_name, url, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)
    
    # if HTTP Response is not 200 then raise an error
    if r.status_code != 200:
        message = "The HTTP response for the get invoke to the server is not 200."
        raise tintri.TintriApiException(message, r.status_code, url, "no request", r.text)
    
    maintenance_mode = r.json()
    return maintenance_mode


# Print the maintenance mode information.
# If maintenance mode enabled, print the start and end time.
def print_maintenance_mode(maintenance_mode):
    is_enabled = maintenance_mode["isEnabled"]
    print("Current Maintenance Mode: " + str(is_enabled))
    if (is_enabled):
        print("From: " + maintenance_mode["startTime"])
        print("To  : " + maintenance_mode["endTime"])
    print""


# Nots the current maintenance mode and sets it interactively
def set_maintenance_mode(server_name, session_id, maint_mode):
    
    is_enabled = maint_mode["isEnabled"]
    new_is_enabled = not is_enabled
    pline = "Set maintenance mode from " + str(is_enabled) + " to " + str(new_is_enabled) + "? (y/n) "
    line = raw_input(pline)
    if (line != "y"):
        return

    # Get now and 6 hours from now.  This is what the GUI sets.
    now = datetime.datetime.now()
    add_6 = now + datetime.timedelta(hours=6)
    time_zone = my_timezone()
    now_str = now.isoformat() + time_zone
    add_6_str = add_6.isoformat() + time_zone
    print_debug("Start time: " + now_str)
    print_debug("End time:   " +add_6_str)

    if (new_is_enabled):
        # Create the maintenance mode DTO for enabling.
        new_maint_mode_info = \
            {"typeId": "com.tintri.api.rest.v310.dto.domain.beans.hardware.ApplianceMaintenanceMode",
             "endTime"   : add_6_str,
             "isEnabled" : new_is_enabled,
             "startTime" : now_str
            }
    else:
        # Create the maintenance mode DTO for disabling.
        new_maint_mode_info = \
            {"typeId": "com.tintri.api.rest.v310.dto.domain.beans.hardware.ApplianceMaintenanceMode",
             "isEnabled" : new_is_enabled,
            }
        
    # Create the Appliance object wit the new ApplianceDns DTO.
    new_appliance = \
        {"typeId": "com.tintri.api.rest.v310.dto.domain.Appliance",
         "maintenanceMode": new_maint_mode_info
        }
                 
    # Create the Request object with the Appliance DTO.
    Request = \
        {"typeId": "com.tintri.api.rest.v310.dto.Request",
         "objectsWithNewValues": [new_appliance],
         "propertiesToBeUpdated": ["maintenanceMode"]
        }
        
    print_debug("Request:\n" + str(Request))

    # Invoke the appliance API to set the maintenance mode.
    url = APPLIANCE_URL
    r = tintri.api_put(server_name, url, Request, session_id)
    print_debug("The JSON response of the put invoke to the server " +
                server_name + " is: " + r.text)
        
    # if HTTP Response is not 204 then raise exception
    if r.status_code != 204:
        message = "The HTTP response for put call to the server is not 204."
        raise tintri.TintriApiException(message, r.status_code, url, str(Request), r.text)
    

# main
if len(sys.argv) < 4:
    print("\nSets maintenance mode on the VMstore\n")
    print("Usage: " + sys.argv[0] + " server user_name password\n")
    sys.exit(-1)

server_name = sys.argv[1]
user_name = sys.argv[2]
password = sys.argv[3]

# Get version and login
try:
    # Get the preferred version
    r = tintri.api_version(server_name)
    json_info = r.json()
    product_name = json_info["productName"]
    
    if (product_name != "Tintri VMstore"):
        raise tintri.TintriRequestException("Server needs to be a VMstore, not a " + product_name)

    print_info("API Version: " + json_info["preferredVersion"])

    # Login to VMstore
    session_id = tintri.api_login(server_name, user_name, password)

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    sys.exit(-10)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    sys.exit(-11)
    
try:
    maintenance_mode = get_maintenance_mode(server_name, session_id)
    print ""
    print_maintenance_mode(maintenance_mode)

    set_maintenance_mode(server_name, session_id, maintenance_mode)

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    tintri.api_logout(server_name, session_id)
    sys.exit(-20)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    tintri.api_logout(server_name, session_id)
    sys.exit(-21)
    
    # All pau, log out
    tintri.api_logout(server_name, session_id)

