#!/bin/bash

DATE=$(date +%Y%m%d)
TIMEZONE=-6
hour=$(date +%H)

if [ "$hour" -ge 6 ]; then
    DATE=$(date -d "$DATE +1 day" +%Y%m%d)
fi

scp NBF:/home/jreyes/sto_reports/disabled_by_sre-$DATE.log /home/jreyes/sto_reports/NBF
scp NBF:/home/jreyes/sto_reports/sto_reasons_raw_$DATE.csv /home/jreyes/sto_reports/NBF

docker run --rm -v "/home/jreyes/sto_reports/NBF:/app" process_sto_data python post-processing.py $DATE $TIMEZONE
