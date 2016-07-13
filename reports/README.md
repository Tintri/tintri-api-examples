# get\_vm\_report.py

The Python script, get\_vm\_report.py downloads a CSV report on VMs. This script
takes a CSV input file that controls which columns are in the report. 

There are 2 input CSV files, a template and and example. The template file,
vm\_report\_fields.csv, contains all the valid fields or columns that be included in
the VM report. Each line in the file contains the field name and a short
description. To customize the report, copy vm\_report\_fields.py to a new file
and uncomment the field lines in the new file to be included in the report.
An example of this is vm\_latency\_report\_fields.csv.

    Usage:
      get_vm_report.py <server_name> <field_file> <report_file>

    Where:
      server_name: TGC name or IP address
      field_file:  file name that contains the fields to report
      report_file: output CSV file name

    Example:
      get_vm_report.py tgc1x vm_latency_report_fields.csv vm_latency_report.csv

####Imports
* tintri\_1\_1.py 
* sys
* csv
* os.path
* getpass