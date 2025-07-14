import sys
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime as dt
from datetime import timedelta as delta
import re

layers = ["total","search","send","valid"]

# Regex strings for each event type
start_patterns = {
    "total" : r"Using high",
    "search" : r"Searching incomplete events",
    "send" : r"Found a valid",
    "valid" : r"Looking for"
}
end_patterns = {
    "total" : r"Macro spent.*total",
    "search" : r"Finished searching incomplete",
    "send" : r"Retriggered event",
    "valid" : r"Found a valid|Searched and"
}
height_and_color = {
    "total" : (3,'#462d26ff'),
    "search" : (11,'#395c78ff'),
    "send" : (7,'#9d312fd6'),
    "valid" : (10, '#768a88e7')
}
is_event_active = {k:False for k in layers}

def main():
    global gantt_dict
    global first_dt
    global last_dt
    global last_valid_date
    global duration_seconds
    try:
        logfile_path = sys.argv[1]
    except:
        logfile_path = "serial_test_7_14.log"
    print(f"Reading log file at {logfile_path}")
    
    # Much easier to work with a list than a filestream tbh
    content = []
    with open(logfile_path, "r") as file:
        content = file.readlines()

    gantt_dict = {k:[] for k in layers}
    first_dt = get_datetime_from_line(content[0])
    last_dt = get_datetime_from_line(content[-1])
    last_valid_date = last_dt
    duration_seconds = last_dt - first_dt

    for line in content:
        line_to_gantt_event(line)

    make_gantt_chart()

def make_gantt_chart():
    fig, gnt = plt.subplots()

    gnt.set_ylim(0,50)
    gnt.set_xlim(0,duration_seconds.total_seconds())

    gnt.set_xlabel('Seconds')
    # gnt.set_ylabel('Task ID')

    # y-axis ticks
    # tickmarks =  [100*(x+1)/(num_tasks+1) for x in range(num_tasks)]
    # gnt.set_yticks(tickmarks)
    # gnt.set_yticklabels([str(x) for x in range(num_tasks)])
    # gnt.set_yticks([15,25,35])
    # gnt.set_yticklabels(['1','2','3'])

    gnt.grid(True)

    for event_type, lst in gantt_dict.items():
        height = height_and_color[event_type][0]
        color = height_and_color[event_type][1]

        gnt.broken_barh(lst,(25-height*0.5,height),facecolors=color,
                            label=event_type)
        
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
                      ncols=2, mode="expand", borderaxespad=0.)
    plt.show()

def line_to_gantt_event(line:str):
    for event_type in layers:
        try:
            start_line = find_from_line(start_patterns[event_type],line)
            end_line = find_from_line(end_patterns[event_type],line)

            if start_line and not(is_event_active[event_type]):
                is_event_active[event_type] = True
                timestamp = get_seconds_since_start(line)
                gantt_dict[event_type].append((timestamp,1))
                # if event_type=="valid":
                #     print(f"Start valid:{line}")
            elif end_line and is_event_active[event_type]:
                is_event_active[event_type] = False
                begins = gantt_dict[event_type][-1][0]
                timestamp = get_seconds_since_start(line)
                gantt_dict[event_type][-1] = (begins,timestamp - begins)
                # if event_type=="valid":
                #     print(f"End valid:{line}")
        except:
            # print(gantt_dict["valid"])
            raise Exception(f"Caused by this line:\n{line}")
    pass

def get_seconds_since_start(line:str) -> float:
    """Gets the number of seconds since the start of the program that the line occured
    """
    moment = get_datetime_from_line(line)
    return (moment - first_dt).total_seconds()

def get_datetime_from_line(line:str):
    """Gets a datetime object from the log line
    Args:
        line (str): Line from the log file
    Returns:
        datetime object or None
    """
    regex = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}"
    datestring = find_from_line(regex,line)
    global last_valid_date
    try:
        last_valid_date = dt.strptime(datestring,"%Y-%m-%d %H:%M:%S.%f")
        return dt.strptime(datestring,"%Y-%m-%d %H:%M:%S.%f")
    except:
        return last_valid_date

def find_from_line(regex:str, line:str) -> str:
    """Just so I don't have to do all that regex stuff"""
    m = re.search(regex,line)
    if m:
        return m.group()
    else:
        return None


if __name__=="__main__":
    main()