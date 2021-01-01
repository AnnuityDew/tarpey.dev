# import native Python packages
from enum import Enum
import os

# import third party packages
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas


# router and templates
ddr_views = APIRouter(prefix="/ddr")
templates = Jinja2Templates(directory='templates')


class PS2DDR(str, Enum):
    MAX_JP = "max_jp"
    MAX2_JP = "max2_jp"
    EX_JP = "ex_jp"
    MAX_US = "max_us"
    MAX2_US = "max2_us"
    EX_US = "ex_us"
    EX2_US = "ex2_us"
    SN_US = "sn_us"
    SN2_US = "sn2_us"
    X_US = "x_us"


@ddr_views.get("/", response_class=HTMLResponse, name="ddr")
async def home(request: Request):
    return templates.TemplateResponse(
        'ddr/home.html',
        context={'request': request},
    )


@ddr_views.get("/{game}", response_class=HTMLResponse)
async def game_info(request: Request, game: PS2DDR):
    game_data = which_save_file(game)
    game_df = game_data.byte_builder()
    return templates.TemplateResponse(
        'ddr/game.html',
        context={
            'request': request,
            'df': game_df,
            'game': game,
        },
    )


def which_save_file(lookup):
    game_data_dictionary = {
        'max_jp': MAXJP(),
        'max2_jp': MAX2JP(),
        'ex_jp': EXJP(),
        'max_us': MAXUS(),
        'max2_us': MAX2US(),
        'ex_us': EXUS(),
        'ex2_us': EX2US(),
        'sn_us': SuperNOVA(),
        'sn2_us': SuperNOVA2(),
        'x_us': DDRX(),
    }

    game_data = game_data_dictionary[lookup]

    return game_data


class GenericSavePS2():
    '''Generic PS2 save data.

    These objects will have three lists of little-endian translations
    of byte objects into integers. A one-byte length list, two byte,
    and four-byte. One-byte lists will probably identify 0/1 flags
    (maybe for something like song unlocks). Two-byte numbers are confirmed
    to contain combo information at least. Four-byte numbers usually contain
    score data for a song or course.

    Each save will also attempt to translate these three lists into
    UTF-8 using decode() (should probably ignore errors).

    Subclasses will inherit from this class and add in their specific
    song and course lists (among other game-specific data).
    '''

    def __init__(self, save_id):
        # read each save file as raw bytes
        self.save_path = os.path.join(
            os.getcwd(),
            'backup',
            'ddr',
            '20200624',
            save_id,
        )
        with open(self.save_path, 'rb') as save_file:
            self.encoded_bytes = save_file.read()
            save_file.close()
        # list comprehensions! build a list of each set of four/two/one bytes
        self.four_byte_list = [self.encoded_bytes[i:i+4] for i in range(0, len(self.encoded_bytes), 4)]
        self.two_byte_list = [self.encoded_bytes[i:i+2] for i in range(0, len(self.encoded_bytes), 2)]
        self.one_byte_list = [self.encoded_bytes[i:i+1] for i in range(0, len(self.encoded_bytes), 1)]
        # another set of list comprehensions.
        # little endian conversion to int of each chunk
        self.four_byte_ints = [int.from_bytes(chunk, byteorder='little') for chunk in self.four_byte_list]
        self.two_byte_ints = [int.from_bytes(chunk, byteorder='little') for chunk in self.two_byte_list]
        self.one_byte_ints = [int.from_bytes(chunk, byteorder='little') for chunk in self.one_byte_list]

    def byte_builder(self):
        '''Construct a generic dictionary and pandas dataframe.'''
        save_data = {}
        for byte in range(0, len(self.four_byte_list), 4):
            save_data[byte] = [4, 'Unknown', None, None, None]

        # for the sections we constructed, append int/hex/bytes for checking/analysis
        for key, info in save_data.items():
            info.append(int.from_bytes(self.encoded_bytes[key:key+info[0]], byteorder='little'))
            info.append(self.encoded_bytes[key:key+info[0]].hex())
            info.append(self.encoded_bytes[key:key+info[0]])

        # convert to pandas dataframe
        save_df = pandas.DataFrame.from_dict(
            save_data,
            orient='index',
            columns=['byte_length', 'type', 'song', 'style', 'difficulty', 'value', 'hex_string', 'raw_bytes']
        ).reset_index(
        ).rename(
            columns={'index': 'starting_byte'},
        )

        return save_df


class MAXJP(GenericSavePS2):
    def __init__(self):
        self.save_id = 'BISLPM-62154system'
        super().__init__(self.save_id)


class MAX2JP(GenericSavePS2):
    def __init__(self):
        self.save_id = 'BISLPM-65277system'
        super().__init__(self.save_id)


class EXJP(GenericSavePS2):
    def __init__(self):
        self.save_id = 'BISLPM-65358system'
        super().__init__(self.save_id)


class MAXUS(GenericSavePS2):
    def __init__(self):
        self.save_id = 'BASLUS-20437system'
        super().__init__(self.save_id)


class MAX2US(GenericSavePS2):
    def __init__(self):
        self.save_id = 'BASLUS-20711system'
        super().__init__(self.save_id)

    def byte_builder(self):
        # empty dictionary to begin mapping bytes
        max2_us_data = {}

        # bytes 0-79 (not sure what these are)
        # break up into chunks of 4 for now
        for byte in range(0, 80, 4):
            max2_us_data[byte] = [4, 'Unknown', None, None, None]

        # bytes 80-9833 (game mode scoreboard)
        song_list = [
            'Still In My Heart',
            'TSUGARU',
            'KAKUMEI',
            'MAXX UNLIMITED',
            'DIVE (more deep and deeper style)',
            'rain of sorrow',
            'Burning Heat!',
            'D2R',
            'i feel...',
            'Vanity Angel',
            'xenon',
            'feeling of love',
            'DESTINY',
            'Radical Faith',
            'BREAK DOWN !',
            'Tomorrow Perfume',
            'more deep',
            'Keep On Liftin\'',
            'Bad Routine',
            'Try 2 Luv U',
            'I Need You',
            'Forever Sunshine',
            'AFRONOVA',
            'SP-TRIP MACHINE (JUNGLE MIX)',
            'PARANOIA KCET (clean mix)',
            'Don\'t Stop!',
            'END OF THE CENTURY',
            'Groove',
            'Secret Rendezvous',
            'Can\'t Stop Fallin\' In Love',
            'Do It Right',
            'AM-3P',
            'CELEBRATE NITE',
            'HYSTERIA',
            'Kind Lady',
            'Silent Hill',
            'SUPER STAR',
            'think ya better D',
            'JAM&MARMALADE',
            'The Shining Polaris',
            'I Was The One',
            'Spin the disc',
            'AM-3P AM East',
            'Celebrate Nite Euro Trance Style',
            'Do It Right (80\'s Electro Mix)',
            'Hysteria 2001',
            'Kind Lady (interlude)',
            'Silent Hill (3rd Christmas Mix)',
            'Super Star (FROM NONSTOP MEGAMIX)',
            'Will I?',
            'Take Me Away',
            'Heaven',
            'A Little Bit of Ecstasy',
            'Love At First Sight',
            'Get Down Tonight',
            'Days Go By',
            'Busy Child',
            'DRIFTING AWAY',
            'The Whistle Song',
            'TWILIGHT ZONE',
            'GHOSTS',
            'IN THE NAVY \'99',
            'CONGA FEELING',
            'DREAM A DREAM',
            'Let\'s Groove',
            'SO DEEP (PERFECT SPHERE REMIX)',
            'LOVIN YOU',
            'Long Train Runnin\'',
        ]

        # let's try a byte lookup approach. start byte and length, then info
        # data for the other songs is evenly spaced 144 bytes apart,
        # so we can construct the rest of the dictionary here with a loop over the song list
        i = 0
        for song in song_list:
            max2_us_data[80+144*i] = [4, 'Score', song, 'Single', 'Beginner']
            max2_us_data[84+144*i] = [4, 'Score', song, 'Single', 'Light']
            max2_us_data[88+144*i] = [4, 'Score', song, 'Single', 'Standard']
            max2_us_data[92+144*i] = [4, 'Score', song, 'Single', 'Heavy']
            max2_us_data[96+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[100+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[104+144*i] = [4, 'Score', song, 'Double', 'Light']
            max2_us_data[108+144*i] = [4, 'Score', song, 'Double', 'Standard']
            max2_us_data[112+144*i] = [4, 'Score', song, 'Double', 'Heavy']
            max2_us_data[116+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[120+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[124+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[128+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[132+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[136+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[140+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[144+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[148+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[152+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[156+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[160+144*i] = [4, 'Play Count', song, 'All', 'All']
            max2_us_data[164+144*i] = [2, 'Unknown', None, None, None]
            max2_us_data[166+144*i] = [2, 'Combo', song, 'Single', 'Beginner']
            max2_us_data[168+144*i] = [2, 'Combo', song, 'Single', 'Light']
            max2_us_data[170+144*i] = [2, 'Combo', song, 'Single', 'Standard']
            max2_us_data[172+144*i] = [2, 'Combo', song, 'Double', 'Heavy']
            max2_us_data[174+144*i] = [2, 'Unknown', song, 'Double', 'Challenge']
            max2_us_data[176+144*i] = [2, 'Combo', None, None, None]
            max2_us_data[178+144*i] = [2, 'Combo', song, 'Double', 'Light']
            max2_us_data[180+144*i] = [2, 'Combo', song, 'Double', 'Standard']
            max2_us_data[182+144*i] = [2, 'Combo', song, 'Double', 'Heavy']
            max2_us_data[184+144*i] = [2, 'Combo', song, 'Double', 'Challenge']
            max2_us_data[188+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[192+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[196+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[200+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[204+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[208+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[212+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[216+144*i] = [4, 'Unknown', None, None, None]
            max2_us_data[220+144*i] = [4, 'Unknown', None, None, None]
            i = i + 1

        # bytes 9834-11823 (not sure what these are)
        # break up into chunks of 4 for now
        for byte in range(9834, 11824, 4):
            max2_us_data[byte] = [4, 'Unknown', None, None, None]

        # bytes 11824-12887
        # nonstop mode scoreboard
        course_list = [
            'LIGHT NAOKI',
            'Hit Station',
            'Feel Emotion',
            'In Motion',
            'Say Yeah!',
            'Globetrotting',
            'RMX of LOVE',
            'DJ Battle',
            'RMX of TRUTH',
            'Mega Dance Hits',
            'Boogie Down',
            'RAP MANIA',
            'Trancendence',
            'House Nights',
            'Ultimate 12',
            'Player\'s Best 1-4',
            'Player\'s Best 5-8',
            'Random CAPRICE',
            'Random',
        ]

        # let's try a byte lookup approach. start byte and length, then info
        # data for the other courses is evenly spaced 56 bytes apart,
        # so we can construct the rest of the dictionary here with a loop over the course list
        i = 0
        for course in course_list:
            max2_us_data[11824+56*i] = [4, 'Score', course, 'Single', 'Normal']
            max2_us_data[11828+56*i] = [4, 'Score', course, 'Single', 'Difficult']
            max2_us_data[11832+56*i] = [4, 'Score', course, 'Double', 'Normal']
            max2_us_data[11836+56*i] = [4, 'Score', course, 'Double', 'Difficult']
            max2_us_data[11840+56*i] = [4, 'Unknown', None, None, None]
            max2_us_data[11844+56*i] = [4, 'Unknown', None, None, None]
            max2_us_data[11848+56*i] = [2, 'Combo', course, 'Single', 'Normal']
            max2_us_data[11850+56*i] = [2, 'Combo', course, 'Single', 'Difficult']
            max2_us_data[11852+56*i] = [2, 'Combo', course, 'Double', 'Normal']
            max2_us_data[11854+56*i] = [2, 'Combo', course, 'Double', 'Difficult']
            max2_us_data[11856+56*i] = [4, 'Unknown', None, None, None]
            max2_us_data[11860+56*i] = [4, 'Unknown', None, None, None]
            max2_us_data[11864+56*i] = [4, 'Unknown', None, None, None]
            max2_us_data[11868+56*i] = [4, 'Unknown', None, None, None]
            max2_us_data[11872+56*i] = [4, 'Unknown', None, None, None]
            max2_us_data[11876+56*i] = [4, 'Unknown', None, None, None]
            i = i + 1

        # bytes 12888-13627 (not sure what these are)
        # break up into chunks of 4 for now
        for byte in range(12888, 13627, 4):
            max2_us_data[byte] = [4, 'Unknown', None, None, None]

        # bytes 13628-14175 (some sort of counter)
        # break up into chunks of 4 for now
        for byte in range(13628, 14176, 4):
            max2_us_data[byte] = [4, 'Another Play Counter?', None, None, None]

        # bytes 14176-15363 (not sure what these are)
        # break up into chunks of 4 for now
        for byte in range(14176, 15364, 4):
            max2_us_data[byte] = [4, 'Unknown', None, None, None]

        # bytes 15364-15571 (endless data)
        max2_us_data[15364] = [4, '1st Rank 1st Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15368] = [4, '1st Rank 2nd Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15372] = [4, '1st Rank Combo', 'Endless', 'Single', 'NONREG']
        max2_us_data[15376] = [4, '1st Rank Stages', 'Endless', 'Single', 'NONREG']
        max2_us_data[15380] = [4, '2nd Rank 1st Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15384] = [4, '2nd Rank 2nd Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15388] = [4, '2nd Rank Combo', 'Endless', 'Single', 'NONREG']
        max2_us_data[15392] = [4, '2nd Rank Stages', 'Endless', 'Single', 'NONREG']
        max2_us_data[15396] = [4, '3rd Rank 1st Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15400] = [4, '3rd Rank 2nd Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15404] = [4, '3rd Rank Combo', 'Endless', 'Single', 'NONREG']
        max2_us_data[15408] = [4, '3rd Rank Stages', 'Endless', 'Single', 'NONREG']
        max2_us_data[15412] = [4, '1st Rank 1st Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15416] = [4, '1st Rank 2nd Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15420] = [4, '1st Rank Combo', 'Endless', 'Double', 'NONREG']
        max2_us_data[15424] = [4, '1st Rank Stages', 'Endless', 'Double', 'NONREG']
        max2_us_data[15428] = [4, '2nd Rank 1st Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15432] = [4, '2nd Rank 2nd Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15436] = [4, '2nd Rank Combo', 'Endless', 'Double', 'NONREG']
        max2_us_data[15440] = [4, '2nd Rank Stages', 'Endless', 'Double', 'NONREG']
        max2_us_data[15444] = [4, '3rd Rank 1st Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15448] = [4, '3rd Rank 2nd Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15452] = [4, '3rd Rank Combo', 'Endless', 'Double', 'NONREG']
        max2_us_data[15456] = [4, '3rd Rank Stages', 'Endless', 'Double', 'NONREG']
        max2_us_data[15460] = [4, '1st Rank 1st Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15464] = [4, '1st Rank 2nd Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15468] = [4, '1st Rank Combo', 'Endless', 'Single', 'NONREG']
        max2_us_data[15472] = [4, '1st Rank Stages', 'Endless', 'Single', 'NONREG']
        max2_us_data[15476] = [4, '2nd Rank 1st Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15480] = [4, '2nd Rank 2nd Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15484] = [4, '2nd Rank Combo', 'Endless', 'Single', 'NONREG']
        max2_us_data[15488] = [4, '2nd Rank Stages', 'Endless', 'Single', 'NONREG']
        max2_us_data[15492] = [4, '3rd Rank 1st Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15496] = [4, '3rd Rank 2nd Half', 'Endless', 'Single', 'NONREG']
        max2_us_data[15500] = [4, '3rd Rank Combo', 'Endless', 'Single', 'NONREG']
        max2_us_data[15504] = [4, '3rd Rank Stages', 'Endless', 'Single', 'NONREG']
        max2_us_data[15508] = [4, '1st Rank 1st Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15512] = [4, '1st Rank 2nd Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15516] = [4, '1st Rank Combo', 'Endless', 'Double', 'NONREG']
        max2_us_data[15520] = [4, '1st Rank Stages', 'Endless', 'Double', 'NONREG']
        max2_us_data[15524] = [4, '2nd Rank 1st Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15528] = [4, '2nd Rank 2nd Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15532] = [4, '2nd Rank Combo', 'Endless', 'Double', 'NONREG']
        max2_us_data[15536] = [4, '2nd Rank Stages', 'Endless', 'Double', 'NONREG']
        max2_us_data[15540] = [4, '3rd Rank 1st Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15544] = [4, '3rd Rank 2nd Half', 'Endless', 'Double', 'NONREG']
        max2_us_data[15548] = [4, '3rd Rank Combo', 'Endless', 'Double', 'NONREG']
        max2_us_data[15552] = [4, '3rd Rank Stages', 'Endless', 'Double', 'NONREG']
        max2_us_data[15556] = [4, '3rd Rank 1st Half', 'Endless', 'Single', 'Regulation']
        max2_us_data[15560] = [4, '3rd Rank 2nd Half', 'Endless', 'Single', 'Regulation']
        max2_us_data[15564] = [4, '1st Rank Combo', 'Endless', 'Single', 'NONREG']
        max2_us_data[15568] = [4, '1st Rank Stages', 'Endless', 'Single', 'NONREG']

        # bytes 15572-end of file (not sure what these are)
        # break up into chunks of 4 for now
        for byte in range(15572, len(self.encoded_bytes), 4):
            max2_us_data[byte] = [4, 'Unknown', None, None, None]

        # for the sections we constructed, append int/hex/bytes for checking/analysis
        for key, info in max2_us_data.items():
            info.append(int.from_bytes(self.encoded_bytes[key:key+info[0]], byteorder='little'))
            info.append(self.encoded_bytes[key:key+info[0]].hex())
            info.append(self.encoded_bytes[key:key+info[0]])

        # convert to pandas dataframe
        max2_us_df = pandas.DataFrame.from_dict(
            max2_us_data,
            orient='index',
            columns=['byte_length', 'type', 'song', 'style', 'difficulty', 'value', 'hex_string', 'raw_bytes']
        ).reset_index(
        ).rename(
            columns={'index': 'starting_byte'},
        )

        return max2_us_df


class EXUS(GenericSavePS2):
    def __init__(self):
        self.save_id = 'BASLUS-20916system'
        super().__init__(self.save_id)


class EX2US(GenericSavePS2):
    def __init__(self):
        self.save_id = 'BASLUS-21174system'
        super().__init__(self.save_id)


class SuperNOVA(GenericSavePS2):
    def __init__(self):
        self.save_id = 'BASLUS-21377system'
        super().__init__(self.save_id)


class SuperNOVA2(GenericSavePS2):
    def __init__(self):
        self.save_id = 'BASLUS-21608system'
        super().__init__(self.save_id)


class DDRX(GenericSavePS2):
    def __init__(self):
        self.save_id = 'BASLUS-21767system'
        super().__init__(self.save_id)
