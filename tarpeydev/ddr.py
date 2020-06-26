# import native Python packages
import functools
import io
import base64

# import third party packages
from flask import Blueprint, render_template, request
from google.cloud import storage

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
        '20200624',
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

    # initialize Google Cloud Storage
    # client = storage.Client()
    # choose the bucket for the site
    # bucket = client.get_bucket(os.environ['DATA_BUCKET'])
    # find the requested file
    # google_save_folder = 'data/ddr/20200624/'
    # google_save_files = {
    #     'max_jp': google_save_folder + 'BISLPM-62154system',
    #     'max2_jp': google_save_folder + 'BISLPM-65277system',
    #     'ex_jp': google_save_folder + 'BISLPM-65358system',
    #     'max_us': google_save_folder + 'BASLUS-20437system',
    #     'max2_us': google_save_folder + 'BASLUS-20711system',
    #     'ex_us': google_save_folder + 'BASLUS-20916system',
    #     'ex2_us': google_save_folder + 'BASLUS-21174system',
    #     'sn_us': google_save_folder + 'BASLUS-21377system',
    #     'sn2_us': google_save_folder + 'BASLUS-21608system',
    #     'x_us': google_save_folder + 'BASLUS-21767system',
    # }

    # return bucket.get_blob(google_save_files[lookup]).download_as_string()

    # open the save as raw bytes
    with open(save_file_dictionary[lookup], 'rb') as save_file:
        encoded_bytes = save_file.read()

    # list comprehension!!! build a list of each set of four bytes
    # encoded_bytes_four = [encoded_bytes[i:i+4] for i in range(0, len(encoded_bytes), 4)]
    # same but by 2s
    # encoded_bytes_two = [encoded_bytes[i:i+2] for i in range(0, len(encoded_bytes), 2)]

    # another list comprehension. little endian conversion to int of each chunk
    # four_chunk_list = [int.from_bytes(chunk, byteorder='little') for chunk in encoded_bytes_four]
    # same but by 2s
    # two_chunk_list = [int.from_bytes(chunk, byteorder='little') for chunk in encoded_bytes_two]

    return encoded_bytes


def read_max2_us_save():
    # fetch chunk list (contains most scores)
    encoded_bytes = which_save_file('max2_us')

    # let's try a byte lookup approach. start byte and length, then info
    byte_lookup = {
        80: [4, 'Score', 'Still In My Heart', 'Single', 'Beginner'],
        84: [4, 'Score', 'Still In My Heart', 'Single', 'Light'],
        88: [4, 'Score', 'Still In My Heart', 'Single', 'Standard'],
        92: [4, 'Score', 'Still In My Heart', 'Single', 'Heavy'],
        96: [4, 'Unknown', None, None, None],
        100: [4, 'Unknown', None, None, None],
        104: [4, 'Score', 'Still In My Heart', 'Double', 'Light'],
        108: [4, 'Score', 'Still In My Heart', 'Double', 'Standard'],
        112: [4, 'Score', 'Still In My Heart', 'Double', 'Heavy'],
        116: [4, 'Unknown', None, None, None],
        120: [4, 'Unknown', None, None, None],
        124: [4, 'Unknown', None, None, None],
        128: [4, 'Unknown', None, None, None],
        132: [4, 'Unknown', None, None, None],
        136: [4, 'Unknown', None, None, None],
        140: [4, 'Unknown', None, None, None],
        144: [4, 'Unknown', None, None, None],
        148: [4, 'Unknown', None, None, None],
        152: [4, 'Unknown', None, None, None],
        156: [4, 'Unknown', None, None, None],
        160: [4, 'Play Count', 'Still In My Heart', 'All', 'All'],
        164: [2, 'Unknown', None, None, None],
        166: [2, 'Combo', 'Still In My Heart', 'Single', 'Beginner'],
        168: [2, 'Combo', 'Still In My Heart', 'Single', 'Light'],
        170: [2, 'Combo', 'Still In My Heart', 'Single', 'Standard'],
        172: [2, 'Combo', 'Still In My Heart', 'Double', 'Heavy'],
        174: [2, 'Unknown', 'Still In My Heart', 'Double', 'Challenge'],
        176: [2, 'Combo', None, None, None],
        178: [2, 'Combo', 'Still In My Heart', 'Double', 'Light'],
        180: [2, 'Combo', 'Still In My Heart', 'Double', 'Standard'],
        182: [2, 'Combo', 'Still In My Heart', 'Double', 'Heavy'],
        184: [2, 'Combo', 'Still In My Heart', 'Double', 'Challenge'],
        224: [4, 'Score', 'TSUGARU', 'Single', 'Beginner'],
        228: [4, 'Score', 'TSUGARU', 'Single', 'Light'],
        232: [4, 'Score', 'TSUGARU', 'Single', 'Standard'],
        236: [4, 'Score', 'TSUGARU', 'Single', 'Heavy'],
        240: [4, 'Unknown', None, None, None],
        244: [4, 'Unknown', None, None, None],
        248: [4, 'Score', 'TSUGARU', 'Double', 'Light'],
        252: [4, 'Score', 'TSUGARU', 'Double', 'Standard'],
        256: [4, 'Score', 'TSUGARU', 'Double', 'Heavy'],
        260: [4, 'Unknown', None, None, None],
        264: [4, 'Unknown', None, None, None],
        268: [4, 'Unknown', None, None, None],
        272: [4, 'Unknown', None, None, None],
        276: [4, 'Unknown', None, None, None],
        280: [4, 'Unknown', None, None, None],
        284: [4, 'Unknown', None, None, None],
        288: [4, 'Unknown', None, None, None],
        292: [4, 'Unknown', None, None, None],
        296: [4, 'Unknown', None, None, None],
        300: [4, 'Unknown', None, None, None],
        304: [4, 'Play Count', 'TSUGARU', 'All', 'All'],
        308: [2, 'Combo', None, None, None],
        310: [2, 'Combo', 'TSUGARU', 'Single', 'Beginner'],
        312: [2, 'Combo', 'TSUGARU', 'Single', 'Light'],
        314: [2, 'Combo', 'TSUGARU', 'Single', 'Standard'],
        316: [2, 'Combo', 'TSUGARU', 'Double', 'Heavy'],
        318: [2, 'Combo', 'TSUGARU', 'Double', 'Challenge'],
        320: [2, 'Combo', None, None, None],
        322: [2, 'Combo', 'TSUGARU', 'Double', 'Light'],
        324: [2, 'Combo', 'TSUGARU', 'Double', 'Standard'],
        326: [2, 'Combo', 'TSUGARU', 'Double', 'Heavy'],
        328: [2, 'Combo', 'TSUGARU', 'Double', 'Challenge'],
    }

    for key, info in byte_lookup.items():
        info.append(int.from_bytes(encoded_bytes[key:key+info[0]], byteorder='little'))
        info.append(encoded_bytes[key:key+info[0]].hex())
        info.append(encoded_bytes[key:key+info[0]])

    max2_data = pandas.DataFrame.from_dict(
        byte_lookup,
        orient='index',
        columns=['byte_length', 'type', 'song', 'style', 'difficulty', 'value', 'hex_string', 'raw_bytes']
    ).reset_index(
    ).rename(
        columns={'index': 'starting_byte'},
    )

    return max2_data


def read_max_us_save():
    return None
