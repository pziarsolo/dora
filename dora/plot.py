from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import seaborn as sns

BAR = 'bar'
LINE = 'line'


def get_fig_and_canvas(num_rows=1, num_cols=1, figsize=None):
    if figsize is None:
        height = 5.0 * num_rows
        width = 7.5 * num_cols
        if height > 320.0:
            height = 320.0
        figsize = (width, height)

    fig = Figure(figsize=figsize)
    canvas = FigureCanvas(fig)
    return fig, canvas


class HistogramPlotter(object):

    def __init__(self, counters, plots_per_chart=1, kind=LINE, num_cols=1,
                 xlabel=None, ylabel=None, ylog_scale=False, ylimits=None,
                 distrib_labels=None, titles=None, xmax=None, xmin=None,
                 linestyles=None, figsize=None, xtickslabel_rotation=None):
        if plots_per_chart > 1 and kind == BAR:
            error_msg = 'if kind is BAR only one plot per chart is allowed'
            raise ValueError(error_msg)
        self.kind = kind
        self.counters = counters
        self.num_cols = num_cols
        self.plots_per_chart = plots_per_chart
        self.ylog_scale = ylog_scale
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.num_plots, self.num_rows = self._get_plot_dimensions()
        fig, canvas = get_fig_and_canvas(num_rows=self.num_rows,
                                         num_cols=self.num_cols,
                                         figsize=figsize)
        self.figure = fig
        self.canvas = canvas
        axes = self._draw_plot(distrib_labels=distrib_labels, ylimits=ylimits,
                               titles=titles, xmax=xmax, xmin=xmin,
                               linestyles=linestyles,
                               xtickslabel_rotation=xtickslabel_rotation)
        self.axes = axes

    def _get_plot_dimensions(self):
        num_plots, mod = divmod(len(self.counters), self.plots_per_chart)
        if mod != 0:
            num_plots += 1

        num_rows, mod = divmod(num_plots, self.num_cols)
        if mod != 0:
            num_rows += 1
        return num_plots, num_rows

    def write_figure(self, fhand):
        self.canvas.print_figure(fhand, format='png')
        fhand.flush()

    def _draw_histogram_in_axe(self, counter, axe, xmax=None, xmin=None,
                               title=None, distrib_label=None, linestyle=None,
                               ylimits=None, xtickslabel_rotation=None):

        try:
            distrib = calculate_distribution(counter, max_=xmax, min_=xmin)
        except RuntimeError:
            axe.set_title(title + ' (NO DATA)')
            return axe
        except AttributeError as error:
            # if distributions is None
            err_msg = "'NoneType' object has no attribute "
            err_msg += "'calculate_distribution'"
            if err_msg in error:
                axe.set_title(title + ' (NO DATA)')
                return axe
            raise
        if distrib is None:
            axe.set_title(title + ' (NO DATA)')
            return axe

        counts = distrib['counts']
        bin_limits = distrib['bin_limits']
        if self.ylog_scale:
            axe.set_yscale('log')

        if self.xlabel:
            axe.set_xlabel(self.xlabel)
        if self.ylabel:
            axe.set_ylabel(self.ylabel)
        if title:
            axe.set_title(title)

        if self.kind == BAR:
            xvalues = range(len(counts))
            axe.bar(xvalues, counts)

            # the x axis label
            xticks_pos = [value + 0.5 for value in xvalues]

            left_val = None
            right_val = None
            xticks_labels = []
            for i, value in enumerate(bin_limits):
                right_val = value
                if left_val is not None:
                    xticks_label = (left_val + right_val) / 2.0
                    if xticks_label >= 10:
                        fmt = '%d'
                    elif xticks_label >= 0.1 and xticks_label < 10:
                        fmt = '%.1f'
                    elif xticks_label < 0.1:
                        fmt = '%.1e'
                    xticks_label = fmt % xticks_label
                    xticks_labels.append(xticks_label)

                left_val = right_val

            # we don't want to clutter the plot
            num_of_xlabels = 15
            step = int(len(counts) / float(num_of_xlabels))
            step = 1 if step == 0 else step
            xticks_pos = xticks_pos[::step]
            xticks_labels = xticks_labels[::step]
            axe.set_xticks(xticks_pos)
            axe.set_xticklabels(xticks_labels, rotation=xtickslabel_rotation)
        elif self.kind == LINE:
            kwargs = {}
            if distrib_label is not None:
                kwargs['label'] = distrib_label
            if linestyle is not None:
                kwargs['linestyle'] = linestyle

            x_values = []
            for index, i in enumerate(bin_limits):
                try:
                    i2 = bin_limits[index + 1]
                except IndexError:
                    break
                x_values.append((i + i2) / 2.0)
            y_values = counts
            axe.plot(x_values, y_values, **kwargs)

        if ylimits is not None:
            axe.set_ylim(ylimits)

        return axe

    def _draw_plot(self, distrib_labels=None, titles=None, xmax=None,
                   xmin=None, linestyles=None, ylimits=None,
                   xtickslabel_rotation=None):
        counter_index = 0
        axes = []
        for plot_num in range(1, self.num_plots + 1):
            axe = self.figure.add_subplot(self.num_rows, self.num_cols,
                                          plot_num)
            for _ in range(self.plots_per_chart):
                try:
                    counter = self.counters[counter_index]
                    if distrib_labels is None:
                        distrib_label = None
                    else:
                        distrib_label = distrib_labels[counter_index]
                    if linestyles is None:
                        linestyle = None
                    else:
                        linestyle = linestyles[counter_index]
                except IndexError:
                    break
                title = titles[counter_index] if titles else None
                self._draw_histogram_in_axe(counter, axe=axe, xmin=xmin,
                                            xmax=xmax, title=title,
                                            distrib_label=distrib_label,
                                            linestyle=linestyle,
                                            ylimits=ylimits,
                                            xtickslabel_rotation=xtickslabel_rotation)
                counter_index += 1

            if distrib_labels is not None:
                axe.legend()
            axes.append(axe)
        return axes


def draw_histogram_in_fhand(counter, fhand, title=None, xlabel=None, xmin=None,
                            xmax=None, ylabel=None, kind=BAR, ylimits=None,
                            ylog_scale=False, figsize=None,
                            xtickslabel_rotation=None):
    'It draws an histogram and if the fhand is given it saves it'
    plot_hist = HistogramPlotter([counter], xlabel=xlabel, ylabel=ylabel,
                                 xmax=xmax, xmin=xmin, titles=[title],
                                 ylimits=ylimits, kind=kind, figsize=figsize,
                                 xtickslabel_rotation=xtickslabel_rotation,
                                 ylog_scale=ylog_scale)
    plot_hist.write_figure(fhand)


def calculate_distribution(counter, bins=None, min_=None, max_=None,
                           outlier_threshold=None):
    'It returns an histogram with the given range and bin'

    distrib = []
    min_, max_ = _calculate_dist_range(counter, min_, max_, outlier_threshold)

    if min_ is None or max_ is None:
        return None
    bin_edges = calculate_bin_edges(counter, min_, max_, bins)
    for bin_index, left_edge in enumerate(bin_edges):
        try:
            rigth_edge = bin_edges[bin_index + 1]
        except IndexError:
            break
        sum_values = 0

        for index2 in sorted(counter.keys()):
            value = counter[index2]
            if index2 > rigth_edge:
                break

            elif (left_edge <= index2 and index2 < rigth_edge or
                  left_edge <= index2 and index2 == max_):
                sum_values += value

        distrib.append(sum_values)
    return {'counts': distrib, 'bin_limits': bin_edges}


def _calculate_dist_range(counter, min_, max_, outlier_threshold):
    'it calculates the range for the histogram'
    if ((min_ is not None or max_ is not None) and
            outlier_threshold is not None):
        msg = 'You can not pass max, min and outlier_threslhosld to '
        msg += 'calculate distribution range'
        raise ValueError(msg)
    if min_ is None:
        min_ = min(counter.keys())
    if max_ is None:
        max_ = max(counter.keys())
    count = sum(counter.values())
    if outlier_threshold:
        left_limit = count * outlier_threshold / 100
        rigth_limit = count - left_limit
        left_value = _get_value_for_index(counter, left_limit)
        rigth_value = _get_value_for_index(counter, rigth_limit)

        if min_ < left_value:
            min_ = left_value
        if max_ > rigth_value:
            max_ = rigth_value
    return min_, max_


def _get_value_for_index(counter, position):
    '''It takes a position and it returns the value for the given index'''
    cum_count = 0
    for index in sorted(counter.keys()):
        count = counter[index]
        cum_count += count
        if position <= cum_count - 1:
            return index
    else:
        if position >= cum_count:
            raise IndexError('You asked for an index beyond the scope')
        return index


def calculate_bin_edges(counter, min_, max_, n_bins=None):
    'It calculates the bin_edges'
    min_bins = 20
    max_bins = 500
    if n_bins is None:
        num_values = int(max_ - min_)
        if num_values == 0:
            n_bins = 1
        elif num_values < min_bins:
            n_bins = num_values
        else:
            n_bins = int(sum(counter.values()) / 10000)
            if n_bins < min_bins:
                n_bins = min_bins
            if n_bins > max_bins:
                n_bins = max_bins
            if n_bins > num_values:
                n_bins = num_values

    # now we can calculate the bin edges
    distrib_span = max_ - min_ if max_ != min_ else 1

    if distrib_span % n_bins:
        distrib_span = distrib_span + n_bins - (distrib_span % n_bins)
    bin_span = distrib_span // n_bins
    bin_edges = [min_ + bin_ * bin_span for bin_ in range(n_bins + 1)]
    return bin_edges


def draw_histogram_in_axe(counter, axe, kind=LINE, xmax=None, xmin=None,
                          title=None, distrib_label=None, linestyle=None,
                          ylimits=None, xlimits=None, xtickslabel_rotation=None,
                          ylog_scale=False, xlabel=None, ylabel=None):
    sns.set_theme(style="whitegrid", palette="pastel")
    try:
        distrib = calculate_distribution(counter, max_=xmax, min_=xmin)
    except RuntimeError:
        axe.set_title(title + ' (NO DATA)')
        return axe
    except AttributeError as error:
        # if distributions is None
        err_msg = "'NoneType' object has no attribute "
        err_msg += "'calculate_distribution'"
        if err_msg in error:
            axe.set_title(title + ' (NO DATA)')
            return axe
        raise
    if distrib is None:
        axe.set_title(title + ' (NO DATA)')
        return axe

    counts = distrib['counts']
    bin_limits = distrib['bin_limits']
    if ylog_scale:
        axe.set_yscale('log')

    if xlabel:
        axe.set_xlabel(xlabel)
    if ylabel:
        axe.set_ylabel(ylabel)
    if title:
        axe.set_title(title)

    if kind == BAR:
        xvalues = range(len(counts))
        axe.bar(xvalues, counts)

        # the x axis label
        xticks_pos = [value + 0.5 for value in xvalues]

        left_val = None
        right_val = None
        xticks_labels = []
        for i, value in enumerate(bin_limits):
            right_val = value
            if left_val is not None:
                xticks_label = (left_val + right_val) / 2.0
                if xticks_label >= 10:
                    fmt = '%d'
                elif xticks_label >= 0.1 and xticks_label < 10:
                    fmt = '%.1f'
                elif xticks_label < 0.1:
                    fmt = '%.1e'
                xticks_label = fmt % xticks_label
                xticks_labels.append(xticks_label)

            left_val = right_val

        # we don't want to clutter the plot
        num_of_xlabels = 15
        step = int(len(counts) / float(num_of_xlabels))
        step = 1 if step == 0 else step
        xticks_pos = xticks_pos[::step]
        xticks_labels = xticks_labels[::step]
        axe.set_xticks(xticks_pos)
        axe.set_xticklabels(xticks_labels, rotation=xtickslabel_rotation)
    elif kind == LINE:
        kwargs = {}
        if distrib_label is not None:
            kwargs['label'] = distrib_label
        if linestyle is not None:
            kwargs['linestyle'] = linestyle

        x_values = []
        for index, i in enumerate(bin_limits):
            try:
                i2 = bin_limits[index + 1]
            except IndexError:
                break
            x_values.append((i + i2) / 2.0)
        y_values = counts
        axe.plot(x_values, y_values, **kwargs)

    if ylimits is not None:
        axe.set_ylim(ylimits)
    if xlimits is not None:
        axe.set_xlim(xmin=xlimits[0], xmax=xlimits[1])

    return axe
