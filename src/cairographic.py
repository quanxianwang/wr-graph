#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CairoPlot.py
#
# Copyright (c) 2008 Rodrigo Moreira Araújo
#
# Author: Rodrigo Moreiro Araujo <alf.rodrigo@gmail.com>
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

# Contributor: João S. O. Bueno
#              Ning Tang <ning.tang@intel.com>
#              Quanxian Wang<quanxian.wang@intel.com>
#              Zhang, Xiaoyan<zhang.xiaoyanx@intel.com>


__version__ = 1.2

import cairo
import math
import random

HORZ = 0
VERT = 1
NORM = 2

COLORS = {"red"    : (1.0,0.0,0.0,1.0), "lime"    : (0.0,1.0,0.0,1.0), "blue"   : (0.0,0.0,1.0,1.0),
          "maroon" : (0.5,0.0,0.0,1.0), "green"   : (0.0,0.5,0.0,1.0), "navy"   : (0.0,0.0,0.5,1.0),
          "yellow" : (1.0,1.0,0.0,1.0), "magenta" : (1.0,0.0,1.0,1.0), "cyan"   : (0.0,1.0,1.0,1.0),
          "orange" : (1.0,0.5,0.0,1.0), "white"   : (1.0,1.0,1.0,1.0), "black"  : (0.0,0.0,0.0,1.0),
          "gray" : (0.5,0.5,0.5,1.0), "light_gray" : (0.9,0.9,0.9,1.0),
          "transparent" : (0.0,0.0,0.0,0.0)}

THEMES = {"black_red"         : [(0.0,0.0,0.0,1.0), (1.0,0.0,0.0,1.0)],
          "red_green_blue"    : [(1.0,0.0,0.0,1.0), (0.0,1.0,0.0,1.0), (0.0,0.0,1.0,1.0)],
          "red_orange_yellow" : [(1.0,0.2,0.0,1.0), (1.0,0.7,0.0,1.0), (1.0,1.0,0.0,1.0)],
          "yellow_orange_red" : [(1.0,1.0,0.0,1.0), (1.0,0.7,0.0,1.0), (1.0,0.2,0.0,1.0)],
          "rainbow"           : [(1.0,0.0,0.0,1.0), (1.0,0.5,0.0,1.0), (1.0,1.0,0.0,1.0), \
				                 (0.0,1.0,0.0,1.0), (0.0,0.0,1.0,1.0), (0.3, 0.0, 0.5,1.0), \
								 (0.5, 0.0, 1.0, 1.0)]}

def colors_from_theme( theme, series_length, mode = 'solid' ):
    colors = []
    if theme not in THEMES.keys() :
        raise Exception, "Theme not defined"
    color_steps = THEMES[theme]
    n_colors = len(color_steps)
    if series_length <= n_colors:
        colors = [color + tuple([mode]) for color in color_steps[0:n_colors]]
    else:
        iterations = [(series_length - n_colors)/(n_colors - 1) for i in color_steps[:-1]]
        over_iterations = (series_length - n_colors) % (n_colors - 1)
        for i in range(n_colors - 1):
            if over_iterations <= 0:
                break
            iterations[i] += 1
            over_iterations -= 1
        for index,color in enumerate(color_steps[:-1]):
            colors.append(color + tuple([mode]))
            if iterations[index] == 0:
                continue
            next_color = color_steps[index+1]
            color_step = ((next_color[0] - color[0])/(iterations[index] + 1),
                          (next_color[1] - color[1])/(iterations[index] + 1),
                          (next_color[2] - color[2])/(iterations[index] + 1),
                          (next_color[3] - color[3])/(iterations[index] + 1))
            for i in range( iterations[index] ):
                colors.append((color[0] + color_step[0]*(i+1),
                               color[1] + color_step[1]*(i+1),
                               color[2] + color_step[2]*(i+1),
                               color[3] + color_step[3]*(i+1),
                               mode))
        colors.append(color_steps[-1] + tuple([mode]))
    return colors


def other_direction(direction):
    "explicit is better than implicit"
    if direction == HORZ:
        return VERT
    else:
        return HORZ

#Class definition

class Graphic(object):
    def __init__(self,
                 surface=None,
                 data=None,    
                 width=640,
                 height=480,
                 show_end=0,
                 background=None,
                 border = 0,
                 axis = False,
                 dash = False,
                 grid = False,
                 x_labels = None,
                 y_labels = None,
                 x_bounds = None,
                 y_bounds = None,
                 z_bounds = None,
                 x_title  = None,
                 y_title  = None,
                 series_colors = None,
                 circle_colors = None):
        random.seed(2)
        self.create_surface(surface, width, height)
        self.dimensions = {}
        self.dimensions[HORZ] = width
        self.dimensions[VERT] = height
        self.context = cairo.Context(self.surface)
        self.show_end = show_end
        self.labels={}
        self.labels[HORZ] = x_labels
        self.labels[VERT] = y_labels
        self.min_data_value = [0,0,0]
        self.max_data_value = [0,0,0]
        self.font_size = 10
        self.set_background (background)
        self.border = border
        self.borders = {}
        self.line_color = (0.5, 0.5, 0.5)
        self.line_width = 0.5
        self.data_line_width = 1.0
        self.label_color = (0.0, 0.0, 0.0)
        self.grid_color = (0.8, 0.8, 0.8)
        self.bounds = {}
        self.bounds[HORZ] = x_bounds
        self.bounds[VERT] = y_bounds
        self.bounds[NORM] = z_bounds
        self.titles = {}
        self.titles[HORZ] = x_title
        self.titles[VERT] = y_title
        self.max_value = {}
        self.axis = axis
        self.grid = grid
        self.variable_radius = False
        self.x_label_angle = 0
        self.circle_colors = circle_colors 
        self.load_series(data, x_labels, y_labels, series_colors)
       # self.calc_boundaries()
       # self.calc_labels()
                
    
    def convert_list_to_tuple(self, data):
        #Data must be converted from lists of coordinates to a single
        # list of tuples
        out_data = zip(*data)
        if len(data) == 3:
            self.variable_radius = True
        return out_data
    
    
    def calc_labels(self):
        if not self.labels[HORZ]:
            amplitude = self.bounds[HORZ][1] - self.bounds[HORZ][0]
            if amplitude % 10: #if horizontal labels need floating points
                self.labels[HORZ] = ["%.2lf" % (float(self.bounds[HORZ][0] \
						+ (amplitude * i / 10.0))) for i in range(11) ]
            else:
                self.labels[HORZ] = ["%d" % (int(self.bounds[HORZ][0] \
						+ (amplitude * i / 10.0))) for i in range(11) ]
        if not self.labels[VERT]:
            amplitude = self.bounds[VERT][1] - self.bounds[VERT][0]
            if amplitude % 10: #if vertical labels need floating points
                self.labels[VERT] = ["%.1lf" % (float(self.bounds[VERT][0] 
					+ (amplitude * i / 10.0))) for i in range(11)]
            else:
                self.labels[VERT] = ["%di" % (int(self.bounds[VERT][0] \
						+ (amplitude * i / 10.0))) for i in range(11) ]


    def calc_extents(self, direction):
        if direction == HORZ:
            self.context.set_font_size(self.font_size * 0.8)
        else:
            self.context.set_font_size(self.font_size * 1.8)
        self.max_value[direction] = max(self.context.text_extents(item)[2] \
				                            for item in self.labels[direction])
        self.borders[other_direction(direction)] = \
				                   self.max_value[direction] + self.border + 20


    def calc_boundaries(self):
        #HORZ = 0, VERT = 1, NORM = 2
        #for group in self.group_list:
        #    for index, item in enumerate(group):
        #        if item > self.max_data_value[index]:
        #            #self.max_data_value[index] += index
        #            self.max_data_value[index] = item
        #        elif item < self.min_data_value[index]:
        #            self.min_data_value[index] = item
        number = -1
        max_data_value = 0
        for group in self.group_list:
            number += 1
            if group[1] > max_data_value:
                max_data_value = group[1]
        self.max_data_value[0] = number
        self.max_data_value[1] = max_data_value
        if not self.bounds[HORZ]:
            self.bounds[HORZ] = (self.min_data_value[HORZ], \
					             self.max_data_value[HORZ] + 0.06)
        if not self.bounds[VERT]:
            self.bounds[VERT] = (self.min_data_value[VERT], \
					             self.max_data_value[VERT] + \
								 self.max_data_value[VERT]/10/2 + 2.5)
        if not self.bounds[NORM]:
            self.bounds[NORM] = (self.min_data_value[NORM], \
					             self.max_data_value[NORM])
	

    def calc_all_extents(self):
        self.calc_extents(HORZ)
        self.calc_extents(VERT)

        self.plot_height = self.dimensions[VERT] - 2 * self.borders[VERT]
        self.plot_width = self.dimensions[HORZ] - 2* self.borders[HORZ]
        
        self.plot_top = self.dimensions[VERT] - self.borders[VERT]
                
    def calc_steps(self):
        #Calculates all the x, y, z and color steps
        series_amplitude = [self.bounds[index][1] - self.bounds[index][0] for index in range(3)]

        if series_amplitude[HORZ]:
            self.horizontal_step = float (self.plot_width) / series_amplitude[HORZ]
        else:
            self.horizontal_step = 0.00
            
        if series_amplitude[VERT]:
            self.vertical_step = float (self.plot_height) / series_amplitude[VERT]
        else:
            self.vertical_step = 0.00

        if series_amplitude[NORM]:
            if self.variable_radius:
                self.z_step = float (self.bounds[NORM][1]) / series_amplitude[NORM]
            if self.circle_colors:
                self.circle_color_step = \
						tuple([float(self.circle_colors[1][i]-self.circle_colors[0][i]) / \
						      series_amplitude[NORM] for i in range(4)])
        else:
            self.z_step = 0.00
            self.circle_color_step = ( 0.0, 0.0, 0.0, 0.0 )
    
    def get_circle_color(self, value):
        return tuple( [self.circle_colors[0][i] + \
				      value*self.circle_color_step[i] for i in range(4)] )
    
    def render(self):
        self.calc_all_extents()
        self.calc_steps()
        self.render_background()
        self.render_bounding_box()
        if self.axis:
            self.render_axis()
        if self.grid:
            self.render_grid()
        #self.render_labels()
        #self.render_fps()
        
            
    def render_axis(self):
        #Draws both the axis lines and their titles
        cr = self.context
        cr.set_source_rgba(*self.line_color)
        cr.move_to(self.borders[HORZ], self.dimensions[VERT] - self.borders[VERT])
        cr.line_to(self.borders[HORZ], self.borders[VERT])
        cr.stroke()

        cr.move_to(self.borders[HORZ], self.dimensions[VERT] - self.borders[VERT])
        cr.line_to(self.dimensions[HORZ] - self.borders[HORZ], \
				   self.dimensions[VERT] - self.borders[VERT])
        cr.stroke()

        cr.set_source_rgba(*self.label_color)
        self.context.set_font_size( 1.2 * self.font_size )
        if self.titles[HORZ]:
            title_width,title_height = cr.text_extents(self.titles[HORZ])[2:4]
            cr.move_to( self.dimensions[HORZ]/2 - title_width/2, \
					    self.borders[VERT] - title_height/2 )
            cr.show_text( self.titles[HORZ] )

        if self.titles[VERT]:
            title_width,title_height = cr.text_extents(self.titles[VERT])[2:4]
            cr.move_to( self.dimensions[HORZ] - self.borders[HORZ] + title_height/2, \
					    self.dimensions[VERT]/2 - title_width/2)
            cr.save()
            cr.rotate( math.pi/2 )
            cr.show_text( self.titles[VERT] )
            cr.restore()
        
    def render_grid(self):
        cr = self.context
        horizontal_step = float( self.plot_height ) / ( len( self.labels[VERT] ) - 1 )
        vertical_step = float( self.plot_width ) / ( len( self.labels[HORZ] ) - 1 )
        
        x = self.borders[HORZ] + vertical_step
        y = self.plot_top - horizontal_step
        
        for label in self.labels[HORZ][:-1]:
            cr.set_source_rgba(*self.grid_color)
            cr.move_to(x, self.dimensions[VERT] - self.borders[VERT])
            cr.line_to(x, self.borders[VERT])
            cr.stroke()
            x += vertical_step
        for label in self.labels[VERT][:-1]:
            cr.set_source_rgba(*self.grid_color)
            cr.move_to(self.borders[HORZ], y)
            cr.line_to(self.dimensions[HORZ] - self.borders[HORZ], y)
            cr.stroke()
            y -= horizontal_step
    
    def render_labels(self, offset, flag):
        self.context.set_font_size(self.font_size * 1.2)
        self.render_horz_labels(offset)
        self.render_vert_labels(flag)
    
    def render_horz_labels(self, offset):
        cr = self.context
        step = float( self.plot_width ) / ( len( self.labels[HORZ] ) - 1)
        x = self.borders[HORZ]
        y = self.dimensions[VERT] - self.borders[VERT] + 5
        # store rotation matrix from the initial state
        rotation_matrix = cr.get_matrix()
        rotation_matrix.rotate(self.x_label_angle)
        cr.set_source_rgba(*self.label_color)
        first  = 0
        for item in self.labels[HORZ]:
            width = cr.text_extents(item)[2]
            if first == 0:
                #cr.move_to(x-90, y+10)
                cr.move_to(x-offset, y+10)
                first = 1
            else:
                cr.move_to(x-30, y-20)
                cr.line_to(x-30, y-10)
                cr.set_line_width(self.line_width)
                cr.stroke()
                cr.move_to(x-60, y+10)
            cr.save()
            cr.set_matrix(rotation_matrix)
            cr.show_text(item)
            cr.restore()
            x += step
    
    def render_vert_labels(self, flag):
        cr = self.context
        step = ( self.plot_height ) / ( len( self.labels[VERT] ) - 1)
        y = self.plot_top
        cr.set_source_rgba(*self.label_color)
        for item in self.labels[VERT]:
            width = cr.text_extents(item)[2]
            cr.move_to(self.borders[HORZ] - width - 20, y)
            cr.show_text(item + flag)
            y -= step


    def render_fps(self):
        self.render_labels(0, 'fps')
        cr = self.context
        cr.rectangle(self.borders[HORZ], self.borders[VERT], \
				     self.plot_width, self.plot_height)
        cr.clip()
        x0 = self.borders[HORZ] 
        y0 = self.borders[VERT]
        last_data = None 
        flag = 0
        last = 0
        count = 0
        total = 0
        last_x = 0
        for data in self.group_list :
            x = x0 + (data[0] * self.plot_width) / self.show_end
            y = y0 + self.vertical_step*data[1]
            if last_data :
                old_x = x0 + (last_data[0] * self.plot_width) / self.show_end
                old_y = y0 + self.vertical_step * last_data[1]
                if data[1] == -1:
                    flag = 1
                    cr.set_source_rgb(0, 0, 0)
                    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, \
							            cairo.FONT_WEIGHT_NORMAL)
                    cr.set_font_size(12)
                    offset = (x - last_x) / 2 + last_x
                    if offset + 100 > self.dimensions[HORZ]:
                        offset = last_x
                        cr.move_to(offset, y0+10)
                    else:
                        cr.move_to(offset, y0+10)
                    average = float("{0:.1f}".format(total / count))
                    str1 = 'ave=' + str(average)
                    cr.show_text(str1)
                    count = 0
                    total = 0
                    continue
                if flag == 1:
                    cr.set_source_rgb(0.7, 0.2, 0.0)
                    cr.set_line_width(2.0)
                    cr.set_dash([5.0, 5.0])  
                    cr.move_to( old_x, self.dimensions[VERT] - old_y )
                    cr.line_to( x, self.dimensions[VERT] - y)
                    cr.stroke()
                    flag = 0
                    last_x = x
                else:
                    cr.set_source_rgba(*self.series_colors[0][:4])
                    cr.set_line_width(self.data_line_width)
                    cr.set_dash([])
                    cr.move_to( old_x, self.dimensions[VERT] - old_y )
                    cr.line_to( x, self.dimensions[VERT] - y)
                    cr.stroke()
            else:
                if data[1] == -1:
                    continue
            count += 1
            total += data[1]
            last_data = data

    
    def render_smooth(self):
        self.render_labels(50, 'ms')
        cr = self.context
        cr.rectangle(self.borders[HORZ], self.borders[VERT], \
				     self.plot_width, self.plot_height)
        cr.clip()
        x0 = self.borders[HORZ] - self.bounds[HORZ][0]*self.horizontal_step
        y0 = self.borders[VERT] - self.bounds[VERT][0]*self.vertical_step
        color_index = 0
        index = 0
        total = 0
        count = 0
        total_event = 0
        total_comm = 0
        for data in self.group_list:
            total += data[1]
            if self.labels[HORZ].index(data[0]) % 2 == 0:
                total_event += data[1]
            else:
                total_comm += data[1]
        per = 0
        last_data = None
        off_width = 50
        for data in self.group_list :
            data = (self.labels[HORZ].index(data[0]), data[1])
            cr.set_source_rgba(*self.series_colors[color_index][:4])
            x = x0 + self.horizontal_step * data[0]
            y = y0 + self.vertical_step*data[1]
            per = data[1] / total * 100
            sper = '(' + str(float("{0:.2f}".format(per))) + '%'+')'
            value = str(float("{0:.2f}".format(data[1])))
            if last_data :
                cr.rectangle(x-off_width, \
						     self.dimensions[VERT]-y0-self.vertical_step*data[1], \
							 off_width, self.vertical_step*data[1])
                cr.fill()
                old_x = x0 + self.horizontal_step*last_data[0]
                old_y = y0 + self.vertical_step*last_data[1]
                cr.set_source_rgb(0, 0, 0)
                cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                cr.set_font_size(12)
                cr.move_to(x - off_width - 8, self.dimensions[VERT] - y - 20)
                cr.show_text(sper)
                cr.move_to(x - off_width, self.dimensions[VERT] - y - 5)
                cr.show_text(value)
                cr.move_to(old_x - off_width/2, self.dimensions[VERT] - old_y)
                cr.line_to(x - off_width/2, self.dimensions[VERT] - y)
                cr.set_line_width(self.data_line_width)
				# Display line as dash line 
                cr.stroke()
                cr.set_dash([])
            else:
                cr.rectangle(x, self.dimensions[VERT]-y0-self.vertical_step*data[1], \
						     off_width, self.vertical_step*data[1])
                cr.fill()
                cr.set_source_rgb(0, 0, 0)
                cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                cr.set_font_size(12)
                cr.move_to(x, self.dimensions[VERT] - y - 20)
                cr.show_text(sper)
                cr.move_to(x, self.dimensions[VERT] - y - 5)
                cr.show_text(value)
                
            last_data = data
            color_index += 1
    

    def create_surface(self, surface, width=None, height=None):
        self.filename = None
        if isinstance(surface, cairo.Surface):
            self.surface = surface
            return
        if not type(surface) in (str, unicode):
            raise TypeError("Surface should be either a Cairo surface \
					         or a filename, not %s" % surface)
        sufix = surface.rsplit(".")[-1].lower()
        self.filename = surface
        if sufix == "png":
            self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        elif sufix == "ps":
            self.surface = cairo.PSSurface(surface, width, height)
        elif sufix == "pdf":
            self.surface = cairo.PSSurface(surface, width, height)
        else:
            if sufix != "svg":
                self.filename += ".svg"
            self.surface = cairo.SVGSurface(self.filename, width, height)

    def commit(self, output_dir=None):
        try:
            self.context.show_page()
            if self.filename and self.filename.endswith(".png"):
                if output_dir == None:
                    output_dir = '.'
                str1 = output_dir + '/' + self.filename
                self.surface.write_to_png(str1)
            else:
                self.surface.finish()
        except cairo.Error:
            pass

    def load_series (self, data, x_labels=None, y_labels=None, series_colors=None):
        self.group_list = []
        self.data_list = []
        group = ()
        for index,item in data.items():
            group = (index, item)
            self.group_list.append(group)

       # for index,item in enumerate(data):
       #     group = (index, item)
       #     self.group_list.append(group)

        self.process_colors( series_colors )
        self.calc_boundaries()
        self.calc_labels()
    
       
    def process_colors( self, series_colors, length = None, mode = 'solid' ):
        #series_colors might be None, a theme, 
		#a string of colors names or a list of color tuples
        if length is None :
            length = len( self.group_list )

        #no colors passed
        if not series_colors:
            #Randomize colors
            self.series_colors = [ [random.random() for i in range(3)] + [1.0, mode]  \
					                  for series in range( length ) ]
        else:
            #Just theme pattern
            if not hasattr( series_colors, "__iter__" ):
                theme = series_colors
                self.series_colors = colors_from_theme( theme.lower(), length )

            #Theme pattern and mode
            elif not hasattr(series_colors, '__delitem__') and \
					                    not hasattr( series_colors[0], "__iter__" ):
                theme = series_colors[0] 
                mode = series_colors[1]
                self.series_colors = colors_from_theme( theme.lower(), length, mode )

            #List
            else:
                self.series_colors = series_colors
                for index, color in enumerate( self.series_colors ):
                    #element is a color name
                    if not hasattr(color, "__iter__"):
                        self.series_colors[index] = COLORS[color.lower()] + tuple([mode])
                    #element is rgb tuple instead of rgba
                    elif len( color ) == 3 :
                        self.series_colors[index] += (1.0,mode)
                    #element has 4 elements, might be rgba tuple or rgb tuple with mode
                    elif len( color ) == 4 :
                        #last element is mode
                        if not hasattr(color[3], "__iter__"):
                            self.series_colors[index] += tuple([color[3]])
                            self.series_colors[index][3] = 1.0
                        #last element is alpha
                        else:
                            self.series_colors[index] += tuple([mode])

    def get_width(self):
        return self.surface.get_width()

    def get_height(self):
        return self.surface.get_height()

    def set_background(self, background):
        if background is None:
            self.background = (0.0,0.0,0.0,0.0)
        elif type(background) in (cairo.LinearGradient, tuple):
            self.background = background
        elif not hasattr(background,"__iter__"):
            colors = background.split(" ")
            if len(colors) == 1 and colors[0] in COLORS:
                self.background = COLORS[background]
            elif len(colors) > 1:
                self.background = cairo.LinearGradient(self.dimensions[HORZ] / 2, \
						              0, self.dimensions[HORZ] / 2, self.dimensions[VERT])
                for index,color in enumerate(colors):
                    self.background.add_color_stop_rgba(float(index)/(len(colors)-1),\
							                            *COLORS[color])
        else:
            raise TypeError ("Background should be either cairo.LinearGradient \
					          or a 3/4-tuple, not %s" % type(background))

    def render_background(self):
        if isinstance(self.background, cairo.LinearGradient):
            self.context.set_source(self.background)
        else:
            self.context.set_source_rgba(*self.background)
        self.context.rectangle(0,0, self.dimensions[HORZ], self.dimensions[VERT])
        self.context.fill()

    def render_bounding_box(self):
        self.context.set_source_rgba(*self.line_color)
        self.context.set_line_width(self.line_width)
        self.context.rectangle(self.border, self.border,
                               self.dimensions[HORZ] - 2 * self.border,
                               self.dimensions[VERT] - 2 * self.border)
        self.context.stroke()


# Function definition


if __name__ == "__main__":
    import tests
    import seriestests
