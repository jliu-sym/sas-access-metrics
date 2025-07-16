#!/bin/bash

export PYTHONPATH=:/home/jreyes/sas-tools_new_sas_monitor/opt/sas-eng/python:/home/jreyes/sas-tools_new_sas_monitor/opt/sas-ops/python

DATE=$(date +%Y%m%d)
hour=$(date +%H)

if [ "$hour" -lt 5 ]; then
# the whole log of the previous day will be processed
    /usr/bin/grep -i "sto_reason" /logs/safety/scpu-$DATE.log > /home/jreyes/sto_reports/sto_reasons_raw_$DATE.log
    /usr/bin/grep "#4107" /logs/safety/scpu-$DATE.log | grep -E "CAN_DRIVE.*DISABLED" | grep -v nobib | grep -vE '([0-9]{1,3}\.){3}[0-9]{1,3}' | gawk '{print $1,$2}' | sed -E 's/([0-9T:.\-]+)-[0-9:+]+ [a-zA-Z]+([0-9]{1,5})\..*/\1 \2/' > /home/jreyes/sto_reports/disabled_by_sre-$DATE.log
    python3 -m logAnalysis.sas-sto /home/jreyes/sto_reports/sto_reasons_raw_$DATE.log > /home/jreyes/sto_reports/sto_reasons_raw_$DATE.csv
else
# the partial log of the current day will be processed
    DATE=$(date -d "$DATE +1 day" +%Y%m%d)
    /usr/bin/grep -i "sto_reason" /logs/safety/scpu.log > /home/jreyes/sto_reports/sto_reasons_raw_$DATE.log
/usr/bin/grep "#4107" /logs/safety/scpu.log | grep -E "CAN_DRIVE.*DISABLED" | grep -v nobib | grep -vE '([0-9]{1,3}\.){3}[0-9]{1,3}' | gawk '{print $1,$2}' | sed -E 's/([0-9T:.\-]+)-[0-9:+]+ [a-zA-Z]+([0-9]{1,5})\..*/\1 \2/' > /home/jreyes/sto_reports/disabled_by_sre-$DATE.log
python3 -m logAnalysis.sas-sto /home/jreyes/sto_reports/sto_reasons_raw_$DATE.log > /home/jreyes/sto_reports/sto_reasons_raw_$DATE.csv
fi
