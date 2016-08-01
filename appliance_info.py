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
 This Python script prints server information.

 Command usage: get_server_info <server_name> <userName> <password>

 Replaces appliance_info.py

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


# main
if len(sys.argv) < 4:
    print("\nPrints server information\n")
    print("Usage: " + sys.argv[0] + " server_name user_name password\n")
    sys.exit(-1)

server_name = sys.argv[1]
user_name = sys.argv[2]
password = sys.argv[3]

# Get the product name
try:
    r = tintri.api_version(server_name)
    json_info = r.json()
    product_name = json_info['productName']
    if json_info['productName'] != "Tintri VMstore":
        raise tintri.TintriRequestException("server needs to be a VMstore.")

    # Login to Tintri server
    session_id = tintri.api_login(server_name, user_name, password)

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    exit(-2)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    exit(-3)
    
try:
    print("\nLoading transporter buffers\n")

    # Get appliance info
    url = "/v310/appliance"
    r = tintri.api_get(server_name, url, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)

    appliance_resp = r.json()
    appliance = appliance_resp[0]

    # Get failed Components for the appliance
    url = "/v310/appliance/default/failedComponents"
    r = tintri.api_get(server_name, url, session_id)
    print_debug("The JSON response of the get invoke to the server " +
                server_name + " is: " + r.text)

    failed_components_resp = r.json()
    failed_components = failed_components_resp['failedComponents']

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    tintri.api_logout(server_name, session_id)
    exit(-10)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    tintri.api_logout(server_name, session_id)
    exit(-11)
    
# log out
tintri.api_logout(server_name, session_id)

# Some basic info
all_flash = False
show_all_flash = False

appliance_info = appliance['info']

if 'isAllFlash' in appliance_info:
    all_flash = appliance_info['isAllFlash']
    show_all_flash = True

print("Appliance")
table_header = ('Info', 'Value')
table = PrettyTable(table_header)
table.align['Info'] = "l"
table.align['Value'] = "l"

row = ('Product', product_name)
table.add_row(row)

row = ('Model', appliance_info['modelName'])
table.add_row(row)

if show_all_flash:
    row = ('All Flash', all_flash)
    table.add_row(row)

long_os_version = appliance_info['osVersion']
dash_x = long_os_version.index("-")
os_version = long_os_version[0:dash_x]
row = ('OS version', os_version)
table.add_row(row)

row = ('API version', json_info['preferredVersion'])
table.add_row(row)

print(table)
print("")

# Appliance Component info
print("Appliance Componets")
table_header = ('Component', 'Status', 'Location')
table = PrettyTable(table_header)
table.align['Component'] = "l"
table.align['Status'] = "l"
table.align['Location'] = "l"

components = appliance['components']
for component in components:
    row = (component['type'], component['status'], component['locator'])
    table.add_row(row)

print(table)
print("")

# Show failed components
if (len(failed_components) == 0):
    print("No failed components")
else:
    print("Failed Components")
    table_header = ('Component', 'Serial #', 'Description')
    table = PrettyTable(table_header)
    table.align['Component'] = "l"
    table.align['Serial #'] = "l"
    table.align['Description'] = "l"
    for component in failed_components:
       row = (component['componentType'], component['serialNumber'], component['description'])
       table.add_row(row)
    
    print(table)
print("") 
    
# Show the configured IP address information
table_header = ('IP', 'Service Type', 'Network Bond', 'VLAN ID')
table = PrettyTable(table_header)
table.align['IP'] = 'l'

ip_configs = appliance['configIps']
for ip_config in ip_configs:
    row = (ip_config['ip'], ip_config['serviceType'], ip_config['networkBond'], ip_config['vlanId'])
    table.add_row(row)

print(table)
print ""

# Now show each controller information
table_header = ('Component', 'Location', 'Status')
nb_table_hdr = ('Port', 'Port Status', 'Role', 'Speed')

# Pull the controller information
controllers = appliance['controllers']
for controller in controllers:
    print(controller['locator'] + ": " + controller['state'] + " - " + controller['role'])
    table = PrettyTable(table_header)
    table.align['Component'] = "l"
    table.align['Location'] = "l"
    table.align['Status'] = "l"

    components = controller['components']
    for component in components:
        row = (component['type'], component['locator'], component['status'])
        table.add_row(row)

    print(table)
    print("")

    # Add network information
    network_bonds = controller['networkBonds']
    for nb in network_bonds:
        print(controller['locator'] + ": " + nb['name'] + ": " + nb['type'] + ": " + nb['status'] + ": " + nb['macAddress'])
        table = PrettyTable(nb_table_hdr)
        for port in nb['ports']:
            port_speed = str(port['maxSpeed']) + port['maxUnit']
            nb_row = (port['locator'], port['status'], port['role'], port_speed)
            table.add_row(nb_row)
        print(table)

    print("")

# Disks
if (not 'disks' in appliance):
    print("No disk information present")
    sys.exit(0)

print("Disks")
table_header = ('Name', 'Status', 'Type')
table = PrettyTable(table_header)
table.align['Name'] = "l"
table.align['Status'] = "l"
table.align['Type'] = "l"
disks = appliance['disks']
for disk in disks:
    if (disk['state'] == "DISK_STATE_REBUILD"):
        disk_state = disk['state'] + " (" + str(disk['rebuildPercent']) + "%)"
    else:
        disk_state = disk['state']
    if 'diskType' in disk:
        row = (disk['locator'], disk_state, disk['diskType'])
    else:
        row = (disk['locator'], disk_state, disk['type'])
    table.add_row(row)

print(table)
print("")
