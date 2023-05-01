

class SpectrometerManager(PersistentListInteractingWithGUI):

    @property
    def configs(self):
        return self.items

    def add_config(self, config_dict):
        self.add_item(config_dict)

    def add_current_config(self, name, timestamp):
        config_dict = {'name': name, 'timestamp': timestamp, 'config': copy.deepcopy(rowland_circle.config)}
        self.add_config(config_dict)

    def set_config_by_index(self, config_index):
        config_dict = self.configs[config_index]
        config = config_dict['config']
        rowland_circle.set_spectrometer_config(config)
        rowland_circle.save_current_spectrometer_config_to_settings()

johann_spectrometer_manager = SpectrometerManager(json_file_path='/nsls2/data/iss/legacy/xf08id/settings/json/johann_spectrometer_manager')

