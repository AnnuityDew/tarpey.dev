# import native Python packages
import functools
import io
import base64

# import third party packages
from flask import Blueprint, render_template, request
import pandas
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.figure import Figure


hysx_bp = Blueprint('haveyouseenx', __name__, url_prefix='/haveyouseenx')


@hysx_bp.route('/', methods=['GET', 'POST'])
@hysx_bp.route('/search', methods=['GET', 'POST'])
def search():
    # read backlog and visualizations
    backlog = read_backlog()
    overall_pie = visualizations()

    # generate image from figure and save to buffer
    buffer = io.BytesIO()
    overall_pie.savefig(buffer, format="png")
    pie_data = base64.b64encode(buffer.getbuffer()).decode("ascii")

    return render_template(
        'haveyouseenx/search.html',
        df=backlog,
        pie=f"<img src='data:image/png;base64,{pie_data}'/>",
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
        'tarpeydev/data/haveyouseenx/haveyouseenx_annuitydew.csv',
        index_col='id',
    ).convert_dtypes()
    
    return backlog


def visualizations():
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
