import sys
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime as dt
from datetime import timedelta as delta
import re

layers = ["total","mutex","search","send","wait","valid"]
# global gantt_dict

# Date objects representing the start and end of the program
# first_dt = dt.now()
# last_dt = dt.now()
# duration_seconds = last_dt - first_dt

# Regex strings for each event type
start_patterns = {
    "total" : "(?<=Task )\d(?= assigned)",
    "mutex" : "(?<=TASK )\d(?=.*has.*mutex.*)",
    "search" : "(?<=TASK )\d(?=.*Searching)",
    "send" : "(?<=TASK )\d(?=.*found)",
    "wait" : "(?<=TASK )\d(?= retriggered)",
    "valid" : "(?<=TASK )\d(?= looking)"
}
end_patterns = {
    "total" : "(?<=Task )\d(?=.*all)",
    "mutex" : "(?<=TASK )\d(?=.*released.*mutex)",
    "search" : "(?<=TASK )\d(?=.*released.*mutex.*SEARCH)",
    "send" : "(?<=TASK )\d(?=.*finished SEND)",
    "wait" : "(?<=TASK )\d(?=.*waiting)",
    "valid" : "(?<=TASK )\d(?= found)"
}

height_and_color = {
    "total" : (3,'#462d26ff'),
    "mutex" : (15,'#6b6a65e7'),
    "search" : (11,'#395c78ff'),
    "send" : (7,'#9d312fd6'),
    "wait" : (6,'#ef9849'),
    "valid" : (10, '#768a88ff')
}

def main():
    global gantt_dict
    global first_dt
    global last_dt
    global last_valid_date
    global duration_seconds
    global num_tasks
    try:
        logfile_path = sys.argv[1]
    except:
        logfile_path = "better.log"
    print(f"Reading log file at {logfile_path}")
    
    # Much easier to work with a list than a filestream tbh
    content = []
    with open(logfile_path, "r") as file:
        content = file.readlines()

    num_tasks = get_num_tasks(content)
    # gantt_dict = {k:[] for k in range(num_tasks)}
    gantt_dict = {g:{k:[] for k in range(num_tasks)} for g in layers}
    first_dt = get_datetime_from_line(content[0])
    last_dt = get_datetime_from_line(content[-1])
    last_valid_date = last_dt
    # print(last_valid_date)
    duration_seconds = last_dt - first_dt
    # print((last_dt - first_dt).total_seconds()/60)
    # print(num_tasks)
    # print(gantt_dict)
    # gantt_dict["mutex"][0].append((0,5))
    # print(gantt_dict['mutex'][0])
    for line in content:
        line_to_gantt_event(line)
    
    # print(gantt_dict["total"])
    # print("hello world")
    make_gantt_chart()
    
    # gant_chart_test()

def get_num_tasks(lines) -> int:
    """Finds the number of tasks the macro created from the log
    Args:
        lines (list[str]): List of strings from readlines()
    """
    regex = "(?<=Macro will distribute work across )((.*?)(?= tasks))"
    for line in lines:
        numstring = find_from_line(regex,line)
        try:
            return int(numstring)
        except:
            continue
    return None

def line_to_gantt_event(line:str):
    """Reads a line then appends the necessary information to the gantt_dict
    Args:
        line (str): Line from log file
    """
    for event_type in layers:
        try:
            task_start = find_from_line(start_patterns[event_type],line)
            task_end = find_from_line(end_patterns[event_type],line)

            # Check if the line is the start of an event
            if task_start:
                timestamp = get_seconds_since_start(line)
                gantt_dict[event_type][int(task_start)].append((timestamp,1))
            elif task_end:
                # Get the most recently added event for the given type and task
                begins = gantt_dict[event_type][int(task_end)][-1][0]
                timestamp = get_seconds_since_start(line)
                gantt_dict[event_type][int(task_end)][-1] = (begins,timestamp - begins)
        except:
            # print(gantt_dict)
            raise Exception(f"Caused by this line: \n{line}")
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
    regex = "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}"
    datestring = find_from_line(regex,line)
    global last_valid_date
    try:
        last_valid_date = dt.strptime(datestring,"%Y-%m-%d %H:%M:%S.%f")
        return dt.strptime(datestring,"%Y-%m-%d %H:%M:%S.%f")
    except:
        return last_valid_date

def make_gantt_chart():
    fig, gnt = plt.subplots()

    gnt.set_ylim(0,100)
    gnt.set_xlim(0,duration_seconds.total_seconds())

    gnt.set_xlabel('Seconds')
    gnt.set_ylabel('Task ID')

    # y-axis ticks
    tickmarks =  [100*(x+1)/(num_tasks+1) for x in range(num_tasks)]
    gnt.set_yticks(tickmarks)
    gnt.set_yticklabels([str(x) for x in range(num_tasks)])
    # gnt.set_yticks([15,25,35])
    # gnt.set_yticklabels(['1','2','3'])

    gnt.grid(True)

    # bars
    # gnt.broken_barh(gantt_dict["mutex"][0], (tickmarks[0],9), facecolors='black')
    # for thread_ID, lst in gantt_dict["mutex"].items():
    #     gnt.broken_barh(lst,(tickmarks[thread_ID],9),facecolors='black')
    labels = set()
    for event_type, tasks in gantt_dict.items():
        for task_ID, lst in tasks.items():
            height = height_and_color[event_type][0]
            color = height_and_color[event_type][1]

            if event_type in labels:
                gnt.broken_barh(lst,(tickmarks[task_ID]-height*0.5,height),facecolors=color)
            else:
                labels.add(event_type)
                gnt.broken_barh(lst,(tickmarks[task_ID]-height*0.5,height),facecolors=color,
                            label=event_type)

            # gnt.broken_barh(lst,(tickmarks[task_ID]-height*0.5,height),facecolors=color,
            #                 label=f'{("" if event_type in labels else "_")}{event_type}')
            # labels.add(event_type)

    plt.legend()
    plt.show()
    # gnt.broken_barh([(40, 50.5)], (30, 9), facecolors =('tab:orange'))


def find_from_line(regex:str, line:str) -> str:
    """Just so I don't have to do all that regex stuff"""
    m = re.search(regex,line)
    if m:
        return m.group()
    else:
        return None


if __name__=="__main__":
    main()