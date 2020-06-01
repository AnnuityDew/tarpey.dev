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


ddr_bp = Blueprint('ddr', __name__, url_prefix='/ddr')


@ddr_bp.route('/', methods=['GET', 'POST'])
@ddr_bp.route('/home', methods=['GET', 'POST'])
def home():
    return render_template(
        'ddr/home.html',
    )
