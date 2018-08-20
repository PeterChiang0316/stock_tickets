import json, pickle, time, os, collections, StringIO
from collections import OrderedDict

def pickle_load(filename):
    '''
    :param filename: the pickle filename
    :return: the dictionary that store date
    '''
    if not os.path.exists(filename):
        return None

    with open(filename, 'rb') as f:
        data = f.read().replace(b'\r\n', b'\n')
        output = StringIO.StringIO(data)
        data = pickle.load(output)

    return data

def convert_dict_to_json(file_path):
    basename, file_extension = os.path.splitext(file_path)
    with open('%s.json' % basename, 'w') as fjson:
        data = pickle_load(file_path)
        json.dump(data, fjson, ensure_ascii=False, sort_keys=True, indent=4)

for subdir, dirs, files in os.walk(".."):
    for file in files:
        filepath = os.path.join(subdir, file)
        basename, file_extension = os.path.splitext(filepath)
        if 'pickle' in file_extension:
            convert_dict_to_json(filepath)
            print filepath, 'done'