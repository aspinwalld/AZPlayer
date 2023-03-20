import pandas as pd
import json
from datetime import datetime

PLAYLIST_NAME  = '94.12 The Stall'
CUTS_XLSX_NAME = 'cuts.xlsx'
CUTS_JSON_NAME = 'cuts.json'

def open_workbook(f):
    try:
        workbook = pd.read_excel(f)
        return workbook
    except Exception as e:
        print(e)
        return None


def create_cut(data):
    # Create meta object
    meta_obj = {}
    meta_obj['album'] = '' # Album not supported in excel importer
    meta_obj['artist'] = data['artist']
    meta_obj['title'] = data['title']

    # Create timers object
    timer_obj = {}
    timer_obj['_track_begin'] = data['track_s']
    timer_obj['_track_end'] = data['track_e']
    timer_obj['intro_begin'] = data['intro_s']
    timer_obj['intro_end'] = data['intro_e']
    timer_obj['segue_begin'] = data['segue_s']
    timer_obj['segue_end'] = data['segue_e']

    # Create links object
    links_obj = {}

    links_obj['audio'] = data['file']
    links_obj['albumart'] = None

    ui_obj = {}
    ui_obj['text_color'] = data['color']

    if data['topplay'] == 1:
        b_topplay = True
    else:
        b_topplay = False

    cut_obj = {
        'category': data['group'],
        'cut': data['cut'],
        'duration': data['track_e'], # Duration tied to track end marker in the importer...
        'meta': meta_obj,
        'timers': timer_obj,
        'topplay': b_topplay,
        '_links': links_obj,
        '_ui': ui_obj
    }
    print(f'Generated Cut ID {data["cut"]}')
    return cut_obj


def create_cuts(df):
    cuts = {}

    for index, row in df.iterrows():
        cut = create_cut(row)

        if cut == None:
            continue
        
        cuts[cut['cut']] = cut

    return cuts


def create_cutfile(cuts):
    cutfile = {
        'id': CUTS_JSON_NAME,
        'name': PLAYLIST_NAME,
        'created_at': datetime.now().isoformat(),
        'cuts': cuts
    }
    return cutfile



if __name__ == '__main__':
    print(f'Generating {CUTS_JSON_NAME} from {CUTS_XLSX_NAME}...')
    df = open_workbook(CUTS_XLSX_NAME)
    cuts = create_cuts(df)
    struct = create_cutfile(cuts)
    
    with open(CUTS_JSON_NAME, 'w') as f:
        f.write(json.dumps(struct))
    
    print(f'\nCuts file generated with {len(cuts)} cuts. Goodbye!')