# m_tagbasedfailover
a modernization of the tag based failover example from documentation.meraki.com @ https://documentation.meraki.com/MX/Site-to-site_VPN/Tag-Based_IPsec_VPN_Failover

File Definitions:
1. ipToMonitor.txt -   is where you define the monitored ips that the script will use to determine if failover is required. This file can be modified   real time to add and remove endpoints, without stopping the script.
2. tagfailover.py the actual script that runs in a loop until interupted.
3. exceptions.txt a text based log file, created and updated if any events occur.

to execute copy tagfailover.py and ipToMonitor.txt to a directory and execute with tagfailover.py --apikey <value> --orgid <value>
