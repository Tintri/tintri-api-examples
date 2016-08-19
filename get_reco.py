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
import datetime
import argparse
import json
import smtplib
import tintri_1_1 as tintri
from email.mime.text import MIMEText

"""
 This Python script generates a recommendation.

 Command usage: 


"""

# For exhaustive messages on console, make it to True; otherwise keep it False
debug_mode = False
beans = "com.tintri.api.rest.v310.dto.domain.beans."

# Global text
output_text = []


# Class for VMstore pool.
class VmstorePool:
    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid
        self.reco_uuid = None

    def get_name(self):
        return self.name

    def get_uuid(self):
        return self.uuid

    def get_reco_uuid(self):
        return self.reco_uuid

    def set_reco_uuid(self, reco_uuid):
        self.reco_uuid = reco_uuid


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


# Buffers the output for later.
def buffer(buf):
    #print_info(buf)
    output_text.append(buf)


# Format JSON into something readable.
def format_json(out):
    return json.dumps(out, sort_keys=True, indent=4, separators=(',', ': '))


# Convert VM UUIDs to VM names
# This is a simple but time consuming way.
def get_vm_names(server, tgc_sess_id, vm_uuids):
    vm_names = []

    for vm_uuid in vm_uuids:
        vm_url = "/v310/vm/" + vm_uuid

        r = tintri.api_get(server, vm_url, tgc_sess_id)
        print_debug("The JSON response of the vm get invoke to the server " + \
                    server + " is: " + r.text)
        vm_info = r.json()
        vm_names.append(vm_info["vmware"]["name"])

    return vm_names


# Return the the VMstore pools from a TGC server.
def get_pools(server, tgc_sess_id):
    vmstore_pools = []

    url = "/v310/vmstorePool"
    r = tintri.api_get(server, url, tgc_sess_id)
    print_debug("The JSON response of the get invoke to the server " +
                server + " is: " + r.text)

    vm_paginated_result = r.json()
    num_pools = int(vm_paginated_result["filteredTotal"])
    if (num_pools) == 0:
        raise tintri.TintriRequestsException("No VMstore Pools present")

    # Load up the pools
    items = vm_paginated_result["items"]
    for pool in items:
        print_info(pool["name"] + ": " + pool["uuid"]["uuid"])
        vmstore_pool = VmstorePool(pool["name"], pool["uuid"]["uuid"])
        vmstore_pools.append(vmstore_pool)

    return vmstore_pools


# Print the recommendation issues.
def get_issues(reco):
    if "issues" in reco:
        buffer("Issues")

        issues = reco["issues"]
        for issue in issues:
            name = issue["vmStoreDisplayName"]
            if "flashInfo" in issue:
                buffer("    " + name + ": Flash - " + issue["flashInfo"]["summary"])
            if "iopsInfo" in issue:
                buffer("    " + name + ": IOPS - " + issue["iopsInfo"]["summary"])
            if "spaceInfo" in issue:
                buffer("    " + name + ": Space - " + issue["spaceInfo"]["summary"])
    else:
        buffer("No issues")


# Get the action issue types.
# There is an empty issue types bug.
def get_action_issue_types(actions):
    issue_types_str = ""
    for action in actions:
        issueTypes = action["issueTypes"]
        if (len(issueTypes) == 0):
            return "UNKNOWN"

        # Collect issue types
        for issueType in issueTypes:
            issue_types_str += issueType + ","

        issue_types_str = issue_types_str[:-1]  # remove trailing comma
        return issue_types_str


# Print the action groups
def get_action_groups(reco):
    if not ("actionGroups" in reco):
        buffer("No ation groups")
        return

    buffer("Action Groups")

    action_groups = reco["actionGroups"]
    print_debug("Groups: " + format_json(action_groups))

    for action_group in action_groups:
        actions = action_group["actions"]
        issueTypes = get_action_issue_types(actions)
        buffer("  Actions for " + issueTypes)
        for action in actions:
            if ("targetVmDisplayName" in action):
                vm_display_name = action["targetVmDisplayName"]
            else:
                vm_display_name = action["targetVmTintriUuid"]

            buffer("    " + vm_display_name  + " on " + action["sourceDatastoreDisplayName"] + \
                  " migrates to " + action["destinationDatastoreDisplayName"])


# Get the outcome summary.
def get_my_summary(server_name, sessiond_id, outcome):
    my_summary = ""
    if "flashInfo" in outcome:
        my_summary += outcome["flashInfo"]["issueType"] + ": "
        my_summary += str(outcome["flashInfo"]["flashHitRatePercent"]) + " percent predicted flash hit rate"
    elif "iopsInfo" in outcome:
        my_summary += outcome["iopsInfo"]["issueType"] + ": "
        my_summary += str(outcome["iopsInfo"]["predictedOutcomeLoadWeekPercent"]) + " percent predicted load"
    elif "protectionInfo" in outcome:
        my_summary += outcome["protectionInfo"]["issueType"] + ": "
        if ("summary" in outcome["protectionInfo"]):
            my_summary += outcome["protectionInfo"]["summary"]
        else:
            my_summary += "VMs not able to replicatte: "
            if ("vmTintriUuids" in outcome["protectionInfo"]):
                vm_names = get_vm_names(server_name, sessiond_id, \
                                        outcome["protectionInfo"]["vmTintriUuids"])
                my_summary += " ".join(vm_names)
            else:
                my_summary += " No UUIDs"
    elif "spaceInfo" in outcome:
        my_summary += outcome["spaceInfo"]["issueType"] + ": "
        my_summary += str(outcome["spaceInfo"]["spaceChangedPhysicalGiB"]) + " change in GiB"

    return my_summary


# Print outcomes
def get_outcomes(server_name, sessiond_id, reco):
    if (not ("expectedOutcomes" in reco)):
        buffer("No outcomes")
        return

    buffer("Outcomes")
    outcomes = reco["expectedOutcomes"]
    for outcome in outcomes:
        my_summary = get_my_summary(server_name, sessiond_id, outcome)
        buffer("    " + outcome["vmStoreDisplayName"] + ": " + my_summary)
        print_debug(format_json(outcome))


# Get the current recommendation
def get_current_reco(server, tgc_sess_id, pool):
    print_debug("Looking for recommendation on pool " + pool.get_name())
    reco_url = "/v310/vmstorePool/" + pool.get_uuid() + "/recommendation/current"

    r = tintri.api_get(server, reco_url, tgc_sess_id)
    print_debug("The JSON response of the reco get invoke to the server " +
                server + " is: " + r.text)
    reco = r.json()

    return reco


# Execute and accept the recommendation
def execute_reco(server, tgc_sess_id, pool):
    reco_url = "/v310/vmstorePool/" + pool.get_uuid() + "/recommendation/" + \
               pool.get_reco_uuid() + "/accept"
    r = tintri.api_post(server, reco_url, None, tgc_sess_id)
    print_debug("The JSON response of the accept reco invoke to the server " +
                server + " is: " + r.text)
    if (r.status_code != 204):
        msg = "The HTTP response for the accept reco post invoke to the server is " + \
              server + "not 200, but is: " + str(r.status_code) + "."
        raise tintri.TintriApiException(msg, r.status_code, reco_url, "No payload", r.text)


# Send e-mail.
def send_email(server_name, from_addr, to_addrs, smtp_server, output_text):

    out_buf = ""
    for text in output_text:
        out_buf += text + "\n"

    msg = MIMEText(out_buf)
    msg['Subject'] = "VM Scale-out Recommendations from TGC " + server_name
    msg['From'] = from_addr
    msg['To'] = ','.join(to_addrs)
    
    print_info("SMTP server: " + smtp_server)
    print_info("From: " + msg['From'])
    print_info("To: " + msg['To'])
    print_info("MIME text:\n" + str(msg) + "\n")
    
    try:
        s = smtplib.SMTP(smtp_server)
        s.sendmail(from_addr, to_addrs, msg.as_string())
        s.quit()
    except smtplib.SMTPException as smtp_err:
        print_error("SMTP error: " + smtp_err.__str__())


# main
accept_reco = False
from_email = ""
to_smail = ""
smtp_server = ""

pools = {}

# Forge the command line argument parser.
gen_descrip = "Get available recommendations and print. " + \
              "Optionally send mail and/or accept recommendation." 
epilog = "--you and --me are required to send e-mail in the form name@x.y. " + \
         "If --smtp is not sepcified then, smtp defaults to smtp.x.y."
parser = argparse.ArgumentParser(description=gen_descrip, epilog=epilog)

parser.add_argument("server_name", help="TGC server name")
parser.add_argument("user_name", help="TGC user name")
parser.add_argument("password", help="User name password")
parser.add_argument("--accept", action = "store_true", help="accept the recommendation")
parser.add_argument("--you", help="e-mail address to send (admin@x.y)")
parser.add_argument("--me", help="e-mail address to send from (postmaster@x.y)")
parser.add_argument("--smtp", help="SMTP server. Default: 'smtp.x.y>'")
        

args = parser.parse_args()

# Check for an e-mail address.
if args.me != None:
    from_email = args.me
    print_info("from e-mail: " + args.me)

if args.you != None:
    to_email = args.you
    print_info("to e-mail: " + args.you)

if (args.me != None and args.you != None):
    if args.smtp != None:
        smtp_server = args.smtp
    else:
        from_email_parts = from_email.split("@")
        smtp_server = "smtp." + from_email_parts[1]
    print_info("Default SMTP server: " + smtp_server)

# Check for recommendation acceptance.
if args.accept:
    accept_reco = True
    print_info("Accept recommendation")

# Collect the required parameters.
server_name = args.server_name
user_name = args.user_name
password = args.password

# Get the product name
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
    exit(-2)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    exit(-3)
    
# Let's get to work.
reco_available = False
try:
    pools = get_pools(server_name, session_id)

    # For each pool, get the current recommendation
    for pool in pools:
        reco = get_current_reco(server_name, session_id, pool)

        buffer("Pool: " + pool.get_name() + ": " + reco["state"])
        if (reco["state"] == "NO_RECOMMENDATION_NEEDED"):
            continue

        if (reco["state"] == "AVAILABLE"):
            pool.set_reco_uuid(reco["id"])

            get_issues(reco)
            get_action_groups(reco)
            get_outcomes(server_name, session_id, reco)
            reco_available = True

        buffer("")

    if accept_reco:
        for pool in pools:
            if reco["state"] == "AVAILABLE" and pool.get_reco_uuid():
                execute_reco(server_name, session_id, pool)
                buffer("Accepted and executed recommendation for pool " + pool.get_name())

        buffer("")

except tintri.TintriRequestsException as tre:
    print_error(tre.__str__())
    exit(-4)
except tintri.TintriApiException as tae:
    print_error(tae.__str__())
    exit(-5)

# Log out
tintri.api_logout(server_name, session_id)

# Now print the text
print ""
for text in output_text:
    print(text)

# if we have e-mail values, then send.
if (reco_available):
    if (len(from_email) > 0) and (len(to_email) > 0) or (len(smtp_server) > 0):
        to_addrs = [to_email]  # Only allow one to email
        send_email(server_name, from_email, to_addrs, smtp_server, output_text)
        print_info("E-mail sent\n")
    else:
        print_info("Not enough information to send e-mail")

