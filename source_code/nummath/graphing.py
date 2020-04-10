import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np


class Graph:
    def __init__(self, figure=None, axes=None, fig_size=None, dpi=None):
        self.figure = plt.figure(figsize=fig_size, dpi=dpi) if figure is None else figure
        self.axes = self.figure.add_subplot(1, 1, 1) if axes is None else axes
        self.data_set_list = []
        self.legend_loc = None
        self.x_ticks = None
        self.y_ticks = None

        self.time_axis = None
        self.major_time_locator = None
        self.major_time_formatter = None
        self.minor_time_locator = None
        self._time_interval = {
            'auto': mdates.AutoDateLocator,
            'day': mdates.DayLocator,
            'week': mdates.WeekdayLocator,
            'month': mdates.MonthLocator,
            'year': mdates.YearLocator}
        self.date_min = None
        self.date_max = None
        self.data_labels = []

    def add_data_set(self, name, x, y, **line_props):
        new_data_set = {'name': name, 'x': x, 'y': y, 'line': line_props}
        self.data_set_list.append(new_data_set)

    def set_graph_title(self, title=''):
        if title: self.axes.set_title(title)

    def set_axis_titles(self, x_title='', y_title=''):
        if x_title: self.axes.set_xlabel(x_title)
        if y_title: self.axes.set_ylabel(y_title)

    def add_legend(self, loc='best'):
        self.legend_loc = loc

    def scale_x_axis(self, lim_min, lim_max, tick_step):
        tick_num = int(np.ceil((lim_max - lim_min) / tick_step)) + 1
        self.x_ticks = np.linspace(lim_min, lim_max, tick_num, endpoint=True)

    def scale_y_axis(self, lim_min, lim_max, tick_step):
        tick_num = int(np.ceil((lim_max - lim_min) / tick_step)) + 1
        self.y_ticks = np.linspace(lim_min, lim_max, tick_num, endpoint=True)

    def setup_time_axis(self, date_min, date_max, major_interval='auto', minor_interval='auto', major_fmt='%d/%m/%y'):
        self.time_axis = True
        if major_interval == 'week':
            self.major_time_locator = self._time_interval[major_interval](byweekday=mdates.MO)
        else:
            self.major_time_locator = self._time_interval[major_interval]()
        if major_interval == 'auto':
            self.major_time_formatter = mdates.AutoDateFormatter(self.major_time_locator)
        else:
            self.major_time_formatter = mdates.DateFormatter(major_fmt)
        self.minor_time_locator = self._time_interval[minor_interval]()
        self.date_min = date_min
        self.date_max = date_max

    def turn_grid_on(self):
        self.axes.grid(True)

    def turn_grid_off(self):
        self.axes.grid(False)

    def _plot(self):
        for data_set in self.data_set_list:
            if 'fill' in data_set['line'].keys():
                fill_params = data_set['line']['fill']
                self.axes.fill_between(data_set['x'], data_set['y'], label=data_set['name'], **fill_params)
            elif 'bar' in data_set['line'].keys():
                bar_params = data_set['line']['bar']
                self.axes.bar(data_set['x'], data_set['y'], label=data_set['name'], **bar_params)
            else:
                self.axes.plot(data_set['x'], data_set['y'], label=data_set['name'], **data_set['line'])

    def add_data_point_labels(self, x_coord_list, y_coord_list, labels):
        data_point_list = list(zip(x_coord_list, y_coord_list))
        data_labels = list(zip(data_point_list, labels))
        self.data_labels.extend(data_labels)

    def draw_graph(self):
        self._plot()
        if self.legend_loc is not None: self.axes.legend(loc=self.legend_loc)
        if self.x_ticks is not None:
            self.axes.set_xticks(self.x_ticks)
            self.axes.set_xlim(self.x_ticks[0], self.x_ticks[-1])
        if self.y_ticks is not None:
            self.axes.set_yticks(self.y_ticks)
            self.axes.set_ylim(self.y_ticks[0], self.y_ticks[-1])
        if self.time_axis is not None:
            self.axes.xaxis.set_major_locator(self.major_time_locator)
            self.axes.xaxis.set_major_formatter(self.major_time_formatter)
            self.axes.xaxis.set_minor_locator(self.minor_time_locator)
            self.axes.set_xlim(self.date_min, self.date_max)
            self.figure.autofmt_xdate()
        if self.data_labels:
            for data_point, label in self.data_labels:
                self.axes.annotate(
                    label,
                    xy=data_point, xycoords='data',
                    xytext=(0, 10), textcoords='offset points',
                    horizontalalignment='center'
                )

    def save_graph(self, name, folder_path=None):
        if folder_path is None: folder_path = os.getcwd()
        file_path = os.path.join(folder_path, name + '.png')
        self.figure.savefig(file_path, bbox_inches='tight')
        plt.close(self.figure)

    @staticmethod
    def show_graph():
        plt.show()


class MultiGraph:
    def __init__(self, row_num, col_num, fig_size=None, dpi=None):
        self.graph_list = []
        self.figure = plt.figure(figsize=fig_size, dpi=dpi)
        self.ax_array = self.figure.subplots(row_num, col_num)
        for i in range(row_num):
            if col_num == 1:
                self.graph_list.append(Graph(self.figure, self.ax_array[i]))
            else:
                for j in range(col_num):
                    self.graph_list.append(Graph(self.figure, self.ax_array[i, j]))
        self.figure.subplots_adjust(wspace=0.3, hspace=0.3)

    def get_graph(self, graph_id):
        return self.graph_list[graph_id - 1]

    def __getitem__(self, graph_id):
        return self.graph_list[graph_id - 1]

    def set_title(self, title):
        self.figure.suptitle(title)

    @staticmethod
    def show_graph():
        plt.tight_layout()
        plt.show()


def fast_plot(x, y):
    g = Graph()
    g.add_data_set('', x, y)
    g.turn_grid_on()
    g.draw_graph()
    g.show_graph()


class SemiLogXGraph(Graph):
    def _plot(self):
        for data_set in self.data_set_list:
            self.axes.semilogx(data_set['x'], data_set['y'], label=data_set['name'], **data_set['line'])
