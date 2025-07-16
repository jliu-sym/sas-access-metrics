#!/bin/bash

DATE=$(date +%Y%m%d)
hour=$(date +%H)

if [ "$hour" -ge 6 ]; then
    DATE=$(date -d "$DATE +1 day" +%Y%m%d)
fi

echo "SAS-STO data from NBF." | mailx -s "[Auto-Sent-From-NBF]" -a /home/jreyes/sto_reports/NBF/sto_reasons_chart_$DATE.png -a /home/jreyes/sto_reports/NBF/sto_reasons_$DATE.csv -r "jreyes@symbotic.com" psobalvarro@symbotic.com jreyes@symbotic.com
