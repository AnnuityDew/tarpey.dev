# import native Python packages
import functools
import io
import base64

# import third party packages
from flask import Blueprint, render_template, request


ddr_bp = Blueprint('ddr', __name__, url_prefix='/ddr')


@ddr_bp.route('/', methods=['GET', 'POST'])
@ddr_bp.route('/home', methods=['GET', 'POST'])
def home():
    return render_template(
        'ddr/home.html',
    )


def which_save_file(lookup):
    save_folder_path = os.path.join(
        os.getcwd(),
        'data',
        'ddr',
    )
    
    save_file_dictionary = {
        'max_jp': os.path.join(save_folder_path, 'BISLPM-62154system'),
        'max2_jp': os.path.join(save_folder_path, 'BISLPM-65277system'),
        'ex_jp': os.path.join(save_folder_path, 'BISLPM-65358system'),
        'max_us': os.path.join(save_folder_path, 'BASLUS-20437system'),
        'max2_us': os.path.join(save_folder_path, 'BASLUS-20711system'),
        'ex_us': os.path.join(save_folder_path, 'BASLUS-20916system'),
        'ex2_us': os.path.join(save_folder_path, 'BASLUS-21174system'),
        'sn_us': os.path.join(save_folder_path, 'BASLUS-21377system'),
        'sn2_us': os.path.join(save_folder_path, 'BASLUS-21608system'),
        'x_us': os.path.join(save_folder_path, 'BASLUS-21767system'),
    }

    return save_file_dictionary[lookup]


def read_max2_us_save():
    with open(which_save_file('max2_us'), 'rb') as max2_us:
        hex_list = ["{:02x}".format(ord(c)) for c in fp.read()]
        test = max2_us.read()


def read_max_us_save():
    save_file_path = os.path.join(
        os.getcwd(),
        'data'
    )
