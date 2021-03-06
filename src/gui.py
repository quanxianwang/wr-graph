#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

# gui.py
#
# Copyright © 2104 Intel Corporation
#
# Author: Ning Tang <ning.tang@intel.com>
#         Quanxian Wang <quanxian.wang@intel.com>
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

# Contributor: Ning Tang
#              Quanxian Wang <quanxian.wang@intel.com>
#              Zhang Xiaoyan <zhang.xiaoyanx@intel.com>

import wx
import wx.lib.wxcairo
import sys
from analyze import Analyzer
from analyze import interval

FRAME_WIDTH = 1200
FRAME_HEIGHT = 600

OutputDir = None
Prefix = None
LogFile = None
ConfigFile = None
ShowFlag = None

def parse_arguments():
    global OutputDir
    global Prefix
    global LogFile
    global ConfigFile
    global ShowFlag

    ll = []
    if(sys.argv) == 0:
        print 'no arguments'
        return

    argument_tags = {'--output': [], '--config': [],
                     '--log': [], '--prefix': [],
                     '--show':[]}

    for key in argument_tags.keys():
        ll = filter(lambda s:s.startswith(key), sys.argv)
        if (len(ll) != 0):
            strs = ll[0]
            index = strs.find('=')
            argument_tags[key].append(strs[index+1:])

    if (len(argument_tags['--output'])):
        OutputDir = argument_tags['--output'][0]
    if (len(argument_tags['--config'])):
        ConfigFile = argument_tags['--config'][0]
    if (len(argument_tags['--log'])):
        LogFile = argument_tags['--log'][0]
    if (len(argument_tags['--prefix'])):
        Prefix = argument_tags['--prefix'][0]
    if (len(argument_tags['--show'])):
        ShowFlag = argument_tags['--show'][0]
    
class TabPanel(wx.Panel):
    """
    Tab Panel Serves as one page in notebook
    """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        # use horizontal sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

    def addWidget(self, widget):
        self.sizer.Add(widget, 0, wx.ALL, 5)


class Notebook(wx.Notebook):
    """
    Notebook have the ability to switch between tabs
    """
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, id=wx.ID_ANY, style=
                             wx.BK_DEFAULT)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.seleted = 0

    def addFpsTab(self, frame, tabName):
        """
        Generate FPS imagebox, quite similar to addImageTab
        """
        newTab = TabPanel(self)
        image = wx.EmptyImage(frame.width, frame.height)
        imageWidget = wx.StaticBitmap(newTab, wx.ID_ANY,
                                      wx.BitmapFromImage(image))
        newTab.addWidget(imageWidget)

        # checkboxes
        checkboxSizer = wx.BoxSizer(wx.VERTICAL)
        checkboxes = []
        events = frame.client_dic.keys()
        for name in events:
            checkbox = wx.CheckBox(newTab, -1, name)
            checkbox.SetValue(frame.client_dic[name])
            wx.EVT_CHECKBOX(frame, checkbox.GetId(), frame.checkboxChange_fps)
            checkboxSizer.Add(checkbox, 0, wx.ALL, 5)
            checkboxes.append(checkbox)

        newTab.addWidget(checkboxSizer)
        self.AddPage(newTab, tabName)
        return imageWidget, checkboxes

    def addSmoothTab(self, frame, tabName):
        """
        Generate Frame imagebox, quite similar to addImageTab
        """
        newTab = TabPanel(self)
        image = wx.EmptyImage(frame.width, frame.height)
        imageWidget = wx.StaticBitmap(newTab, wx.ID_ANY,
                                      wx.BitmapFromImage(image))
        newTab.addWidget(imageWidget)
        self.AddPage(newTab, tabName)
        return imageWidget

    def OnPageChanged(self, event):
        self.selected = event.GetSelection()
        event.Skip()


class Analyzer_Frame(wx.Frame):
    """ We simply derive a new class of Frame. """
    def __init__(self, parent, title, output, configfile, logfile):
        # window size
        self.width = FRAME_WIDTH
        self.height = FRAME_HEIGHT
        wx.Frame.__init__(self, parent, title=title,
                          size=(self.width, self.height))
        self.area = "N/A"
        self.label_moved = False
        self.selected = 0
        self.count = 0
        # stores each level's image
        self.fps_charts = []
        self.smooth_charts = []
        self.imageCountFps = 0
        self.imageCountSmooth = 0
        self.intervals = []
        # UI related panel
        self.scrolling_window = wx.ScrolledWindow(self)
        self.scrolling_window.SetScrollRate(1, 1)
        self.scrolling_window.EnableScrolling(True, True)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        # analyzer class instance
        self.analyzer = Analyzer()
        self.analyzer.init(configfile, logfile)
        self.action_type = self.analyzer.get_action_type()
        self.client_color = []
        self.client_dic = self.analyzer.get_client_activate()
        self.addWidgets()
        self.showTotalInterval()
        self.Show(True)

    def addWidgets(self):
        """Initialize the UI and layout"""
        hyphen = wx.StaticText(self.scrolling_window,
                               label="(start time) - (end time)")

        self.viewButton = wx.Button(self.scrolling_window, label='View')
        self.viewButton.Bind(wx.EVT_BUTTON, self.onButton)
        self.saveButton = wx.Button(self.scrolling_window, label='Save')
        self.saveButton.Bind(wx.EVT_BUTTON, self.onButton)

        # Tabs
        self.notebook = Notebook(self.scrolling_window)
        self.fpsBox, self.checkboxes_fps = \
				               self.notebook.addFpsTab(self, "FPS Chart")
        self.smoothBox = self.notebook.addSmoothTab(self, "Frame Summary")

        # Sizers and widgets
        self.startTimeText = wx.TextCtrl(self.scrolling_window, size=(100, -1))
        self.endTimeText = wx.TextCtrl(self.scrolling_window, size=(100, -1))
        self.labelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.labelSizer.Add(self.startTimeText, 0, wx.ALL, 5)
        self.labelSizer.Add(hyphen, 0, wx.UP, 10)
        self.labelSizer.Add(self.endTimeText, 0, wx.ALL, 5)
        self.labelSizer.Add(self.viewButton, 0, wx.LEFT, 20)
        self.labelSizer.Add(self.saveButton, 0, wx.LEFT, 20)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.notebook, 0, wx.ALL, 5)
        self.mainSizer.Add(self.labelSizer, 0, wx.ALL, 5)

        self.scrolling_window.SetSizer(self.mainSizer)
        self.mainSizer.Fit(self)

        self.scrolling_window.Layout()

    def showTotalInterval(self):
        """Show Initial Chart spans over total interval"""
        init_interval = interval()
        init_interval.start = self.analyzer.start_time
        init_interval.end = self.analyzer.total_interval
        self.addShowImage(init_interval)

    def OnSize(self, event):
        self.scrolling_window.SetSize(self.GetClientSize())

    def onView(self):
        """Callback function on action to View button click"""
        new_interval = interval()
        try:
            new_interval.start = \
                int(self.absToRel(self.startTimeText.GetValue()))
            new_interval.end = \
                int(self.absToRel(self.endTimeText.GetValue()))
        except:
            print "input time not integer"
            return
        if new_interval.end < new_interval.start:
            return
        if new_interval.end - new_interval.start \
            > self.analyzer.total_interval:
            new_interval.end = new_interval.start \
                               + self.analyzer.total_interval
        if new_interval.start > self.analyzer.total_interval \
           or new_interval.end < 0:
            return
        del self.fps_charts[0:len(self.fps_charts)]
        del self.smooth_charts[0:len(self.smooth_charts)]
        del self.intervals[0:len(self.intervals)]
        del self.client_color[0:len(self.client_color)]
        self.imageCountFps = 0
        self.imageCountSmooth = 0
        self.label_moved = False
        self.addShowImage(new_interval)

    def onSave(self):
        """Save image to file"""
        if self.imageCountFps > 0:
            self.fps_charts[self.imageCountFps - 1].commit()
        if self.imageCountSmooth > 0:
            self.smooth_charts[self.imageCountSmooth - 1].commit()
        print "chart and fps image saved"

    def onButton(self, event):
        if event.GetEventObject() == self.saveButton:
            self.onSave()
        elif event.GetEventObject() == self.viewButton:
            self.onView()

    def getFPSChart(self, interval):
        """Request a new dot line chart"""
        filename = str(int(interval.start)) + '-' \
                   + str(int(interval.end)) + '_fps.png'

        if self.action_type == 'media':
            img = self.analyzer.draw_fps_media(filename, interval.start, \
                                         interval.end, self.width, \
                                         self.height, OutputDir)
        else:
            img = self.analyzer.draw_fps(filename, interval.start, \
                                         interval.end, self.width, \
                                         self.height, OutputDir)
        return img

    def getSmoothChart(self, interval):
        """Request a new dot line chart"""
        filename = str(int(interval.start)) + '-' \
                   + str(int(interval.end)) + '_smooth.png'
        if self.action_type == 'media':
            return None
        img = self.analyzer.draw_smooth(filename, interval.start, \
                                        interval.end, self.width, \
                                        self.height, OutputDir)
        return img

    def relToAbs(self, time):
        return float(time) + self.analyzer.start_time

    def absToRel(self, time):
        return float(time) - self.analyzer.start_time

    def showImage(self):
        """Show image in image list to screen"""
        if self.imageCountFps > 0:
            fps_chart = self.fps_charts[self.imageCountFps - 1]
            self.fpsBox.SetBitmap(
                wx.lib.wxcairo.BitmapFromImageSurface(fps_chart.surface))
        if self.imageCountSmooth > 0:
            smooth_chart = self.smooth_charts[self.imageCountSmooth - 1]
            self.smoothBox.SetBitmap(
                wx.lib.wxcairo.BitmapFromImageSurface(smooth_chart.surface))
        self.Refresh()

    def showBitmap(self, imageBox, bitmap):
        """Show bitmap to imagebox"""
        imageBox.SetBitmap(bitmap)
        self.Refresh()

    def checkboxChange_fps(self, event):
        checkbox = event.GetEventObject()
        self.client_dic[self.happened_client] = False
        self.client_dic[checkbox.GetLabel()] = checkbox.IsChecked()

        if not (True in self.client_dic.values()):
            self.client_dic[checkbox.GetLabel()] = not checkbox.IsChecked()
            checkbox.SetValue(True)
            return
        self.analyzer.updateClient(self.client_dic)
        self.refreshShowImage()

    def updateInterval(self):
        interval = self.intervals[self.imageCountFps - 1]
        self.startTimeText.SetValue(str(int(self.relToAbs(interval.start))))
        self.endTimeText.SetValue(str(int(self.relToAbs(interval.end))))

    def updateCheckboxes_fps(self):
        for key in self.client_dic:
            if self.client_dic[key] == True:
                self.happened_client = key
        client_color = self.client_color[self.imageCountFps - 1]
        for checkbox in self.checkboxes_fps:
            if checkbox.GetLabel() == self.happened_client:
                checkbox.SetValue(True)
                index = self.happened_client.index(checkbox.GetLabel())
                r = client_color[index][0] * 255
                g = client_color[index][1] * 255
                b = client_color[index][2] * 255
                checkbox.SetForegroundColour(wx.Colour(r, g, b))
            else:
                checkbox.SetValue(False)

    def addShowImage(self, interval, label = None):
        self.intervals.append(interval)
        fps_image = self.getFPSChart(interval)
        if fps_image is not None:
            self.fps_charts.append(fps_image)
            self.imageCountFps += 1
        client_color = self.analyzer.get_client_color()
        self.client_color.append(client_color)
        smooth_image = self.getSmoothChart(interval)
        if smooth_image is not None:
            self.smooth_charts.append(smooth_image)
            self.imageCountSmooth += 1
        self.showImage()
        self.updateCheckboxes_fps()
        self.updateInterval()

    def delShowImage(self):
        if len(self.fps_charts) == self.imageCountFps and \
				                            self.imageCountFps > 0:
            del self.fps_charts[self.imageCountFps - 1]
            self.imageCountFps -= 1
        if len(self.smooth_charts) == self.imageCountSmooth and \
				                            self.imageCountSmooth > 0:
            del self.smooth_chart[self.imageCountSmooth - 1]
            self.imageCountSmooth -= 1
        del self.intervals[self.imageCountFps - 1]
        self.showImage()
        self.updateInterval()
        self.updateCheckboxes_fps()

    def refreshShowImage(self, labels = None):
        new_fps = self.getFPSChart(self.intervals[self.imageCountFps - 1])
        new_smooth = self.getSmoothChart(self.intervals[self.imageCountSmooth - 1])
        client_color = self.analyzer.get_client_color()
        if len(self.fps_charts) == self.imageCountFps \
		            and self.imageCountFps > 0:
            del self.fps_charts[self.imageCountFps - 1]
            del self.client_color[self.imageCountFps - 1]
        if len(self.smooth_charts) == self.imageCountSmooth \
		            and self.imageCountSmooth > 0:
            del self.smooth_charts[self.imageCountSmooth - 1]
        self.fps_charts.append(new_fps)
        self.smooth_charts.append(new_smooth)
        self.client_color.append(client_color)
        self.showImage()
        self.updateCheckboxes_fps()
        self.updateInterval()

parse_arguments()
if ShowFlag == 'false':
    analyzer = Analyzer()
    analyzer.init(ConfigFile, LogFile)
    action_type = analyzer.get_action_type()
    if Prefix == None:
        Prefix = 'wayland_rendering'
    filename = Prefix + '_fps.png'
    if action_type == 'media':
        fps_image = analyzer.draw_fps_media(filename, analyzer.start_time,\
                                  analyzer.total_interval, 1200, 600, OutputDir)
        fps_image.commit(OutputDir)
    else:
        fps_image = analyzer.draw_fps(filename, analyzer.start_time,\
                                  analyzer.total_interval, 1200, 600)
        filename = Prefix + '_frame.png'
        smooth_image = analyzer.draw_smooth(filename, analyzer.start_time,\
                                        analyzer.total_interval, 1200,\
                                        600, OutputDir)
        fps_image.commit(OutputDir)
        smooth_image.commit(OutputDir)
else:
    app = wx.App(False)
    frame = Analyzer_Frame(None, 'Profile Analyzer', OutputDir, \
                           ConfigFile, LogFile)
    app.MainLoop()
