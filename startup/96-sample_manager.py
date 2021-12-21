
from PyQt5 import uic, QtGui, QtCore, QtWidgets
from PyQt5.Qt import Qt



class Sample:
    def __init__(self, name, comments = None, coords = None):
        self.name = name
        self.comments = comments
        if coords is not None:
            if (any(isinstance(element, list) for element in coords) and
                    any(len(element) == 4 for element in coords)):
                self.coords = coords
            else:
                print('ERROR: Incorrect list of coordinates!')
                self.coords = []

    def sample_to_dict(self):
        sample = {}
        sample['name'] = self.name
        sample['comments'] = self.comments
        sample['coords'] = self.coords
        return sample

    def add_coord(self, coord):
        if (isinstance(coord, list) and (len(coord) == 4 )):
            self.coords.append(coord)
        else:
            print('ERROR: Incorrect coordinates!')

class SampleManager:
    def __init__(self,):
        self.samples = []

    def add_sample(self, sample):
        self.samples.append(sample)

sample_manager = SampleManager()
