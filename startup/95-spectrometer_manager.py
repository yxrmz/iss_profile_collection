

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
        print_to_gui(f'Setting the spectrometer config to {self.generate_config_str(config_dict)}', add_timestamp=True, tag='Spectrometer')
        config = copy.deepcopy(config_dict['config'])
        rowland_circle.set_spectrometer_config(config)
        rowland_circle.save_current_spectrometer_config_to_settings()
        johann_emission._match_energy_limits_to_rowland_circle()

    def set_config_by_uid(self, config_uid):
        for index, config_dict in enumerate(self.configs):
            if config_dict['uid'] == config_uid:
                if config_dict['config'] != rowland_circle.config:
                    self.set_config_by_index(index)
                else:
                    print_to_gui(f'Spectrometer config {self.generate_config_str(config_dict)} is currently active',
                                 add_timestamp=True, tag='Spectrometer')
                return

        # # config_dict = self.configs[config_index]
        # config = config_dict['config']
        # rowland_circle.set_spectrometer_config(config)
        # rowland_circle.save_current_spectrometer_config_to_settings()
        # johann_emission._match_energy_limits_to_rowland_circle()

    def generate_config_str(self, config_dict):
        name = config_dict['name']
        timestamp_str = datetime.strftime(datetime.fromtimestamp(config_dict['timestamp']), '%Y-%m-%d')
        config = config_dict['config']
        return f'{name} - {config["crystal"]}({"".join([str(i) for i in config["hkl"]])})-{int(config["R"])} - {config_dict["PI"]} - {timestamp_str}'

johann_spectrometer_manager = SpectrometerManager(json_file_path='/nsls2/data/iss/legacy/xf08id/settings/json/johann_spectrometer_manager')

