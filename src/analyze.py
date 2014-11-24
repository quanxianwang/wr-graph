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
FPS = 60
MAX_TIME = 500
START_TIME = 999999999
SHOW_START = 0
SHOW_END = 4000
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


class option:

    def __init__(self, name):
        self.name = name
        self.count = -1


class interval_opt(option):

    def __init__(self, name, size):
        option.__init__(self, name)
        self.events = [interval() for i in range(size)]
        self.activate = True
        self.color = "orange"


class Analyzer:
    """
    Profile Analyzer
    It's used to read from log file and visualize the record.
    """
    def __init__(self):
        # standard FPS
        self.FPS = FPS
        # max record time is 10 seconds
        self.MAX_TIME = MAX_TIME

        # log file's start time, will be changed (absolute real world time)
        self.START_TIME = START_TIME
        # showing interval's start time (relative)
        self.SHOW_START = SHOW_START
        # showing interval's end time
        self.SHOW_END = SHOW_END
        # total interval
        self.TOTAL_INTERVAL = TOTAL_INTERVAL
        # predefined match pattern
        self.pregex = re.compile('\[\ *(?P<time>[0-9]+\.[0-9]+)\]profiling_point:'
                      + '(?P<name>.*)')
        self.sregex = re.compile('.*\[\ *(?P<time>[0-9]+\.[0-9]+)\]profiling_start:'
                      + '(?P<name>.*)')
        self.eregex = re.compile('.*\[\ *(?P<time>[0-9]+\.[0-9]+)\]profiling_end:'
                      + '(?P<name>.*)')
        self.idregex = re.compile('.*\[\ *(?P<time>[0-9]+\.[0-9]+)\]profiling_id:'
                      + '(?P<name>.*)')
        self.events_dic = {}
        # dic of events's activate(accordng to events's activate to draw fps)
        self.events_activate = {}
        # dic of smooth_events's activate(accordng to smooth_events's activate to draw smooth)
        self.smooth_activate = {}
		# list of time frame events
        self.smooth_events = collections.OrderedDict()
        self.comm_events = collections.OrderedDict()
        self.time_dic = collections.OrderedDict()
        # offset of first event in zoomed chart
        self.event_list = []
        self.fps_event_list = []
        self.smooth_event_list = []
        self.client_id_list = []
        # log files
        self.log_files = []
        #happened events
        self.happened_events_fps = []
        self.fps_event_colors = []
        self.seg_point = None
        self.seg_point_time = []
        self.seg_point_list = []
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

    def get_fps_event_list(self):
        event_list = collections.OrderedDict()
        if len(self.events_activate) == 0:
            return event_list
        for id in self.client_id_list:
            event_list['client'+'_'+id] \
					= self.events_activate['client'+'_'+id]
        return event_list

    def get_happened_events_fps(self):
        return self.happened_events_fps

    def get_fps_event_colors(self):
        return self.fps_event_colors

    def updateFpsEvents(self, events):
        for id in self.client_id_list:
            self.events_activate['client'+'_'+id] \
					= events['client'+'_'+id]

    def updateSmoothEvents(self, events):
        for id in self.client_id_list:
            self.smooth_activate['client'+'_'+id] \
					= events['client'+'_'+id]

    def draw_smooth(self, name, show_start, show_end, width, height, output_dir=None):
        """
		Note:draw the smooth graphic
        Args:
            show_start: the start time to show
            show_end:   the end time to show
		Input:self.smooth_events
		Output:Smooth object
        """
        if len(self.smooth_events.keys()) == 0:
            return None
        for id in self.client_id_list:
            data = []
            if 'client'+'_'+id in self.smooth_activate \
					and self.smooth_activate['client'+'_'+id]==True:
                color_index = 0
                colors = []
                x_labels = []
                events = []
                events.append('client' + '_' + id)
                smoothtime_dic = collections.OrderedDict()
                smoothtime_dic[id] = collections.OrderedDict()
                sum_total = 0
                for i in range(len(self.smooth_event_list)):
                    event_len = len(self.smooth_events
						            [self.smooth_event_list[i]][id])
                    event = self.smooth_event_list[i]
                    total = 0
                    for j in range(event_len):
                        total += self.smooth_events[event][id][j]
                    smoothtime_dic[id][event] = (total / event_len)
                    sum_total += smoothtime_dic[id][event]
                    if i < len(self.smooth_event_list) - 1:
                        event_comm = self.comm_events[id].keys()[i]
                        if self.comm_events[id][event_comm] > 0.05:
                            smoothtime_dic[id][event_comm] \
								    = self.comm_events[id][event_comm]
                            sum_total += smoothtime_dic[id][event_comm]
				
                sum_total = float("{0:.2f}".format(sum_total))
                fps = float("{0:.2f}".format(1000 / sum_total))
                str1 = 'total_time = ' + str(sum_total) + 'ms'\
						+ '\n' + 'fps = ' + str(fps) + 'fps'
                if output_dir == None:
                    output_dir = '.'
                fd = open(output_dir + '/fps.txt', 'w')
                fd.write(str1)
                fd.close()
                for i in range(len(smoothtime_dic[id].keys())):
                    event_name = smoothtime_dic[id].keys()[i]
                    x_labels.append(event_name)
                for i in range(len(x_labels)):
                    color_index = color_index % (len(self.color_table))
                    colors.append(self.color_table.values()[color_index])
                    color_index += 1
            else:
                continue

            data = smoothtime_dic[id]
            smooth_chart = Graphic(name, data, width, 
					              height, x_labels=x_labels, 
								  axis=True, grid=True, 
								  background="white", series_colors=colors)
            smooth_chart.render()
            smooth_chart.render_smooth()
        return smooth_chart

    def draw_fps(self, name, show_start, show_end, width, height, output_dir=None):
        """
		Input:self.time_dic
		Output:Graphic instance
		"""
        
        if len(self.time_dic) == 0:
            return None
        show_start -= self.START_TIME
        show_end -= self.START_TIME

        for id in self.client_id_list:
            time_list = []
            colors = []
            events = []
            x_labels = []
            group_time = 0
            self.happened_events_fps = []
            count = 0
            accum = 0
            time_list = self.time_dic[id]
            FPS = collections.OrderedDict()
            first = 0
            time = 0
            if 'client' + '_' + id in self.events_activate \
					and self.events_activate['client' + '_' + id] == True:
                x_axis_num = int(math.floor(width / X_AXIS_INTERVAL))
                x_interval = int(math.floor((show_end - show_start) 
			             / x_axis_num))
                for i in range(x_axis_num + 1):
                    x_labels.append("{0}ms".format(show_start + i * x_interval))

                group_time = (show_end / x_axis_num) / x_axis_num / x_axis_num / x_axis_num
                group_time = 3
           
                for i in range(len(time_list)):
                    if time_list[i].start < show_start:
                        continue
                    if time_list[i].end > show_end:
                        break
                    if time_list[i].end == -1:
                        FPS[time_list[i].start] = time_list[i].end
                        count = 0
                        accum = 0
                        first = 0
                        time = 0
                        continue
                    time_list[i].end = 1000/time_list[i].end
                    accum += time_list[i].end
                    count += 1
                    if first == 0:
                        time = 0
                        first = 1
                    else:
                        time += (time_list[i].start - time_list[i-1].start)
                    if time > group_time:
                        value = accum / count
                        FPS[time_list[i - count + 1].start] = value
                        count = 0
                        accum = 0
                        time = 0

                events.append('client' + '_' + id)
                colors.append(self.color_table["blue"])
            fps_chart = Graphic(name, FPS, width, height, show_end,
                                x_labels=x_labels, axis=True, grid=True,
                                background="white", series_colors=colors)
            fps_chart.render()
            fps_chart.render_fps()
            self.happened_events_fps = events
            self.fps_event_colors = colors
        return fps_chart

    def calculate_fps(self):
        """
		Input:self.time_dic = {event_name:{id:time}}
		Output:self.time_dic
		Data Formate:
        """
        time_list = []
        total = 0
        number = 0
        index = 0
        offset = 0
        rate = 0
        event1 = self.fps_event_list[0]
        event2 = self.fps_event_list[-1]
        for client_id in self.client_id_list:
            event_len = len(self.events_dic[event1][client_id].events)
            self.time_dic[client_id] = []
            for i in range(event_len):
                start = self.events_dic[event1][client_id].events[i].start
                end = self.events_dic[event2][client_id].events[i].start
                cycle = end - start
                total += cycle
                number += 1
                itv = interval()
                itv.start = start
                itv.end = cycle

                if len(self.seg_point_time) > 0:
                    seg_time = self.seg_point_time[index]
                    if start >= seg_time:
                        lens = len(time_list) - offset
                        rate = float(self.sample_rate) * lens
                        rate = int("{0:.0f}".format(rate))
                        time_list = time_list[0:offset] + \
								    sorted(time_list[offset:len(time_list)],\
									       key=lambda e:e.end)
                        if rate > 0:
                            del time_list[offset : rate+offset]
                            del time_list[-rate:]
                        time_list = time_list[0:offset] + \
								    sorted(time_list[offset:len(time_list)], \
									       key=lambda e:e.start)
                        itv2 = interval()
                        itv2.start = seg_time
                        itv2.end = -1
                        index += 1
                        time_list.append(itv2) 
                        offset = len(time_list)
                time_list.append(itv) 

            if self.seg_point_time[-1] not in [e.start for e in time_list]:
                itv = interval()
                itv.start = self.seg_point_time[-1]
                itv.end = -1
                time_list.append(itv)
            self.time_dic[client_id] = time_list

    def parse_log_file(self):
        """
        parse log file.
		Return:self.events_dic
        """
        color_index = 0
        for debug_file in self.log_files:
            with open(debug_file) as inf:
                count_line=0
                for line in inf:
                    count_line+=1
                    if count_line >= self.FPS * self.MAX_TIME:
                        break
                    match = self.idregex.match(line)
                    if match is not None:
                        if len(match.groups()) == 2:
                            client_id = match.group('name')
                            event_time = match.group('time')
                            if client_id not in self.client_id_list:
                                self.client_id_list.append(client_id)
                    match = self.sregex.match(line)
                    if match is not None:
                        if len(match.groups()) == 2:
                            event_name_ori = match.group('name')
                            event_time = match.group('time')
                            id_index = event_name_ori.find('_')
                            if id_index == -1:
                                event_id = '0'
                                event_name = event_name_ori
                            else:
                                event_name = event_name_ori[:id_index]
                                event_id = event_name_ori[id_index+1:]
                            if self.seg_point == event_name:
                                self.seg_point_time.append(float(event_time))
                            if event_name not in self.events_dic:
                                self.events_dic[event_name] = {}
                            if event_id not in self.events_dic[event_name]:
                                color_index = (color_index + 1) \
                                                 % len(self.color_table)
                                opt = interval_opt(event_name, 
										           self.FPS * self.MAX_TIME)
                                self.events_dic[event_name][event_id] = opt
                            event = self.events_dic[event_name][event_id]
                            event.count += 1
                            event.events[event.count].start = float(event_time)
                    # match predefined time interval pattern (end)
                    match = self.eregex.match(line)
                    if match is not None:
                        if len(match.groups()) == 2:
                            event_name_ori = match.group('name')
                            event_time = match.group('time')
                            id_index = event_name_ori.find('_')
                            if id_index == -1:
                                event_id = '0'
                                event_name = event_name_ori
                            else:
                                event_name = event_name_ori[:id_index]
                                event_id = event_name_ori[id_index+1:]
                            if event_name in self.events_dic:
                                if event_id in self.events_dic[event_name]:
                                    # event should has been added
                                    event = self.events_dic[event_name][event_id]
                                    for i in range(0, event.count+1):
                                        if event.events[i].end is -1:
								            event.events[i].end = float(event_time)

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
        self.seg_point = config_tags["segmentation_point"][1][0]
        self.event_list.extend(config_tags["event_item"][1])
        self.fps_event_list.extend(config_tags["fps_item"][1])
        self.smooth_event_list.extend(config_tags["smooth_item"][1])
        self.sample_rate = config_tags["sample_rate"][1][0]

        if logfile != None:
            self.log_files.append(logfile)
        else:
            self.log_files.extend(config_tags["profile"][1])
 
    def check_fps(self):
        """
        according to self.events_dic 
		to generate the self.time_dic(be used to draw fps)
		Return:self.time_dic
        """
        first = 0
        for id in self.client_id_list:
            if first == 0:
                self.events_activate['client' + '_' + id] = True
                first = 1
            else:
                self.events_activate['client' + '_' + id] = False

    def get_smooth_time(self):
        """
		Note:According to valid data(self.events_dic) 
		     to generate the smooth data(self.smooth_events)
		Input:self.events_dic
		Return:self.smooth_events
		Data Format:self.smooth_events = {event_name:{client_id:time}}
        """

        event_len = MAX_LEN
        for id in self.client_id_list:
            #for event in self.smooth_event_list:
            #    if event_len > self.events_dic[event][id].count:
            #      event_len = self.events_dic[event][id].count
            ll = len(self.smooth_event_list)
            for i in range(ll):
                self.smooth_events[self.smooth_event_list[i]] = {}
                self.smooth_events[self.smooth_event_list[i]][id] = [] 
                name = self.smooth_event_list[i]
                event_len = len(self.events_dic[name][id].events)
                for j in range(event_len): 
                    number = float(self.events_dic[name][id].events[j].end) \
					         - float(self.events_dic[name][id].events[j].start)
                    self.smooth_events[name][id].append(number)
                self.smooth_events[name][id].sort()
                lens = len(self.smooth_events[name][id])
                rate = float(self.sample_rate) * lens
                rate = int("{0:.0f}".format(rate))
                del self.smooth_events[name][id][0:rate]
                del self.smooth_events[name][id][-rate:]
				
    
    def get_comm_time(self):
        """
		Note:According to valid data(self.events_dic) 
		     to generate the communication data(self.comm_events)
		Input:self.events_dic
		Return:self.comm_events
		Data Format:self.comm_events = {client_id:{event_name:time}}
        """
        for id in self.client_id_list:
            self.comm_events[id] = collections.OrderedDict()
            for i in range(0, len(self.smooth_event_list) - 1):
                comm_list = []
                name = self.smooth_event_list[i]
                event_len = len(self.events_dic[name][id].events)
                total = 0
                lens = 0
                comm_first_end = []
                comm_first_end = [e.end for e in 
				                     self.events_dic[self.event_list[i]][id].events]
                comm_second_start = []
                comm_second_start = [e.start for e in 
				                        self.events_dic[self.event_list[i+1]][id].events]
                for j in range(event_len):
                    number = comm_second_start[j] - comm_first_end[j]
                    comm_list.append(number)
                comm_list.sort()
                lens = len(comm_list)
                rate = float(self.sample_rate) * lens
                rate = int("{0:.0f}".format(rate))
                del comm_list[0:rate]
                del comm_list[-rate:]
                lens = len(comm_list)
                for number in comm_list:
                    total += number
                comm_time = total / lens
                self.comm_events[id]['comm' + str(i)] = comm_time
       
            
    def get_valid_data(self):
        """
		Note:according to the first event in 
		     self.event_list(like 'client', self.event_list 
			 according to config.xml, the order of the list is 
			 the order of the events), rule out the error data.
		Input:original data:self.events_dic
		Return:valid data:self.events_dic
		data format:self.events_dic = {event_name:{id:time}}
        """
        for event in self.events_dic.keys():
            if event not in self.event_list:
                del self.events_dic[event]
                continue
            for client_id in self.events_dic[event].keys():
                if client_id == '0':
                    continue
                if client_id not in self.client_id_list:
                    del self.events_dic[event][client_id]

        for id in self.client_id_list:
            self.smooth_activate['client'+'_'+id] = True
            for i in range(0, len(self.event_list)-1):
                first = self.event_list[i]
                if id not in self.events_dic[first].keys() and \
						'0' in self.events_dic[first].keys() and id != '0':
					self.events_dic[first][id] = []
					self.events_dic[first][id] = copy.deepcopy(
					                                     self.events_dic[first]['0'])
                second = self.event_list[i+1]
                event_len = self.events_dic[first][id].count
                count = 0
                num = 0
                if id not in self.events_dic[second].keys() and \
						'0' in self.events_dic[second].keys() and id != '0':
					self.events_dic[second][id] = []
					self.events_dic[second][id] = copy.deepcopy(
							                              self.events_dic[second]['0'])

                if event_len < self.events_dic[second][id].count:
					event_len = self.events_dic[second][id].count

                if id == '0' and '0' not in self.events_dic[second].keys():
					self.events_dic[second][id] = []
				  	event_len = self.events_dic[second][id].count
                while num < event_len:
                    if self.events_dic[first][id].events[count].start == -1:
                        del self.events_dic[second][id].events[count : 
								    self.events_dic[second][id].count]
                        self.events_dic[second][id].count \
								-= (self.events_dic[second][id].count - count) 
                        break
                    elif self.events_dic[second][id].events[count].start == -1:
                        del self.events_dic[first][id].events[count : 
								    self.events_dic[first][id].count]
                        self.events_dic[first][id].count \
								-= (self.events_dic[first][id].count - count) 
                        break
                    elif self.events_dic[first][id].events[count].start \
						     < self.events_dic[second][id].events[count].start:
                        if self.events_dic[first][id].events[count+1].start \
						       > self.events_dic[second][id].events[count].start:
                            if self.events_dic[first][id].events[count+1].start \
							       < self.events_dic[second][id].events[count+1].start \
							           or self.events_dic[second][id].events[count+1].start == -1:
                                count += 1
                                num += 1
                            else:
                                index = count
                                while self.events_dic[second][id].events[index].start \
									      < self.events_dic[first][id].events[count+1].start:
                                    index += 1
                                #del self.events_dic[second][id].events[count:index-1]
                                del self.events_dic[second][id].events[count+1:index]
                                self.events_dic[second][id].count -= (index - count - 1) 
                                num += (index - count - 1)
                        else:
                            index = count
                            if self.events_dic[first][id].events[count+1].start == -1:
                                break
                            while self.events_dic[first][id].events[index].start \
								      < self.events_dic[second][id].events[count].start \
								          and self.events_dic[first][id].events[index].start != -1:
                                index += 1
                            for k in range(0, i):
                                del self.events_dic[self.event_list[k]][id].events[count+1:index]
                                self.events_dic[self.event_list[k]][id].count -= (index - count - 1) 
                            del self.events_dic[first][id].events[count+1:index]
                            self.events_dic[first][id].count -= (index - count - 1) 
                            num += (index - 1 - count)
                    else:
                        index = count
                        while self.events_dic[second][id].events[index].start < \
						          self.events_dic[first][id].events[count].start:
                            index += 1
                        del self.events_dic[second][id].events[count:index]
                        self.events_dic[second][id].count -= (index - count) 
                        num += (index - count)
                for i in range(count+1, len(self.events_dic[first][id].events)):
                    self.events_dic[first][id].events[i].start = -1
                for i in range(count+1, len(self.events_dic[second][id].events)):
                    self.events_dic[second][id].events[i].start = -1
                self.events_dic[first][id].count = count
                self.events_dic[second][id].count = count

            event_len = self.events_dic[self.event_list[0]][id].count;
            for event in self.events_dic.keys():
                if event_len > self.events_dic[event][id].count:
                    event_len = self.events_dic[event][id].count

            for event in self.events_dic.keys():
                del self.events_dic[event][id].events[event_len+1:]
                self.events_dic[event][id].count = event_len

    def get_start_time(self):
        """
		Note:get the start time of log files.
		Input:self.events_dic
		Output:self.START_TIME
        """
        for event in self.events_dic.keys():
            for id in self.client_id_list:
                del self.events_dic[event][id].events[self.events_dic[event][id].count + 1:]
                self.events_dic[event][id].events.sort(key=lambda e: e.start)
                if self.events_dic[event][id].events[0].start < self.START_TIME:
                    self.START_TIME = self.events_dic[event][id].events[0].start

        for time in self.seg_point_time:
            if time < self.START_TIME:
                sefl.START_TIME = time

    def update_to_relative(self):
        """
        all event time is decreased by start time
        """
        for event in self.events_dic.keys():
            for id in self.events_dic[event].keys():
                for i in range(self.events_dic[event][id].count + 1):
                    self.events_dic[event][id].events[i].start -= self.START_TIME
                    self.events_dic[event][id].events[i].end -= self.START_TIME
        
        for i in range(len(self.seg_point_time)):
            self.seg_point_time[i] -= self.START_TIME

    def get_total_interval(self):
        """
        get total interval from recorded events
        Input:self.events_dic
		Output:self.TOTAL_INTERVAL
        """
        
        for event in self.events_dic.keys():
            for id in self.client_id_list:
                lens = len(self.events_dic[event][id].events)
                if self.events_dic[event][id].events[lens - 1].end \
						> self.TOTAL_INTERVAL:
                    self.TOTAL_INTERVAL \
							= self.events_dic[event][id].events[lens- 1].end

        for time in self.seg_point_time:
            if time > self.TOTAL_INTERVAL:
                self.TOTAL_INTERVAL = time


        #if len(self.seg_point_list) == 0:
        #    self.seg_point_list.append((self.START_TIME, self.TOTAL_INTERVAL))

    def init(self, configfile, logfile):
        """initialize start time and parse config file"""
        self.parse_config_file(configfile, logfile)
        self.parse_log_file()
        if len(self.client_id_list) == 0:
            self.client_id_list.append('0')

        # filer the all data to be valid
        self.get_valid_data()

        if len(self.smooth_event_list) > 0:
            self.get_smooth_time()
            self.get_comm_time()
        self.get_start_time()
        self.get_total_interval()
        self.update_to_relative()
        if len(self.fps_event_list) != 0:
            self.time_dic = {}
            self.check_fps()
            self.calculate_fps()
