

class SpectrometerManager(PersistentListInteractingWithGUI):

    @property
    def configs(self):
        return self.items

    def add_config(self, config):
        self.add_item(config)

johann_spectrometer_manager = SpectrometerManager(json_file_path='/nsls2/data/iss/legacy/xf08id/settings/json/johann_spectrometer_manager')

