
import json
import uuid
from PyQt5 import QtGui

class ScanManager():
    def __init__(self, scan_manager_json = '/nsls2/xf08id/settings/json/scan_manager.json'):
        with open(scan_manager_json, 'r') as f:
            self.scan_dict= json.loads(f.read())






    def add_scan(self, new_scan, name, model= None):
        uid = self.check_if_brand_new(new_scan)
        if uid:
            item = QtGui.QStandardItem(name)
            item.uid = uid
            if model:
                parent = model.invisibleRootItem()
                parent.appendRow(item)



    def check_if_brand_new(self, new_scan):
        for uid, scan in self.scan_dict.items():
            if scan['scan_type'] == new_scan['scan_type']:
                scan_parameters = scan['scan_parameters']
                new_scan_parameters = new_scan['scan_parameters']
                keys =  scan_parameters.keys()
                new_keys = new_scan_parameters.keys()
                if all([(new_k in keys) for new_k in new_keys]):
                    parameters_match = True
                    for k in keys:
                        print('>>>>>>>>>>>>>>>>>>>>>>>', k)
                        if (k != 'filename') and (k != 'offset'):
                            if scan_parameters[k] != new_scan_parameters[k]:
                                print(k)
                                parameters_match = False
                                break

                    if parameters_match:
                        dets = scan['detectors']
                        new_dets = new_scan['detectors']
                        if all([d in new_dets for d in dets]):
                            print('SCAN IS OLD')
                            return uid
                        else:
                            new_scan['scan_parameters']['filename'] = scan['scan_parameters']['filename']
                            break

        new_uid = self.make_scan_uid()
        # new_scan['uid'] = new_uid
        print('SCAN IS NEW')
        self.scan_dict[new_uid] = new_scan
        return new_uid

    def make_scan_uid(self):
        return str(uuid.uuid4())[:13]


scan_manager = ScanManager()





