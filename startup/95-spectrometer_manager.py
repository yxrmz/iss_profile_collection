

class SpectrometerManager(PersistentListInteractingWithGUI):

    @property
    def configs(self):
        return self.items

    def add_config(self, config_dict):
        self.add_item(config_dict)

    def add_current_config(self, name):
        config_dict = {'name': name,
                       'uid': str(uuid.uuid4()),
                       'timestamp': ttime.time(),
                       'year': RE.md['year'],
                       'cycle': RE.md['cycle'],
                       'proposal': RE.md['proposal'],
                       'PI': RE.md['PI'],
                       'config': copy.deepcopy(rowland_circle.config)}
        self.add_config(config_dict)

    def set_config_by_index(self, config_index):
        config_dict = self.configs[config_index]
        config = config_dict['config']
        rowland_circle.set_spectrometer_config(config)
        rowland_circle.save_current_spectrometer_config_to_settings()

    def generate_config_str(self, config_dict):
        name = config_dict['name']
        timestamp_str = datetime.strftime(datetime.fromtimestamp(config_dict['timestamp']), '%Y-%m-%d')
        config = config_dict['config']
        return f'{name} - {config["crystal"]}({"".join([str(i) for i in config["hkl"]])})-{int(config["R"])} - {timestamp_str}'

johann_spectrometer_manager = SpectrometerManager(json_file_path='/nsls2/data/iss/legacy/xf08id/settings/json/johann_spectrometer_manager')

