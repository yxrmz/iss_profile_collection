
print(ttime.ctime() + ' >>>> ' + __file__)

class UserManager(PersistentListInteractingWithGUI):

    def __init__(self, json_file_path = f'{ROOT_PATH_SHARED}/settings/user_management/user_manager.json'):
        super().__init__(json_file_path)
        try:
            _, current_user = self.current_user()
            self._init_managers(current_user['sample_manager'], current_user['scan_manager'])
        except:
            pass


    # Class specific decorators
    @property
    def users(self):
        return self.items

    # @users.setter
    # def users(self, value):
    #     self.items = value
    #
    # @users.deleter
    # def users(self):
    #     del self.items

    def find_user_index(self, first_name, last_name):
        for i, user in enumerate(self.users):
            if (user['first_name'] == first_name) and (user['last_name'] == last_name):
                return i
        return -1


    @emit_list_update_signal_decorator
    def set_user(self, first_name, last_name, affiliation, email):
        index = self.find_user_index(first_name, last_name)
        if index == -1:
            uid = str(uuid.uuid4())
            sample_manager_filename = f'sample_manager_{str(uuid.uuid4())[0:7]}.json'
            scan_manager_filename = f'scan_manager_{str(uuid.uuid4())[0:7]}.json'
            user_dict =     {'uid': uid,
                            'first_name': first_name,
                            'last_name': last_name,
                            'affiliation': affiliation,
                            'email':email,
                            'sample_manager': sample_manager_filename,
                            'scan_manager': scan_manager_filename,
                            }

            self.users.append(user_dict)
        else:
            sample_manager_filename = self.users[index]['sample_manager']
            scan_manager_filename = self.users[index]['scan_manager']

        self._init_managers(sample_manager_filename, scan_manager_filename)

    def _init_managers(self, sample_manager_filename, scan_manager_filename):
        sample_manager.init_from_new_file(f'{ROOT_PATH_SHARED}/settings/user_management/{sample_manager_filename}')
        scan_manager.load_local_manager(f'{ROOT_PATH_SHARED}/settings/user_management/{scan_manager_filename}')

    def current_user(self):
        current_user_name = RE.md['PI'].split(' ')
        for indx, user in enumerate(self.users):
            if (user['first_name'] == current_user_name[0]) and (user['last_name'] == current_user_name[1]):
                return indx, user

    def add_run(self, proposal, saf, experimenters):
        _current_index, _current_user  = self.current_user()
        run={}
        run['start'] = ttime.ctime()
        run['timestamp'] = ttime.time()
        run['proposal'] = proposal
        run['saf'] = saf
        run['experimenters'] = experimenters
        if 'runs' in _current_user.keys():
            self.users[_current_index]['runs'].append(run)
        else:
            self.users[_current_index]['runs']=[run]


user_manager = UserManager()


user_manager.set_user('Eli', 'Stavitski', 'NSLS II','istavitski.bnl.gov')






