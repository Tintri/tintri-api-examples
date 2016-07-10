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
import csv
import os.path
import getpass
import tintri_1_1 as tintri

"""
 This Python script prints a URL that downloads a CSV report.

 Command usage: get_vm_report.py <server_name> <field_file_name> <csv_file_name>

"""

# For exhaustive messages on console, make it to True; otherwise keep it False
debug_mode = False
BEANS_VM = "com.tintri.api.rest.v310.dto.domain.beans.vm."


def print_with_prefix(prefix, out):
    print(prefix + out)
    return


def print_debug(out):
    if debug_mode:
        print_with_prefix("[DEBUG] : ", out)
    return


def print_error(out):
    print_with_prefix("[ERROR] : ", out)
    return


def print_info(out):
    print_with_prefix("[INFO] : ", out)
    return


def get_fields(field_file_loc):

    fields = []
    
    try:
        if os.path.isfile(field_file_loc):
            with open(field_file_loc,'r') as csv_file:
                csv_list = csv.reader(csv_file)
                for row in csv_list:
                    print_debug(str(row))
                    field = row[0].strip(' ')
                    if (field[0] != '#'):
                        fields.append(field)
        else:
            raise Exception("Could not find file " + field_file_loc)
    
        return fields
    
    except Exception as tre:
        print_error(tre.__str__())
        sys.exit(4)


# main
if len(sys.argv) < 4:
    print("\nDownloads a CSV VM report. \n")
    print("Usage: " + sys.argv[0] + " server_name field_file_name csv_file_name\n")
    print("Where:")
    print("   server_name:     TGC server name or IP address")
    print("   field_file_name: input file name that contains the fields to report")
    print("   csv_file_name:   output report CSV file name")
    print ""
    sys.exit(1)

server_name = sys.argv[1]
field_file_name = sys.argv[2]
csv_file_name = sys.argv[3]

# Get the field attributes to report
attributes = get_fields(field_file_name)
if len(attributes) == 0:
    print_error("No fields specified in " + field_file_name)
    sys.exit(1)

print("Fields to report:\n" + str(attributes))

# Credentials Gathering - support Python 2.X and 3.X
try: 
	user_name = raw_input("Enter user name: ")
except NameError:
	user_name = input("Enter user name: ")
password = getpass.getpass("Enter password: ")
print("")

session_id = None

# Try to login into the TGC.
try:
    r = tintri.api_get(server_name, '/info')
    json_info = r.json()
    product_name = json_info['productName']

    # Check for correct product
    if product_name  != "Tintri Global Center":
        raise tintri.TintriRequestException(server_name + "is not a Tintri Global Center server.")

    session_id = tintri.api_login(server_name, user_name, password)
except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    sys.exit(1)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    sys.exit(2)
    
try:
    url = "/v310/vm/vmListDownloadable"

    # Create the report filter.
    report_filter = {"typeId" : BEANS_VM + "VirtualMachineDownloadableReportFilter",
                     "attachment" : csv_file_name,
                     "attributes" : attributes,
                     "since"  :     "",
                     "until"  :     "",
                     "format" :     "CSV"
                    }

    # Invoke API to get a useable report URL.
    r = tintri.api_post(server_name, url, report_filter, session_id)
    if r.status_code != 200:
        message = "The HTTP response for report call to the server is not 200."
        raise tintri.TintriApiException(message, r.status_code, url, report_filter, r.text)
    
    report_url = r.text

    # Print the URL.
    print("URL: {" + report_url + "} is good for 30 days")
    
    # Get the report.
    tintri.download_file(server_name, report_url, session_id, csv_file_name)
    
    print(csv_file_name + " is ready")


    tintri.api_logout(server_name, session_id)

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    tintri.api_logout(server_name, session_id)
    sys.exit(5)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    tintri.api_logout(server_name, session_id)
    sys.exit(6)
except Exception as e:
    print_error(e.__str__())
    tintri.api_logout(server_name, session_id)
    sys.exit(6)
