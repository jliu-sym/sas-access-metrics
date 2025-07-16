#!/usr/bin/python
"""
    @sas-sto.py

    Symbotic Matrix Bot Safety System Tools
    Copyright 2024,
    Symbotic LLC
    200 Research Drive
    Wilmington, Massachusetts 01887

    Created on: Aug 1, 2024
        Author: bray
	Description: sas-sto parses through a safety log file to extract the bots, which got disabled during an area access.
				It generates a report on the disabled bots with reasons and writes them in multiple output files. 
				The reasons are sourced from accountant code: src/core/include/safetyTypes.h 
				and is shown below as reference:
enum STOReasonCodeEnum {
    SR_NOT_STO                     = 0,             // Reserved for LEVEL census, and to clear STO reason
    SR_ESTOP_PRESSED               = (1 << 16),     // mbot Estop button is pressed 
    SR_BOT_OUTSIDE_STRUCTURE       = (2 << 16),     // mbot is in lift, stand or maint census
    SR_UNKNOWN_DURING_ACCESS       = (3 << 16),     // mbot is in UNKNOWN census during access                                      
    SR_LOST_COMMUNICATIONS         = (4 << 16),     // mbot has lost comm
    SR_LEVEL_ACCESS                = (5 << 16),     // level key is being requested
    SR_NOT_LOCALIZED               = (6 << 16),     // Bot not localized after aisle gate closed
    SR_INVALID_ACCESS_AREA         = (7 << 16),     // Invalid key or zone accessed
    SR_CRITICAL_ERRORS             = (8 << 16),     // Critical errors exist on the bot
    SR_BOT_ID_FAILURE              = (9 << 16),     // Bot ID from Simba is not valid
    SR_GSTO                        = (10 << 16),    // Global STO triggered
    SR_BOT_IN_DRIVEWAY             = (11 << 16),    // Bot in accessed driveway during access
    SR_INTERNAL_ERROR              = (12 << 16),    // Unable to determine safety status
    SR_SAFETY_BYBASSED             = (13 << 16),    // Key released or door opened with no access request
 
    SR_LAST_STO_REASON_CODE        = (15 << 16),    // Last value for STO reason - that is 5 bits
 
    STOReasonCodeEnum_LAST_ELEMENT = UINT32_MAX     // force 32 bit enum
};

	Usage: python sas-sto.py [<safety-log-file>]
			1. if no log file is given, it reads the default log file (/logs/safety/scpu.log)
			2. the log file could be a text file or gz type file 
	Output: a set of output files showing bots disabled due to:
			1. unsafe aisle
			2. unsafe level
			3. unsafe cell (driveway)
			4. out of comm
			5. invalid access area (wrongi/bad codeplate)
			6. Unlocalized bots during or before the access request.
"""
# imports
import os
import re
import time
import sys
import datetime
from operator import itemgetter, attrgetter
import gzip
import lzma

# defines
SPACE                       =   " "
TIME_RSPLIT_IAR             =   '-'
TIME_RSPLIT_BG              =   '+'

# default input safety log file
DEFAULT_LOG_FILE 			= 	"/logs/safety/scpu.log"
# output files - contains the sto report
STO_UNSAFE_LEVEL 			= 	"sto_level.log"
STO_UNSAFE_AISLE 			= 	"sto_aisle.log"
STO_UNSAFE_DRIVEWAY 		= 	"sto_cell.log"
STO_INVALID_AREA			= 	"sto_unsafe_bot.log"
STO_NO_COMM					= 	"sto_no_comm.log"
STO_UNLOCALIZED_AT_LEVEL	=	"sto_unlocalized_level.log"

# sto events 
STO_EVENT_BYPASSED          =   "BYPASSED"
STO_EVENT_GATE_CLOSED       =   "gate_closed"
# sto events string
STO_REASON_BYPASS_STR       =   "BYPASSED (Key/door breached)."
STO_REASON_GATE_CLOSE_STR   =   "bot did not localize after gate closure."
STO_REASON_UNKNOWN_STR      =   "Unknown."

"""
    StoGetTimeString:
    input: string containing time
    to handle: 2024-02-03T08:51:08.958-05:00 or 2024-02-03T08:51:08.958+05:00
    output: returns the time string 2024-02-03T08:51:08.958
"""
def StoGetTimeString(tstr):
    if '+' in tstr:
        separator = '+'
    else:
        separator = '-'
    return tstr.rsplit(separator, 1)[0]


"""
	StoMultiSort: helper sort function. Given a list, and a set of keys, it will sort the list 
					in straight or reverse order and returns the sorted list
"""
def StoMultiSort(iList, keys):
    for key, reverse in reversed(keys):
        iList.sort(key = attrgetter(key), reverse = reverse)
    return iList

"""
	StoDateTimeSort: helper sort function. Given a list, sort by dateTime field
    DateTime format: (YYYY-MM-DDTHH:MN:SS.msec) e.g., 2024-03-21T03:38:32.627 
"""
def StoDateTimeSort(iList, start, end):
    dateFormat = '%Y-%m-%dT%H:%M:%S.%f'
    iList_t = sorted(iList[start:(end +1)], key = lambda x: datetime.datetime.strptime(x.reportTime, dateFormat))
    return iList_t

def StoGetStoReasonStrReduced(stoLine):
    if (stoLine.eventType == STO_EVENT_BYPASSED) or (stoLine.state == STO_EVENT_BYPASSED):
        stoReason = STO_REASON_BYPASS_STR
        str = stoReason
    elif stoLine.eventType == STO_EVENT_GATE_CLOSED:
        stoReason = STO_REASON_GATE_CLOSE_STR
        str = stoReason
    else:
        stoReason = STO_REASON_UNKNOWN_STR + SPACE + stoLine.eventType
        str = stoReason
    return str

def StoParseStoReason(stoLine):
    idx1 = stoLine.index("sto_reason")
    if "PlcID" in stoLine:
        idx2 = stoLine.index("PlcID")
        stoReason = "_".join(stoLine[idx1+1 : idx2])
    else:
        stoReason = "_".join(stoLine[idx1+1 :])
    return stoReason


def StoGetStoReasonStr(stoLine):
    if (stoLine.eventType == STO_EVENT_BYPASSED) or (stoLine.state == STO_EVENT_BYPASSED):
        stoReason = STO_REASON_BYPASS_STR
        str = "Bot " + stoLine.botid + " was disabled at " + stoLine.reportTime + \
        " with sto_reason: " + stoReason + " LastLocationTime " + \
        stoLine.lastLocTime + stoLine.lastLocYear + '\n'
    elif stoLine.eventType == STO_EVENT_GATE_CLOSED:
        stoReason = STO_REASON_GATE_CLOSE_STR
        str = "Bot " + stoLine.botid + " was disabled at " + stoLine.reportTime + \
                " with sto_reason: " + stoReason + \
                " LastLocationTime " + stoLine.lastLocTime + stoLine.lastLocYear + \
                " GateClosedTime " + stoLine.eventTime + stoLine.eventYear + '\n'
    else:
        stoReason = STO_REASON_UNKNOWN_STR + SPACE + stoLine.eventType
        str = "Bot " + stoLine.botid + " was disabled at " + stoLine.reportTime + \
                " with sto_reason: " + stoReason + \
                " LastLocationTime " +  stoLine.lastLocTime + \
                stoLine.lastLocYear + '\n'
    return str

"""
    class AilseAccess: to store the collected log of a bot, which was stoed due to unsafe Aisle 
"""
class AilseAccess:
    def __init__(self, botid, zone, aisle, state, lastLocTime, lastLocYear, eventType, eventTime, eventYear, reportTime, logStoReason):
        self.botid = '{0: <5}'.format(botid)
        self.zone = zone
        self.aisle = aisle
        self.state = state
        self.lastLocTime = lastLocTime
        self.lastLocYear = lastLocYear
        self.eventType = eventType
        self.eventTime = eventTime
        self.eventYear = eventYear
        self.reportTime = reportTime
        self.stoReason = logStoReason
    def __repr__(self):
        return repr((self.botid, self.zone, self.aisle, self.state, self.lastLocTime, \
                self.lastLocYear, self.eventType, self.eventTime, \
                self.eventYear, self.reportTime, self.stoReason))

#------------------------------------------------------------------------------------------------------
"""
 StoReasonUnsafeAisleReport - generate the report of disabled bots in a unsafe aisle
 input: 
   sto_list - list of entries of type class AilseAccess
   {zone, aisle, state} - tuple to search 
   entry - starting index to the sto_list for search
   w - file to write
 self.botid, self.aisle, self.state, self.lastLocTime, self.eventType, self.eventTime, self.reportTime
"""
#------------------------------------------------------------------------------------------------------
def StoReasonUnsafeAisleReport(stoList, zone, aisle, state, entry, wFile):
    for lastEntry in range(entry, len(stoList)):
        if (stoList[lastEntry].zone == zone) and \
                (stoList[lastEntry].aisle == aisle) and \
                (stoList[lastEntry].state == state):
            pass
        else:
            break
    stoListAisle = StoDateTimeSort(stoList, entry, lastEntry)
    stoReason = ''
    stoReport = []
    botList = []
    for row in range(len(stoListAisle)):
        if stoListAisle[row].botid not in botList:
            botList.append(stoListAisle[row].botid)
            stoReason = StoGetStoReasonStr(stoListAisle[row])
            stoReport.append(stoReason)
    
    r1 = "\tNumber of bots disabled-by-safety: " + "{0: <5}".format(len(botList)) + \
            " at Zone: " + "{0: <3}".format(zone)  + " Aisle: " + "{0: <3}".format(aisle) + \
            " with state: " + state + " Total log entries: " + "{0: <5}".format(len(stoListAisle))
    #print(r1)
    wFile.writelines('\n' + r1 + '\n')
    wFile.writelines(stoReport)
    # return the starting index to the sto_list for next search
    return (lastEntry + 1)

#----------------------------------------------------------------------------------------------
# 2024-03-21T04:58:59.746-04:00 act00006.mservices.wmt06020-c.symbotic <info> work   6204 #3084 _census_  Unsafe zone 2 aisle 1 bot 8798 : state=PREPARING  scan@04:38:45 [21-Mar]   gate_closed@08:51:38 [21-Mar]
# List = [botid, zone, aisle, state, locStamp, eventType, eventTimeStamp, ReportTime]
#----------------------------------------------------------------------------------------------
def StoReasonUnsafeAisle(log):
    stoUnsafeAisle = []
    stoList = []
    pattern = r"Unsafe zone"
    #regS = re.compile(pattern)
    try:
        wFile = open(STO_UNSAFE_AISLE, "w+")
    except OSError:
        print("StoReasonUnsafeAisle: Could not open file: ", STO_UNSAFE_AISLE)
        sys.exit()
    with wFile:
        for line in log:
            #if regS.search(line):
            #if line.find(pattern) != -1:
            if pattern in line:
                elems = line.split()
                stoUnsafeAisle = AilseAccess(elems[13], \
                        elems[9], \
                        elems[11], \
                        elems[15].split('=')[1], \
                        elems[16].split('@')[1], \
                        elems[17], elems[18].split('@')[0], \
                        elems[18].split('@')[1], \
                        elems[19], \
                        StoGetTimeString(elems[0]), \
                        StoParseStoReason(elems) ) #.rsplit(TIME_RSPLIT_BG, 1)[0]) 
                stoList.append(stoUnsafeAisle)
                stoUnsafeAisle = []
        stoList = StoMultiSort(list(stoList), (('zone', False), ('aisle', False), ('state', False)))
        reportUnsafeAisle = "-----------Disabled-by-safety due to Unsafe Aisle -----------"
        # if len(stoList) > 0:
        #     print(reportUnsafeAisle)
        wFile.writelines(reportUnsafeAisle + '\n')
        
        for entry in stoList:
            print(f"{entry.reportTime.split('T')[0]},{entry.reportTime.split('T')[1]},{entry.botid},zone:{entry.zone};aisle:{entry.aisle},aisle_access,{entry.stoReason},{entry.lastLocTime}{entry.lastLocYear},{entry.eventTime}{entry.eventYear}")

        entry = 0
        while entry < len(stoList):
            zone = stoList[entry].zone
            aisle = stoList[entry].aisle
            state = stoList[entry].state
            entry = StoReasonUnsafeAisleReport(stoList, zone, aisle, state, entry, wFile) 
        wFile.close()

#----------------------------------------------------------------------------------------------------
# 2024-03-21T03:38:35.476-04:00 act00006.mservices.wmt06020-c.symbotic <info> work  57476 #3084 _census_  Unsafe cell 17 zone 1 driveway 1 bot 10063 : state=SAFE_ACCESS_GRANTED  scan@06:08:04 [21-Mar]   gate_closed@07:25:22 [21-Mar]
# List = [botid, cell, zone, driveway, state, locStamp, eventType, eventStamp, reportTime]
#----------------------------------------------------------------------------------------------------
"""
    class DrivewayAccess: to store the collected log of a bot, which was stoed due to unsafe Cell 
"""
class DrivewayAccess:
    def __init__(self, botid, cell, zone, driveway, state, lastLocTime, lastLocYear, eventType, eventTime, eventYear, reportTime, logStoReason):
        self.botid = '{0: <5}'.format(botid)
        self.cell = cell
        self.zone = zone
        self.driveway = driveway
        self.state = state
        self.lastLocTime = lastLocTime
        self.lastLocYear = lastLocYear
        self.eventType = eventType
        self.eventTime = eventTime
        self.eventYear = eventYear
        self.reportTime = reportTime
        self.stoReason = logStoReason
    def __repr__(self):
        return repr((self.botid, self.cell, self.zone, self.driveway, self.state, \
                self.lastLocTime, self.lastLocYear, self.eventType, \
                self.eventTime, self.eventYear, self.reportTime, self.stoReason))

#------------------------------------------------------------------------------------------------------
"""
 StoReasonUnsafeDrivewayReport - generate the report of disabled bots in a unsafe cell
 input: 
   sto_list - list of entries of type class AilseAccess
   {zone, aisle, cell, state} - tuple to search 
   entry - starting index to the sto_list for search
   w - file to write
   each entry of the input list: self.botid, self.zone, self.aisle, self.cell, self.state, self.lastLocTime, self.eventType, 
									self.eventTime, self.reportTime
"""
#------------------------------------------------------------------------------------------------------
def StoReasonUnsafeDrivewayReport(stoList, zone, cell, driveway, state, entry, w):
    for lastEntry in range(entry, len(stoList)):
        if (stoList[lastEntry].zone == zone) and \
                (stoList[lastEntry].cell == cell) and \
                (stoList[lastEntry].driveway == driveway) and \
                (stoList[lastEntry].state == state):
            pass
        else:
            break
    stoListDW = StoDateTimeSort(stoList, entry, lastEntry)
    stoReason = ''
    stoReport = []
    botList = [] 
    for row in range(len(stoListDW)):
        if stoListDW[row].botid not in botList:
            botList.append(stoListDW[row].botid)
            stoReason = StoGetStoReasonStr(stoListDW[row])
            stoReport.append(stoReason)
    
    r1 = "\tNumber of bots disabled-by-safety: " + "{0: <5}".format(len(botList)) + \
            " at Zone: " + "{0: <3}".format(zone) + " Cell: " + "{0: <3}".format(cell) + \
            " Driveway: " + "{0: <3}".format(driveway) + "State: " + state + \
            " Total log entries: " + "{0: <5}".format(len(stoListDW))
    #print(r1)
    w.writelines('\n' + r1 + '\n')
    w.writelines(stoReport)
    return (lastEntry + 1)


def StoReasonUnsafeDriveway(log):
    stoUnsafeDW = []
    stoList = []
    pattern = r"Unsafe cell"
    #regS = re.compile(pattern)
    try:
        wFile = open(STO_UNSAFE_DRIVEWAY, "w+")
    except OSError:
        print("StoReasonUnsafeDriveway: Could not open file: ", STO_UNSAFE_DRIVEWAY)
        sys.exit()
    with wFile:
        for line in log:
            #if re.search(str, line):
            #if regS.search(line):
            #if line.find(pattern) != -1:
            if pattern in line:
                elems = line.split()
                stoUnsafeDW = DrivewayAccess(elems[15], \
                        elems[9], \
                        elems[11], \
                        elems [13], \
                        elems[17].split('=')[1], \
                        elems[18].split('@')[1], \
                        elems[19], \
                        elems[20].split('@')[0], \
                        elems[20].split('@')[1], \
                        elems[21], \
                        StoGetTimeString(elems[0]), \
                        StoParseStoReason(elems) ) #elems[0].rsplit(TIME_RSPLIT_BG, 1)[0])
                stoList.append(stoUnsafeDW)
                stoUnsafeDW = []
        stoList = StoMultiSort(list(stoList), (('zone', False), ('cell', False), ('driveway', False), ('state', False)))
        reportUnsafeCell = "-----------Disabled-by-safety due to Unsafe Cell ------------"
        # if len(stoList) > 0:
        #     print(reportUnsafeCell)
        wFile.writelines(reportUnsafeCell + '\n')

        for entry in stoList:
            print(f"{entry.reportTime.split('T')[0]},{entry.reportTime.split('T')[1]},{entry.botid},zone:{entry.zone};cell:{entry.cell};driveway:{entry.driveway},driveway_access,{entry.stoReason},{entry.lastLocTime}{entry.lastLocYear},{entry.eventTime}{entry.eventYear}")
        entry = 0
        while entry < len(stoList):
            zone = stoList[entry].zone
            cell = stoList[entry].cell
            driveway = stoList[entry].driveway
            state = stoList[entry].state
            entry = StoReasonUnsafeDrivewayReport(stoList, zone, cell, driveway, state, entry, wFile)
        wFile.close()

#-------------------------------------------------------------------------------------------------
# 2024-03-21T03:38:32.627-04:00 act00002.mservices.wmt06020-c.symbotic <info> work  16736 #3084 _census_  Unsafe level 10 bot 10761 : state=SAFE_ACCESS_GRANTED  scan@06:34:54 [21-Mar]   gate_closed@07:33:12 [21-Mar]
# List = [Botid, level, state, locTimeStamp, eventType, eventTimeStamp, reportTime]
#-------------------------------------------------------------------------------------------------
"""
    class LevelAccess: to store the collected log of a bot, which was stoed due to unsafe Level 
"""
class LevelAccess:
    def __init__(self, botid, level, state, lastLocTime, lastLocYear, eventType, eventTime, eventYear, reportTime, logStoReason):
        self.botid = '{0: <5}'.format(botid)
        self.level = level
        self.state = state
        self.lastLocTime = lastLocTime
        self.lastLocYear = lastLocYear
        self.eventType = eventType
        self.eventTime = eventTime
        self.eventYear = eventYear
        self.reportTime = reportTime
        self.stoReason = logStoReason
    def __repr__(self):
        return repr((self.botid, self.level, self.state, self.lastLocTime, self.lastLocYear, \
                self.eventType, self.eventTime, self.eventYear, self.reportTime, self.stoReason))

#------------------------------------------------------------------------------------------------------
"""
 StoReasonUnsafeLevelReport - generate the report of disabled bots in a unsafe level 
 input: 
   sto_list - list of entries of type class LevelAccess
   {level, state} - tuple to search 
   entry - starting index to the sto_list for search
   w - file to write
   each entry of the input list: self.botid, self.level, self.state, self.lastLocTime, self.eventType, 
									self.eventTime, self.reportTime
"""
#------------------------------------------------------------------------------------------------------
def StoReasonUnsafeLevelReport(stoList, level, state, entry, w):
    for lastEntry in range(entry, len(stoList)):
        if (stoList[lastEntry].level == level) and (stoList[lastEntry].state == state):
            pass
        else:
            break
    stoListLevel = StoDateTimeSort(stoList, entry, lastEntry)
    stoReason = ''
    reportList = []
    botList = []
    for row in range(len(stoListLevel)):
        if stoListLevel[row].botid not in botList:
            botList.append(stoListLevel[row].botid)
            stoReason = StoGetStoReasonStr(stoListLevel[row])
            reportList.append(stoReason)

    r1 = "\tNumber of bots disabled-by-safety: " + "{0: <5}".format(len(botList)) + \
            " at Level: " + "{0: <3}".format(level) + \
            " with state: " + state + \
            " Total log entries: " + "{0: <5}".format(len(stoListLevel))
    #print(r1)
    w.writelines('\n' + r1 + '\n')
    w.writelines(reportList)
    return (lastEntry + 1)


def StoReasonUnsafeLevel(log):
     stoUnsafeLevel = []
     stoList = []
     pattern = r"Unsafe level"
     #regS = re.compile(pattern)
     try:
         wFile = open(STO_UNSAFE_LEVEL, "w+")
     except OSError:
         print("StoReasonUnsafeLevel: Could not open file: ", STO_UNSAFE_LEVEL)
         sys.exit()
     with wFile:
         for line in log:
             #if regS.search(line):
             #if pattern in line:
             #if line.find(pattern) != -1:
             if pattern in line:
                 elems = line.split()
                 stoUnsafeLevel = LevelAccess(elems[11], \
                         elems[9], \
                         elems[13].split('=')[1], \
                         elems[14].split('@')[1], \
                         elems[15], \
                         elems[16].split('@')[0], \
                         elems[16].split('@')[1], \
                         elems[17], \
                         StoGetTimeString(elems[0]), \
                         StoParseStoReason(elems)) #elems[0].rsplit(TIME_RSPLIT_BG, 1)[0])
                 stoList.append(stoUnsafeLevel)
                 stoUnsafeLevel = []
         stoList = StoMultiSort(list(stoList), (('level', False), ('state', False)))
         reportUnsafeLevel = "-----------Disabled-by-safety due to Unsafe Level -----------"
        #  if len(stoList) > 0:
        #      print(reportUnsafeLevel)
         wFile.writelines(reportUnsafeLevel + '\n')

         for entry in stoList:
            print(f"{entry.reportTime.split('T')[0]},{entry.reportTime.split('T')[1]},{entry.botid},lvl:{entry.level},level_access,{entry.stoReason},{entry.lastLocTime}{entry.lastLocYear},{entry.eventTime}{entry.eventYear}")
         entry = 0
         while entry < len(stoList):
             level = stoList[entry].level
             state = stoList[entry].state
             entry = StoReasonUnsafeLevelReport(stoList, level, state, entry, wFile)
         wFile.close()

#---------------------------------------------------------------------------------------------
"""
 Report bots with Invalid codeplate and hence disabled during access
 From log:
    List = [botid, level, eventType,  reportTime]
    eventType = 'closure' or 'BYPASSED'
"""
#---------------------------------------------------------------------------------------------
# List = [botid, zone, sto_reason, reportTime]
class InvalidAccessArea:
    def __init__(self, botid, level, eventType, reportTime, logStoReason):
        self.botid = botid
        self.level = level
        self.eventType = eventType
        self.reportTime = reportTime
        self.stoReason = logStoReason
    def __repr__(self):
        return repr((self.botid, self.level, self.eventType, self.reportTime, self.stoReason))

def StoReasonInvalidAreaReport(stoList, level, entry, w):
    for lastEntry in range(entry, len(stoList)):
        if (stoList[lastEntry].level == level):
            pass
        else:
            break
    stoReport = []
    botList = []
    stoListInvalidArea = StoDateTimeSort(stoList, entry, lastEntry)
    for row in range(len(stoListInvalidArea)):
            if stoListInvalidArea[row].botid not in botList:
                botList.append(stoListInvalidArea[row].botid)
                str = "Bot " + stoListInvalidArea[row].botid + " was disabled at " + \
                        stoListInvalidArea[row].reportTime + " with sto_reason: " + \
                        stoListInvalidArea[row].eventType + '\n'
                stoReport.append(str)

    r1 = "\tNumber of bots disabled-by-safety" + "{0: <5}".format(len(botList)) + " at Level: " + "{0: <3}".format(level) + \
            "Total log entries " + "{0: <5}".format(len(stoListInvalidArea))
    #print(r1)
    w.writelines('\n' + r1 + '\n')
    w.writelines(stoReport)
    return (lastEntry + 1)

def StoReasonInvalidAccessArea(log):
     stoInvalidline = []
     stoList = []
     pattern = r"UNSAFE Bot"
     try:
         wFile = open(STO_INVALID_AREA, "w+")
     except OSError:
         print("StoReasonInvalidAccessArea: Could not open file: ", STO_INVALID_AREA)
         sys.exit()
     with wFile:
         for line in log:
             #if line.find(pattern) != -1:
             if pattern in line:
                 elems = line.split()
                 stoInvalidLine = InvalidAccessArea(elems[9], \
                         elems[17], \
                         "Invalid Codeplate", \
                         StoGetTimeString(elems[0]), \
                         StoParseStoReason(elems) ) #elems[0].rsplit(TIME_RSPLIT_BG, 1)[0])
                 stoList.append(stoInvalidLine)
                 stoInvalidLine = []
         stoList = StoMultiSort(list(stoList), (('level', False), ('botid', False)))
         reportInvalidArea = "---------------Disabled-by-safety UNSAFE Bots (Bots with Invalid Codeplate)-------------"
        #  if len(stoList) > 0:
        #      print(reportInvalidArea)
         wFile.writelines(reportInvalidArea + '\n')

         for entry in stoList:
            print(f"{entry.reportTime.split('T')[0]},{entry.reportTime.split('T')[1]},{entry.botid},lvl:{entry.level},invalid_access,{entry.stoReason},{entry.lastLocTime}{entry.lastLocYear},{entry.eventTime}{entry.eventYear}")
         entry = 0
         while entry < len(stoList):
             level = stoList[entry].level
             entry = StoReasonInvalidAreaReport(stoList, level, entry, wFile)
         wFile.close()

#---------------------------------------------------------------------------------------------
"""
 Report bots which are unlocalized and hence disabled during access
 Unlocalized bots are disabled during any access
 Unlocalized bots are unsafe if any level is closed or bypassed
 From log:
    List = [botid, level, eventType,  reportTime]
    eventType = 'closure' or 'BYPASSED'
"""
#---------------------------------------------------------------------------------------------
class UnlocalizedAtLevel:
    def __init__(self, botid, level, eventType, reportTime, logStoReason):
        self.botid = '{0: <5}'.format(botid)
        self.level = level
        self.eventType = eventType
        self.reportTime = reportTime
        self.stoReason = logStoReason
    def __repr__(self):
        return repr((self.botid, self.level, self.eventType, self.reportTime, self.stoReason))

def StoReasonUnlocalizedReport(stoList, level, entry, w):
    for lastEntry in range(entry, len(stoList)):
        if (stoList[lastEntry].level == level):
            pass
        else:
            break
    stoReport = []
    botList = []
    stoReason = ' '
    stoListUnlocal = StoDateTimeSort(stoList, entry, lastEntry)
    for row in range(len(stoListUnlocal)):
        if stoListUnlocal[row].botid not in botList:
            botList.append(stoListUnlocal[row].botid)
            if stoListUnlocal[row].eventType == "BYPASSED":
                stoReason =  "found UNLOCALIZED during BYPASSED event (Key/door breached). "
            elif stoListUnlocal[row].eventType == "closure.":
                stoReason = "found UNLOCALIZED during area closure"
            else:
                stoReason = "Unknown " + stoListUnlocal[row].eventType
            str = "Bot " + stoListUnlocal[row].botid + \
                    " was disabled at " + stoListUnlocal[row].reportTime + \
                    " with sto_reason: " + stoReason + '\n'
            stoReport.append(str)

    r1 = "\tNumber of bots disabled-by-safety: " + "{0: <5}".format(len(botList)) + " at Level: " + "{0: <3}".format(level) + \
            " Total log entries: " + "{0: <5}".format(len(stoListUnlocal))
    #print(r1)
    w.writelines('\n' + r1 + '\n')
    w.writelines(stoReport)
    return (lastEntry + 1)

def StoReasonUnlocalizedAtLevel(log):
     stoLevelUnlocal = []
     stoList = []
     pattern = r"UNLOCALIZED at level"
     try:
         wFile = open(STO_UNLOCALIZED_AT_LEVEL, "w+")
     except OSError:
         print("StoReasonUnlocalizedAtLevel: Could not open file: ", STO_UNLOCALIZED_AT_LEVEL)
         sys.exit()
     with wFile:
         for line in log:
             #if line.find(pattern) != -1:
             if pattern in line:
                 elems = line.split()
                 stoLevelUnlocal = UnlocalizedAtLevel(elems[8], \
                         elems[12], \
                         elems[13], \
                         StoGetTimeString(elems[0]), \
                         StoParseStoReason(elems) ) #elems [0].rsplit(TIME_RSPLIT_BG, 1)[0])
                 stoList.append(stoLevelUnlocal)
                 stoLevelUnlocal = []
         stoList = StoMultiSort(list(stoList), (('level', False), ('botid', False)))
         reportUnlocalized = "---------------UNLOCALIZED bots disabled-by-safety during access-------------"
        #  if len(stoList) > 0:
            #  print(reportUnlocalized)
         wFile.writelines(reportUnlocalized + '\n')

         for entry in stoList:
            print(f"{entry.reportTime.split('T')[0]},{entry.reportTime.split('T')[1]},{entry.botid},lvl:{entry.level},Unlocalized,{entry.stoReason},-,-")
         entry = 0
         while entry < len(stoList):
             level = stoList[entry].level
             entry = StoReasonUnlocalizedReport(stoList, level, entry, wFile)
         wFile.close()


# List = [botid, nocomm_time, sto_reason, reportTime]
class OutOfComm:
    def __init__(self, botid, timeNoComm, eventType, reportTime, logStoReason):
        self.botid = botid
        self.timeNoComm = timeNoComm
        self.eventType = eventType
        self.reportTime = reportTime
        self.stoReason = logStoReason
    def __repr__(self):
        return repr((self.botid, self.timeNoComm, self.eventType, self.reportTime, self.stoReason))

# List = [botid, nocomm_time, sto_reason, reportTime]
def StoReasonNoCommPrint(line, stoReport):
    str = "Bot " + "{0: <5}".format(line.botid) + " lost communication for " + line.timeNoComm + \
            " was disabled at " + line.reportTime + '\n'
    stoReport.append(str)
    return

def StoReasonNoComm(log):
     stoList = []
     botList = []
     stoLineNoComm = []
     stoReport = []
     pattern = r"incommunicado for";
     try:
         wFile = open(STO_NO_COMM, "w+")
     except OSError:
         print("StoReasonNoComm: Could not open file: ", STO_NO_COMM)
         sys.exit()
     with wFile:
         for line in log:
             #if line.find(pattern) != -1:
             if pattern in line:
                 elems = line.split()
                 stoLineNoComm = OutOfComm(elems[9], \
                         elems[12], \
                         "accountant lost communication with bot", \
                         StoGetTimeString(elems[0]), \
                         StoParseStoReason(elems) ) #elems [0].rsplit(TIME_RSPLIT_BG, 1)[0])
                 stoList.append(stoLineNoComm)
                 stoLineNoComm = []
         stoNoCommList = StoDateTimeSort(stoList, 0, len(stoList))
         for row in range(len(stoNoCommList)):
             if stoNoCommList[row].botid not in botList:
                 botList.append[stoNoCommList[row].botid]
                 StoReasonNoCommPrint(stoNoCommList[row], stoReport)

         reportNocomm = "---------------Disabled-by-safety Out Of Comm Bots-------------"
         r1 = "\tNumber of bots disabled-by-safety: " + "{0: <5}".format(len(botList)) + \
                 "Number of log entries: " + "{0: <5}".format(len(stoNoCommList))
         wFile.writelines(reportNocomm + '\n')
         if (len(stoNoCommList) > 0):
            # print(reportNocomm)
            #print(r1)
            wFile.writelines(r1 + '\n')
         wFile.writelines(stoReport)
         wFile.close()

#------------------------------------------------------------------------------------------
"""
   StoPrintHelp - print usage  
"""
#------------------------------------------------------------------------------------------
def StoPrintHelp():
    print("Usage: python3 sas-sto.py [log-file]")
    print("\tDefault log-file:\t /logs/safety/scpu.log")
    print("\tScans the log-file to generate reports on disabled-by-safety bots in the following output files:")
    print("\tUnsafe level:\t", STO_UNSAFE_LEVEL)
    print("\tUnsafe aisle:\t", STO_UNSAFE_AISLE)
    print("\tUnsafe cell:\t", STO_UNSAFE_DRIVEWAY)
    print("\tUNLOCALIZED:\t", STO_UNLOCALIZED_AT_LEVEL)
    print("\tout of comms:\t", STO_NO_COMM)
    print("\tUnsafe Bot:\t", STO_INVALID_AREA)
    return

#------------------------------------------------------------------------------------------
"""
   main -  
"""
#------------------------------------------------------------------------------------------
def main():
     if len(sys.argv) == 1:
         log_file = DEFAULT_LOG_FILE 
     else:
         if ((sys.argv[1] == '-h') or (sys.argv[1] == '--help') or (len(sys.argv) > 2)):
             StoPrintHelp()
             sys.exit()
         else:
             log_file = sys.argv[1]
     if log_file.endswith('.gz'):
         cmdOpen = gzip.open
     elif log_file.endswith('.xz'):
         cmdOpen = lzma.open
     else:
         cmdOpen = open
     try:
        #  print("logFile: ", log_file)
         log = cmdOpen(log_file, 'rt', errors="ignore")
     except FileNotFoundError:
         print("sas-sto: Could not open file: ", log_file)
         sys.exit()
     with log:
         StoReasonUnsafeLevel(log)
         log.seek(0)
         StoReasonUnsafeAisle(log)
         log.seek(0)
         StoReasonUnsafeDriveway(log)
         log.seek(0)
         StoReasonInvalidAccessArea(log)
         log.seek(0)
         StoReasonUnlocalizedAtLevel(log)
         log.seek(0)
         StoReasonNoComm(log)
         log.close()

if __name__ == '__main__':
    main()

