import csv
import json
import os
import sys
from collections import OrderedDict
def convert_dict_to_json(file_path):
    basename, file_extension = os.path.splitext(file_path)
    assert file_extension == '.csv', file_extension
    d = OrderedDict()
    with open(file_path) as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            date = row['Date'].replace('-', '')
            d[date] = row
        
    with open('%s.json' % basename, 'w') as fjson:
        json.dump(d, fjson, ensure_ascii=False, sort_keys=True, indent=4)

if __name__ == '__main__':
    print 'Processing %s' % sys.argv[1]
    convert_dict_to_json(sys.argv[1])
    print 'Done'