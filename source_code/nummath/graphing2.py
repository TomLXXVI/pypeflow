import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter


class Axis:
    def __init__(self, axes):
        self._axes = axes
        self.label = None
        self.ticks = None

    @property
    def axes(self):
        return self._axes

    def set_title(self, label):
        pass

    def scale(self, lim_down, lim_up, step_size):
        step_size = abs(step_size)
        self.ticks = [lim_down]
        i = 1
        if lim_down < lim_up:
            while self.ticks[-1] < lim_up:
                self.ticks.append(lim_down + i * step_size)
                i += 1
        else:
            while self.ticks[-1] > lim_up:
                self.ticks.append(lim_down - i * step_size)
                i += 1

    def _format_xticks(self, fmt_str='%.2f'):
        self._axes.xaxis.set_major_formatter(FormatStrFormatter(fmt_str))

    def _format_yticks(self, fmt_str='%.2f'):
        self._axes.yaxis.set_major_formatter(FormatStrFormatter(fmt_str))


class PrimaryXAxis(Axis):
    def set_title(self, label):
        self._axes.set_xlabel(label)

    def scale(self, lim_down, lim_up, step_size):
        super().scale(lim_down, lim_up, step_size)
        self._axes.set_xticks(self.ticks)
        self._axes.set_xlim(self.ticks[0], self.ticks[-1])

    def format_ticks(self, fmt_str='%.2f'):
        self._format_xticks(fmt_str)


class SecondaryXAxis(Axis):
    def __init__(self, axes):
        super().__init__(axes)
        self._axes2 = axes.twiny()
        self._axes2.xaxis.set_ticks_position('bottom')
        self._axes2.xaxis.set_label_position('bottom')
        self._axes2.spines['bottom'].set_position(('outward', 40))

    @property
    def axes(self):
        return self._axes2

    def set_title(self, label):
        self._axes2.set_xlabel(label)

    def scale(self, lim_down, lim_up, step_size):
        super().scale(lim_down, lim_up, step_size)
        self._axes2.set_xticks(self.ticks)
        self._axes2.set_xlim(self.ticks[0], self.ticks[-1])

    def format_ticks(self, fmt_str='%.2f'):
        self._axes2.xaxis.set_major_formatter(FormatStrFormatter(fmt_str))


class PrimaryYAxis(Axis):
    def set_title(self, label):
        self._axes.set_ylabel(label)

    def scale(self, lim_down, lim_up, step_size):
        super().scale(lim_down, lim_up, step_size)
        self._axes.set_yticks(self.ticks)
        self._axes.set_ylim(self.ticks[0], self.ticks[-1])

    def format_ticks(self, fmt_str='%.2f'):
        self._format_yticks(fmt_str)


class SecondaryYAxis(Axis):
    def __init__(self, axes):
        super().__init__(axes)
        self._axes2 = axes.twinx()

    @property
    def axes(self):
        return self._axes2

    def set_title(self, label):
        self._axes2.set_ylabel(label)

    def scale(self, lim_down, lim_up, step_size):
        super().scale(lim_down, lim_up, step_size)
        self._axes2.set_yticks(self.ticks)
        self._axes2.set_ylim(self.ticks[0], self.ticks[-1])

    def _format_yticks(self, fmt_str='%.2f'):
        self._axes2.yaxis.set_major_formatter(FormatStrFormatter(fmt_str))


class TimeAxis:
    def __init__(self, figure, axes):
        self._figure = figure
        self._axes = axes
        self.label = None
        self._time_locator = {
            'auto': mdates.AutoDateLocator,
            'day': mdates.DayLocator,
            'week': mdates.WeekdayLocator,
            'month': mdates.MonthLocator,
            'year': mdates.YearLocator
        }

    def set_title(self, label):
        self._axes.set_xlabel(label)

    def scale(self, date_min, date_max, interval='auto', fmt='%d/%m/%y'):
        # set locator for major ticks
        if interval == 'week':
            major_time_locator = self._time_locator[interval](byweekday=mdates.MO)
            self._axes.xaxis.set_major_locator(major_time_locator)
        else:
            major_time_locator = self._time_locator[interval]()
            self._axes.xaxis.set_major_locator(major_time_locator)
        # set formatter for major tick label
        if interval == 'auto':
            self._axes.xaxis.set_major_formatter(mdates.AutoDateFormatter(major_time_locator))
        else:
            self._axes.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
        # set locator for minor ticks
        self._axes.xaxis.set_minor_locator(self._time_locator['auto']())
        # set time axis limits
        self._axes.set_xlim(date_min, date_max)
        self._figure.autofmt_xdate()


class Graph2D:
    def __init__(self, fig_size=None, dpi=None, padding=1, figure_constructs=None):
        if figure_constructs is not None:
            self._figure = figure_constructs[0]
            self._axes = figure_constructs[1]
        else:
            self._figure = plt.figure(figsize=fig_size, dpi=dpi, tight_layout={'pad': padding})
            self._axes = self._figure.add_subplot(1, 1, 1)
        self.x1 = PrimaryXAxis(self._axes)
        self.x2 = None
        self.y1 = PrimaryYAxis(self._axes)
        self.y2 = None
        self.datasets = {}
        self._legend_on = False
        self._legend_loc = None
        self._legend_ncol = 1
        self._legend_bbox_to_anchor = None

    def add_secondary_x_axis(self):
        self.x2 = SecondaryXAxis(self._axes)

    def add_secondary_y_axis(self):
        self.y2 = SecondaryYAxis(self._axes)

    def add_dataset(self, name, x1_data=None, x2_data=None, y1_data=None, y2_data=None, layout=None):
        if layout is None: layout = {}
        dataset = {'x1': x1_data, 'y1': y1_data, 'x2': x2_data, 'y2': y2_data, 'layout': layout}
        self.datasets[name] = dataset

    def _draw_data(self):
        pass

    def add_legend(self, anchor='center left', anchor_position=(1.01, 0.5), column_count=1):
        """
        Add legend to figure. Without arguments, the legend is positioned in the center at the right side of the
        plot.

        Params:
        -------
        - `anchor` : reference point on legend box ('upper left', 'upper center', 'upper right', 'center right',
                     'lower right', 'lower center', 'lower left', 'center left', 'center', 'best')
        - `anchor_position` : (x, y)-coordinate with respect to axes origin were anchor is positioned
        - `column_count` : the number of columns in the legend box

        """
        self._legend_on = True
        self._legend_loc = anchor
        self._legend_bbox_to_anchor = anchor_position
        self._legend_ncol = column_count

    def _draw_legend(self):
        if self._legend_on:
            self._axes.legend(
                loc=self._legend_loc,
                ncol=self._legend_ncol,
                bbox_to_anchor=self._legend_bbox_to_anchor
            )

    def draw(self, grid_on):
        self._draw_data()
        self._draw_legend()
        self._axes.grid(grid_on)

    def add_title(self, title):
        self._axes.set_title(title)

    def show(self, grid_on=True):
        self.draw(grid_on)
        plt.tight_layout()
        plt.show()

    def save(self, file_name, folder_path=None, grid_on=True, ext='.png'):
        self.draw(grid_on)
        if folder_path is None: folder_path = os.getcwd()
        fp = os.path.join(folder_path, file_name + ext)
        self._figure.savefig(fp, bbox_inches='tight')
        plt.close(self._figure)


class LineGraph(Graph2D):
    def _draw_data(self):
        for name, dataset in self.datasets.items():
            if (dataset['x1'] is not None) and (dataset['y1'] is not None):
                self.y1.axes.plot(dataset['x1'], dataset['y1'], label=name, **dataset['layout'])
            if (dataset['x1'] is not None) and (dataset['y2'] is not None):
                self.y2.axes.plot(dataset['x1'], dataset['y2'], label=name, **dataset['layout'])


class BarGraph(Graph2D):
    def __init__(self, fig_size=None, dpi=None, padding=3, figure_constructs=None):
        super().__init__(fig_size, dpi, padding, figure_constructs)
        self.width = 0.8
        self.align = 'center'
        self.bottom = None

    def set_bar_properties(self, **props):
        self.width = props.get('width', self.width)
        self.align = props.get('align', self.align)
        self.bottom = props.get('bottom', self.bottom)

    def _draw_data(self):
        for i, (name, dataset) in enumerate(self.datasets.items()):
            if (dataset['x1'] is not None) and (dataset['y1'] is not None):
                self.y1.axes.bar(
                    dataset['x1'],
                    dataset['y1'],
                    width=self.width,
                    bottom=self.bottom,
                    align=self.align,
                    label=name,
                    **dataset['layout']
                )
            if (dataset['x1'] is not None) and (dataset['y2'] is not None):
                self.y2.axes.bar(
                    dataset['x1'],
                    dataset['y1'],
                    width=self.width,
                    bottom=self.bottom,
                    align=self.align,
                    label=name,
                    **dataset['layout']
                )


class SemiLogXGraph(Graph2D):
    def _draw_data(self):
        for name, dataset in self.datasets.items():
            if (dataset['x1'] is not None) and (dataset['y1'] is not None):
                self.y1.axes.semilogx(dataset['x1'], dataset['y1'], label=name, **dataset['layout'])
            if (dataset['x1'] is not None) and (dataset['y2'] is not None):
                self.y2.axes.semilogx(dataset['x1'], dataset['y2'], label=name, **dataset['layout'])


class VectorGraph(Graph2D):
    origin = [0.0], [0.0]

    def _draw_data(self):
        for name, dataset in self.datasets.items():
            kwargs = {
                'scale': 1.0,
                'scale_units': 'xy',
                'angles': 'xy',
            }
            kwargs.update(dataset['layout'])
            self.y1.axes.quiver(*self.origin, dataset['x1'], dataset['y1'], label=name, **kwargs)


class PolarGraph:
    def __init__(self, fig_size=None, dpi=None, padding=3):
        self._figure = plt.figure(figsize=fig_size, dpi=dpi, tight_layout={'pad': padding})
        self._axes = self._figure.add_subplot(111, projection='polar')
        self.datasets = {}

    def scale(self, r_max, step_size):
        ticks = [0.0]
        i = 1
        while ticks[-1] < r_max:
            ticks.append(i * step_size)
            i += 1
        self._axes.set_rmax(r_max)
        self._axes.set_rticks(ticks)

    def add_title(self, title):
        self._axes.set_title(title)

    def add_dataset(self, name, r_data=None, phi_data=None, layout=None):
        if layout is None: layout = {}
        dataset = {'r': r_data, 'phi': phi_data, 'layout': layout}
        self.datasets[name] = dataset

    def _draw(self, grid_on):
        for name, dataset in self.datasets.items():
            self._axes.plot(dataset['phi'], dataset['r'], label=name, **dataset['layout'])
        self._axes.grid(grid_on)

    def show(self, grid_on=True):
        self._draw(grid_on)
        plt.show()


class MultiGraph:
    # noinspection PyTypeChecker
    def __init__(self, row_num, col_num, share_x=False, share_y=False, fig_size=None, dpi=None):
        self._figure, self._axes_arr = plt.subplots(
            row_num,
            col_num,
            sharex=share_x,
            sharey=share_y,
            figsize=fig_size,
            dpi=dpi
        )
        self._multi_graph = []
        for r in range(row_num):
            row = []
            if col_num > 1:
                for c in range(col_num):
                    row.append(LineGraph(figure_constructs=(self._figure, self._axes_arr[r, c])))
            elif col_num == 1:
                row.append(LineGraph(figure_constructs=(self._figure, self._axes_arr[r])))
            self._multi_graph.append(row)
        plt.subplots_adjust(wspace=0.3, hspace=0.3)

    def __getitem__(self, index):
        return self._multi_graph[index[0]][index[1]]

    def __setitem__(self, index, graph):
        self._multi_graph[index[0]][index[1]] = graph

    def show(self, grid_on=True):
        for r in range(len(self._multi_graph)):
            row = self._multi_graph[r]
            for c in range(len(row)):
                self._multi_graph[r][c].draw(grid_on)
        plt.tight_layout()
        plt.show()
