# import native Python packages
import functools
import io
import base64

# import third party packages
from flask import Blueprint, render_template, request
from matplotlib import cm, rcParams
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
import numpy
import pandas
import seaborn


hysx_bp = Blueprint('haveyouseenx', __name__, url_prefix='/haveyouseenx')


@hysx_bp.route('/', methods=['GET', 'POST'])
@hysx_bp.route('/search', methods=['GET', 'POST'])
def search():
    # read backlog and visualizations
    backlog = read_backlog()
    feature_chart = stacked_by_system()

    # generate image from figure and save to buffer
    buffer = io.BytesIO()
    feature_chart.savefig(
        buffer,
        format="png",
        facecolor='black',
    )
    feature_data = base64.b64encode(buffer.getbuffer()).decode("ascii")

    return render_template(
        'haveyouseenx/search.html',
        df=backlog,
        feature=f"<img src='data:image/png;base64,{feature_data}'/>",
    )


@hysx_bp.route('/results', methods=['GET', 'POST'])
def results():
    search_term = request.form['searchterm']
    backlog = read_backlog()
    return render_template(
        'haveyouseenx/results.html',
        df=backlog,
        search_term=search_term,
    )


def read_backlog():
    backlog = pandas.read_csv(
        'data/haveyouseenx/haveyouseenx_annuitydew.csv',
        index_col='id',
    ).convert_dtypes()
    
    return backlog


def create_overall_pie():
    # count by gameStatus
    overall_pie_df = pandas.pivot_table(
        read_backlog(),
        index='gameStatus',
        aggfunc='count',
    )[['gameTitle']]

    # how many colors do we need for pie chart?
    pie_color_count = len(overall_pie_df.index)

    # generate a [0,1] range evenly spaced
    pie_range = range(0, pie_color_count)
    color_list = []
    for number in pie_range:
        color_list.append((number + 1) / pie_color_count)
    # generate the color array
    plasma_colors = cm.plasma(color_list)

    # set up the figure and its axes
    figure = Figure()
    axes = figure.subplots()

    # use the pie function to define pie wedges, text, and colors
    wedges, texts = axes.pie(
        overall_pie_df,
        labels=overall_pie_df.index,
        colors=plasma_colors,
    )

    # set chart title
    axes.set_title("Games by Completion Status")

    # send the figure back to Flask to display
    return figure


def stacked_by_system():
    # read backlog and create a count column
    backlog = read_backlog()
    backlog['count'] = 1

    # pivot table by gameSystem and gameStatus.
    # fill missing values with zeroes

    by_system_df = pandas.pivot_table(
        backlog,
        values='count',
        index='gameSystem',
        columns='gameStatus',
        aggfunc='count',
        fill_value=0,
    )
    
    # sort by the total of each row
    by_system_df = by_system_df.assign(
        sums=by_system_df.sum(axis=1)
    ).sort_values(
        by='sums', ascending=True
    ).drop(
        columns='sums'
    )

    # N = number of systems. for spacing out the bars
    N = len(by_system_df.index)
    # use numpy arange for x locations. evenly spaced out bars
    spacing = numpy.arange(N)

    # set up the figure and its axes
    figure = Figure(
        figsize=(8, 8),
    )
    ax = figure.subplots(
        nrows=1,
        ncols=1,
    )

    # list of statuses (order they will be shown in from left to right)
    status_list = [
        'Wish List',
        'Not Started',
        'Started',
        'Beaten',
        'Completed',
        'Mastered',
        'Infinite',
    ]

    # how many colors do we need for pie chart?
    bar_color_count = len(status_list)

    # generate a [0,1] range evenly spaced
    bar_range = range(0, bar_color_count)
    color_list = []
    for number in bar_range:
        color_list.append((number + 1) / bar_color_count)
    # generate the color array
    color_array = cm.Spectral(color_list)
    # counter for coming loop
    color_counter = 0

    # need to create a default series of zeroes for left_position.
    # this will allow us to make a stacked bar chart.
    left_position = pandas.DataFrame(
        {'position': 0},
        index=by_system_df.index
    )

    # loop over status list to create the chart
    for status in status_list:
        # use the bar function to define each status and where it starts (at the top
        # of the previous bar).
        ax.barh(
            y=spacing,
            width=by_system_df[status],
            tick_label=by_system_df.index,
            left=left_position['position'],
            color=color_array[color_counter],
        )
        # add the previous width to position to get the new left position for the next category
        left_position = left_position.add(
            by_system_df[[status]].rename(columns={status: 'position',})
        )
        # up the color counter
        color_counter = color_counter + 1

    # figure and chart background colors
    figure.set_facecolor('black')
    ax.set_facecolor('black')

    # title and title color
    ax.set_title("Games by Completion Status")
    ax.title.set_color('white')

    # axis colors
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')

    # tick label colors
    ax.tick_params(axis='both', colors='white')

    # add a legend
    ax.legend(status_list, loc='lower right')

    # optimize chart spacing
    figure.tight_layout()

    return figure
