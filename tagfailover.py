#######
# upcoming enhancements:
# 1) Meraki SDK Integration
#
# 4) integrate with Webex for ChatOPS
#
#to run tagfailover.py --apikey <value> --orgid <value>


import json, time, argparse, datetime
from pathlib import Path
import subprocess, sys, pkg_resources, os

# Install Required Packages if missing
required = {'requests', 'meraki'}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed

if missing:
    # implement pip as a subprocess:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])

import requests
import meraki

# collect the runtime arguments
parser = argparse.ArgumentParser()
parser.add_argument('--apikey', type=str, required=True, help='Enter your API Key')
parser.add_argument('--orgid', type=str, required=True, help='Enter Your Orginization ID')

# Parse the argument
args = parser.parse_args()

########begin Constants - api_key, org_ID ############
api_key = args.apikey
org_ID = args.orgid
########End Constants ################################

url = f'https://api.meraki.com/api/v1/organizations/{org_ID}/devices/uplinksLossAndLatency'
header = {"X-Cisco-Meraki-API-Key": api_key, "Content-Type": "application/json"}

networkDownList = []

#Make sure ipToMonitor.txt is populated with the remote IPs you wish to monitor, these should match the monitored IPs you added in Dashboard

while True:
    monitoredIps = []
    eventtime = datetime.datetime.now()
    exceptionlog = "exceptions.txt"
    ipsToMonitor = "ipToMonitor.txt"
    
    #Since this read from a file monitored endpoints can be updated on the fly without stopping the script
    #read the file and append to the monitoredIps list object
    with open(ipsToMonitor) as file:
        while (line := file.readline().rstrip()):
            monitoredIps.append(line)
            
    try:
        response = requests.get(url, headers=header)
        for network in response.json():
            tagsModified = []
            if network['ip'] in monitoredIps:
                network_info = requests.get("https://api.meraki.com/api/v1/networks/" + network['networkId'],
                                            headers=header)
                if network_info.status_code != 200:
                    print("Issue Communicating with the API, Retrying")
                    break

                print("------------------------")
                print(network_info.json()['name'])
                print("Network_ID: " + network['networkId'])
                print("Monitored_IP: " + network['ip'])
                print("Device_Serial: " + network['serial'])
                loss = False
                tagsCurrent = network_info.json()['tags']
                for tag in tagsCurrent:
                    if "_primary" in tag:
                        primary = tag
                    elif "_backup" in tag:
                        backup = tag
                    else:
                        tagsModified.append(tag)



                for iteration in network['timeSeries']:
                    if iteration['lossPercent'] >= 30 or iteration['latencyMs'] >= 800:
                        loss = True
                        tags = network_info.json()['tags']

                        if any("_primary_down" in t for t in tags):
                            print("VPN already swapped")
                            break

                        else:
                            print("Need to change VPN, recent loss - " + str(iteration['lossPercent']) + " - " + str(iteration['latencyMs']))
                            tagsModified.append(primary.split("_up")[0] + "_down")
                            tagsModified.append(backup.split("_down")[0] + "_up")

                            payload = {'tags': tagsModified}
                            new_network_info = requests.put(
                                "https://api.meraki.com/api/v1/networks/" + network['networkId'],
                                data=json.dumps(payload),
                                headers=header)
                            networkDownList.append(network['networkId'])
                            break

                    if loss == False and network['networkId'] in networkDownList:
                        print("Primary VPN healthy again..swapping back")

                        tagsModified.append(primary.split("_down")[0] + "_up")
                        tagsModified.append(backup.split("_up")[0] + "_down")

                        payload = {'tags': tagsModified}

                        new_network_info = requests.put(
                            "https://api.meraki.com/api/v1/networks/" + network['networkId'],
                            data=json.dumps(payload), headers=header)
                        networkDownList.remove(network['networkId'])

    except Exception as error:
        logdata = (error.__class__)
        inpath = Path(exceptionlog)
        with inpath.open('a') as ef:
            ef.write(str(eventtime) + ' ' + str(logdata) + '\n')
        print(eventtime, "exception occurred & logged.")
        pass

    print("Sleeping for 30s...")
    time.sleep(30)

