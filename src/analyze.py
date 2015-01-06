#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

# analyze.py
#
# Copyright © 214 Intel Corporation
#
# Author: Quanxian Wang <quanxian.wang@intel.com>
#         Zhang Xiaoyan <zhang.xiaoyanx@intel.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

import re
import math
import xml.etree.ElementTree as ET
import collections
import copy
import sys
import os
from cairographic import Graphic

#Define macro
START_TIME = 999999999
TOTAL_INTERVAL = 0
GROUP_NUM = 3
X_AXIS_INTERVAL = 120
MAX_LEN = 1000000


class interval:

    def __init__(self):
        self.start = -1
        self.end = -1

    def __repr__(self):
        return repr(self.start)

class Analyzer:
    """
    Profile Analyzer
    It's used to read from log file and visualize the record.
    """
    def __init__(self):
        # log file's start time, will be changed (absolute real world time)
        self.start_time = START_TIME
        # total interval
        self.total_interval = TOTAL_INTERVAL
        # log file's end time
        self.end_time = TOTAL_INTERVAL
		# predefined match pattern
        self.pregex = re.compile('\[\ *(?P<hour>[0-9]+):(?P<min>[0-9]+):(?P<sec>[0-9]+)\.(?P<msec>[0-9]+)\] perf_point:' + \
                                 '(?P<name>.*)')
        self.sregex = re.compile('\[\ *(?P<hour>[0-9]+):(?P<min>[0-9]+):(?P<sec>[0-9]+)\.(?P<msec>[0-9]+)\] perf_start:' + \
                                 '(?P<name>.*)')
        self.eregex = re.compile('\[\ *(?P<hour>[0-9]+):(?P<min>[0-9]+):(?P<sec>[0-9]+)\.(?P<msec>[0-9]+)\] perf_end:' + \
                                 '(?P<name>.*)')
        self.idregex = re.compile('\[\ *(?P<hour>[0-9]+):(?P<min>[0-9]+):(?P<sec>[0-9]+)\.(?P<msec>[0-9]+)\] perf_id:' + \
                                 '(?P<name>.*)')
		# dic of events data generate from log file analysis
        self.events_dic = {}
		# dic of valid events data generate from self.events_dic
        self.new_events = {}
        # dic of client's activate(accordng to client's activate to draw graph)
        self.client_activate = {}
		# dic of different data used to represent different functions
		# the amount of time of each event in order to draw summary frame chart
        self.smooth_events = collections.OrderedDict()
		# the communication time of between each eventi in order to draw summary frame chart.
        self.comm_events = collections.OrderedDict()
		# the whole time of each cycle in order to draw fps chart.
        self.time_dic = collections.OrderedDict()
        # list of all event
        self.event_list = []
        # event list to calculate fps
        self.fps_event_list = []
        # event list to calculate frame summary
        self.smooth_event_list = []
        # client_id list generate from log file
        self.client_id_list = []
        # log files list
        self.log_files = []
        # happened events
        self.happened_clients = []
        self.fps_events_colors = []
        # segmentation point
        self.seg_point = None
        # time list of segmentation point
        self.seg_point_time = []
        # sample rate
        self.sample_rate = None

        # predefined color hexcode list
        self.color_table = {"blue": (0.0, 0.0, 1.0),
                             "cyan": (0.0, 1.0, 1.0),
                             "magenta": (1.0, 0.0, 1.0),
                             "orange": (1.0, 0.5, 0.0),
                             "maroon": (0.5, 0.0, 0.0),
                             "purple": (1.0, 0.2, 1.0),
                             "green": (0.0, 0.5, 0.0),
							 "red": (1.0, 0.0, 0.0),
							 "lime": (0.0, 1.0, 0.0),
							 "navy": (0.0, 0.0, 0.5),
							 "yellow": (1.0, 1.0, 0.0),
							 "black": (0.0, 0.0, 0.0)}

    def get_client_activate(self):
        return self.client_activate

    def get_happened_clients(self):
        return self.happened_clients

    def get_happened_clients_colors(self):
        return self.fps_events_colors

    def updateClient(self, clients):
        for id in self.client_id_list:
            self.client_activate['client'+'_'+id] \
                = clients['client'+'_'+id]

    def draw_smooth(self, name, show_start, show_end, width, height, output_dir=None):
        """
        Note:draw frame summary graph
        Args:
            show_start: the start time to show
            show_end:   the end time to show
            output_dir: the output directory of fps.txt
        Input:self.smooth_events, self.comm_events
        Output:Graphic object
        """
        if len(self.smooth_events.keys()) == 0:
            return None

        st_dic = collections.OrderedDict()

        for cid in self.client_id_list:
            if 'client'+'_'+cid not in self.client_activate \
                    or self.client_activate['client'+'_'+cid] != True:
                continue

            st_dic[cid] = collections.OrderedDict()
            data = []
            color_index = 0
            colors = []
            x_labels = []
            sum_total = 0
            se_len = len(self.smooth_event_list)
            for i in range(se_len):
                total = 0
                ename = self.smooth_event_list[i]
                data_len = len(self.smooth_events[cid][ename])
                for number in self.smooth_events[cid][ename]:
                    total += number
                st_dic[cid][ename] = total/data_len
                if i < se_len - 1:
                    cname = 'comm' + str(i)
                    comm_val = self.comm_events[cid][cname]
                    if comm_val > 0.1:
                        st_dic[cid][cname]  = comm_val
	
            # get sum_total
            for ename in st_dic[cid]:
                sum_total += st_dic[cid][ename]

            sum_total = float("{0:.2f}".format(sum_total))
            fps = float("{0:.2f}".format(1000 / sum_total))
            str1 = 'total_time = ' + str(sum_total) + 'ms'\
                   + '\n' + 'fps = ' + str(fps) + 'fps'

            if output_dir == None:
                output_dir = '.'
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)
            fd = open(output_dir + '/fps.txt', 'w')
            fd.write(str1)
            fd.close()

            for ename in st_dic[cid].keys():
                x_labels.append(ename)

            for i in range(len(x_labels)):
                color_index = color_index % (len(self.color_table))
                colors.append(self.color_table.values()[color_index])
                color_index += 1

            data = st_dic[cid]
            smooth_chart = Graphic(name, data, width, 
                                   height, x_labels=x_labels,
                                   axis=True, grid=True,
                                   background="white", series_colors=colors)
            smooth_chart.render()
            smooth_chart.render_smooth()
        return smooth_chart

    def draw_fps(self, name, show_start, show_end, width, height, output_dir=None):
        """
        Note:draw fps graph
        Args:
            show_start: the start time to show
            show_end:   the end time to show
        Input:self.time_dic
        Output:Graphic object
        """

        if len(self.time_dic) == 0:
            return None

        # change to relative time
        rel_start = show_start - self.start_time
        rel_end = show_end - self.start_time

        for cid in self.client_id_list:
            if 'client' + '_' + cid not in self.client_activate or \
                self.client_activate['client' + '_' + cid] == False:
                continue

            client_colors = []
            time_list = []
            clients = []
            x_labels = []
            self.happened_clients = []
            time_list = self.time_dic[cid]
            FPS = collections.OrderedDict()

            x_axis_num = int(math.floor(width / X_AXIS_INTERVAL))
            x_interval = int(math.floor((rel_end - rel_start) 
			             / x_axis_num))
            for i in range(x_axis_num + 1):
                x_labels.append("{0}ms".format(rel_start + i * x_interval))

            for i in range(len(time_list)):
                if time_list[i].start < rel_start:
                    continue
                if time_list[i].end > rel_end:
                    break
                if time_list[i].end == -1:
                    FPS[time_list[i].start] = -1
                    continue
                # change ms value to FPS value
                FPS[time_list[i].start] = 1000/time_list[i].end

            clients.append('client' + '_' + cid)
            client_colors.append(self.color_table["blue"])

            # FPS is defined for every client id
            # lets calculate start, end, interval and labels.
            fps_chart = Graphic(name, FPS, width, height, rel_end,
                                x_labels=x_labels, axis=True, grid=True,
                                background="white", series_colors=client_colors)
            fps_chart.render()
            fps_chart.render_fps()
            self.happened_clients = clients
            self.fps_events_colors = client_colors

        return fps_chart

    def create_interval(self, start, end):
        itv = interval()
        itv.start = start
        itv.end = cycle
    
    def sample_data(self, time_list = None, start = 0, end = 0):
        if not time_list:
           return []

        rate = float(self.sample_rate) * (end-start)
        rate = int("{0:.0f}".format(rate))

        if rate > 0:
            del time_list[start:start+rate]
            del time_list[end-rate*2:end-rate]

    def calculate_fps(self):
        """
		Input:self.time_dic = {event_name:{id:time}}
		Output:self.time_dic
		Data Formate:
        """
        for cid in self.client_id_list:
            time_list = []
            number = 0
            index = 0
            offset = 0
            rate = 0
            event1 = self.fps_event_list[0]
            event2 = self.fps_event_list[-1]
            seg_len = len(self.seg_point_time)
            for event in self.new_events[cid]:
                if event[0] == event1:
                    start = event[1]
                    continue

                if event[0] == event2:
                    end = event[1]
                    itv = interval()
                    itv.start = start
                    itv.end = end - start
                    number += 1

                    if seg_len > 0 and seg_len > index:
                        seg_time = self.seg_point_time[index]
                        if start >= seg_time:
                            """
                            Before insert segment point, sample the time data
                            """
                            new_list = sorted(time_list[offset:len(time_list)], key=lambda e:e.end)
                            self.sample_data(new_list, 0, len(new_list))
                            new_list.sort(key=lambda e:e.start)
                            if offset > 0:
                                time_list = time_list[0:offset] + new_list
                            else:
                                time_list = new_list

                            itv2 = interval()
                            itv2.start = seg_time
                            itv2.end = -1
                            index += 1
                            time_list.append(itv2)
                            offset = len(time_list)
                    time_list.append(itv)

            if seg_len > 0 and self.seg_point_time[-1] not in [e.start for e in time_list]:
                new_list = sorted(time_list[offset:len(time_list)], key=lambda e:e.end)
                self.sample_data(new_list, 0, len(new_list))
                new_list.sort(key=lambda e:e.start)
                if offset > 0:
                    time_list = time_list[0:offset] + new_list
                else:
                    time_list = new_list

                itv = interval()
                itv.start = self.seg_point_time[-1]
                itv.end = -1
                time_list.append(itv)

            self.update2rel(time_list)
            self.time_dic[cid] = time_list

    def process_id(self, match):
        if not match:
            return
         
        ename = match.group('name')
        if ename not in self.client_id_list:
            self.client_id_list.append(ename)

    def process_point(self, match):
        if not match:
            return

        ename = match.group('name')
        etime = float(match.group('hour')) * 60 * 60 * 1000 +\
                float(match.group('min')) * 60 * 1000 +\
                float(match.group('sec')) * 1000 +\
                float(match.group('msec'))/1000
        if self.seg_point == ename:
            self.seg_point_time.append(float(etime))

    def process_timestr(self, match=None, start=True):
        if not match:
            return

        ename_ori = match.group('name')
        etime = float(match.group('hour')) * 60 * 60 * 1000 +\
                float(match.group('min')) * 60 * 1000 +\
                float(match.group('sec')) * 1000 +\
                float(match.group('msec'))/1000
        id_index = ename_ori.find('_')
        if id_index == -1:
            eid = '0'
            ename = ename_ori
        else:
            ename = ename_ori[:id_index]
            eid = ename_ori[id_index+1:]

        if start:
            if self.seg_point == ename:
                self.seg_point_time.append(float(etime))

        if eid not in self.events_dic:
            self.events_dic[eid] = []

        if start:
            new_event = {'name':ename, 'time':float(etime), 'start':True}
        else:
            new_event = {'name':ename, 'time':float(etime), 'start':False}

        self.events_dic[eid].append(new_event)

    def parse_log_file(self):
        """
        parse log file.
		Return:self.events_dic
        """
        color_index = 0
        for debug_file in self.log_files:
            with open(debug_file) as inf:
                for line in inf:
                    # Find the match
                    match = self.idregex.match(line)
                    if match is not None:
                        self.process_id(match)
                        continue

                    match = self.pregex.match(line)
                    if match is not None:
                        self.process_point(match)
                        continue

                    match = self.sregex.match(line)
                    if match is not None:
                        self.process_timestr(match, True)
                        continue

                    match = self.eregex.match(line)
                    if match is not None:
                        self.process_timestr(match, False)
                        continue

    def parse_config_file(self, configfile, logfile):
        """
        parse config xml file, it shows how to parse log file.
        parse log file then according to the xml instruction.
        """
        if configfile == None:
            configfile = '../config/config.xml'

        if not os.path.exists(configfile):
            return

        self.root = ET.parse(configfile).getroot()

        config_tags = {"segmentation_point":("point", []),
                    "event_item":("event", []),
                    "fps_item":("fps", []),
                    "smooth_item":("smooth", []),
                    "sample_rate":("rate", []),
                    "profile":("file", [])}

        for key in config_tags.keys():
            debug = self.root.find(key)
            if debug is None:
                continue

            subitems = debug.getchildren()
            for item in subitems:
                if item.tag == config_tags[key][0]:
                    config_tags[key][1].append(item.text)

        # convert config to global values
        if len(config_tags["segmentation_point"][1]) > 0:
            self.seg_point = config_tags["segmentation_point"][1][0]
        self.event_list.extend(config_tags["event_item"][1])
        self.fps_event_list.extend(config_tags["fps_item"][1])
        self.smooth_event_list.extend(config_tags["smooth_item"][1])
        if len(config_tags["sample_rate"][1]) == 0:
            self.sample_rate = 0
        else:
            self.sample_rate = config_tags["sample_rate"][1][0]

        if logfile != None:
            self.log_files.append(logfile)
        else:
            self.log_files.extend(config_tags["profile"][1])
 
    def init_client_activate(self):
        first = self.client_id_list[0]
        self.client_activate['client' + '_' + first] = True
        for cid in self.client_id_list[1:]:
            self.client_activate['client' + '_' + cid] = False

    def get_smooth_time(self):
        """
		Note:According to valid data(self.events_dic) 
		     to generate the smooth data(self.smooth_events)
		Input:self.events_dic
		Return:self.smooth_events
		Data Format:self.smooth_events = {event_name:{client_id:time}}
        """

        event_len = MAX_LEN
        for cid in self.client_id_list:
            self.smooth_events[cid] = {}
            for event in self.new_events[cid]:
                name = event[0]
                number = event[2] - event[1]
                if name not in self.smooth_events[cid].keys():
                    self.smooth_events[cid][name] = []
                self.smooth_events[cid][name].append(number)

            # merge the data based on the sample rate
            for name in self.smooth_events[cid].keys():
                self.smooth_events[cid][name].sort()
                self.sample_data(self.smooth_events[cid][name], 0, \
                     len(self.smooth_events[cid][name]))

    def get_comm_time(self):
        """
		Note:According to valid data(self.events_dic) 
		     to generate the communication data(self.comm_events)
		Input:self.events_dic
		Return:self.comm_events
		Data Format:self.comm_events = {client_id:{event_name:time}}
        """
        for cid in self.client_id_list:
            self.comm_events[cid] = collections.OrderedDict()
            total = 0
            comm_time = 0
            comm_len = 0
            for i in range(0, len(self.smooth_event_list) - 1):
                fname = self.smooth_event_list[i]
                sname = self.smooth_event_list[i+1]
                fst_end = [e[2] for e in self.new_events[cid] \
                                  if e[0] == fname]
                sec_start = [e[1] for e in self.new_events[cid] \
                                  if e[0] == sname]
                comm_list = []
                if len(fst_end) == 0 or len(sec_start) == 0:
                    print 'smooth invalid data!'
                    sys.exit(-1)
                comm_len = len(fst_end) > len(sec_start) and \
                           len(sec_start) or len(fst_end)
                for j in range(comm_len):
                    number = sec_start[j] - fst_end[j]
                    comm_list.append(number)

                comm_list.sort()
                self.sample_data(comm_list, 0, len(comm_list))

                for number in comm_list:
                    total += number
                if len(comm_list) > 0:
                     comm_time = total / len(comm_list)
                self.comm_events[cid]['comm' + str(i)] = comm_time

    def clean_up(self):
        # Clean up data unused
        for cid in self.events_dic.keys():
            # clean up unsed client id
            if cid not in self.client_id_list and cid != '0':
			    del self.events_dic[cid]
			    continue

            # clean up unused event
            event_len = len(self.events_dic[cid])
            i = 0
            while i < event_len:
                event = self.events_dic[cid][i]
                if event['name'] not in self.event_list:
                    del self.events_dic[cid][i]
                    event_len -= 1
                    continue
                i += 1

        for cid in self.client_id_list:
            if cid not in self.events_dic.keys():
			    index = self.client_id_list.index(cid)
			    del self.client_id_list[index]

    def merge_server(self):
        # merge weston server data with client data
        events = self.events_dic['0']
        for cid in self.client_id_list:
            if cid == '0':
                continue

            self.events_dic[cid].extend(events)
            self.events_dic[cid].sort(key=lambda e: e['time'])

    def form_new_dic(self):
        """
        Form new event dictionary
        """
        for cid in self.client_id_list:
            self.new_events[cid] = []

        for cid in self.client_id_list:
            for i in range(len(self.events_dic[cid])):
                event = self.events_dic[cid][i]
                if event['start'] == True:
                    new_event = (event['name'], event['time'], -1)
                    self.new_events[cid].append(new_event)
                    continue

                if event['start'] == False:
                    # find the last event which end is -1
                    event_len = len(self.new_events[cid])
                    if event_len == 0:
                        continue

                    i = 1
                    while i < (event_len - 1):
                        e1 = self.new_events[cid][-i]
                        if e1[0] == event['name'] and e1[2] != -1:
                            break
                        i += 1

                    while i > 0:
                        e1 = self.new_events[cid][-i]
                        if e1[0] == event['name'] and e1[2] == -1:
                            new_event = (e1[0], e1[1], event['time'])
                            del self.new_events[cid][-i]
                            self.new_events[cid].append(new_event)
                        i -= 1

            # sort self.new_events
            self.new_events[cid].sort(key=lambda e:e[1])

    def build_complete_dic(self):
        """
        Form a complete event dictionary
        """
        elen = len(self.event_list) 
        for cid in self.client_id_list:
            ecount = len(self.new_events[cid])
            j = 0
            index = 0
            while j < ecount:
                if self.new_events[cid][j][0] == self.event_list[index]:
                    index += 1
                    index = index % elen
                    j += 1
                else:
                    del self.new_events[cid][j]
                    ecount -= 1
        for cid in self.new_events.keys():
            if len(self.new_events[cid]) == 0:
                del self.new_events[cid]
                index = self.client_id_list.index(cid)
                del self.client_id_list[index]

    def get_valid_data(self):
        """
		Note:according to the first event in 
		     self.event_list(like 'client', self.event_list 
			 according to config.xml, the order of the list is 
			 the order of the events), rule out the error data.
		Input:original data:self.events_dic
		Return:valid data:self.events_dic
		data format:self.events_dic = {id:[event]}
                event = {'name':event_name, 'start':start_time, 'end':end_time}
        """

        self.clean_up()
        self.merge_server()
        self.form_new_dic()
        # build a complate event dic
        self.build_complete_dic()
        self.init_client_activate()
        self.get_startend_time()

    def get_startend_time(self):
        """
		Note:get the start time of log files.
		Input:self.events_dic
		Output:self.start_time
        """
        for cid in self.client_id_list:
            if len(self.events_dic[cid]) <= 0:
                continue

            start_time = self.new_events[cid][0][1]
            end_time = self.new_events[cid][-1][2]
            if self.start_time > start_time:
               self.start_time = start_time
            if self.end_time < end_time:
               self.end_time = end_time 

        for time in self.seg_point_time:
            if time < self.start_time:
                self.start_time = time

        for time in self.seg_point_time:
            if time > self.end_time:
                self.end_time = time

        self.total_interval = self.end_time

    def update2rel(self, time_list):
        """
        all event time is decreased by start time
        """
        for event in time_list:
            event.start -= self.start_time

    def init(self, configfile, logfile):
        """initialize start time and parse config file"""
        self.parse_config_file(configfile, logfile)
        self.parse_log_file()
        if len(self.client_id_list) == 0:
          #  self.client_id_list.append('0')
            self.client_id_list.extend(self.events_dic.keys())

        # filer the all data to be valid
        if len(self.events_dic.keys()) == 0:
            print 'logfile do not have valid data!'
            sys.exit(-1)
        self.get_valid_data()

        if len(self.smooth_event_list) > 0:
            self.get_smooth_time()
            self.get_comm_time()

        if len(self.fps_event_list) != 0:
            self.time_dic = {}
            self.calculate_fps()
