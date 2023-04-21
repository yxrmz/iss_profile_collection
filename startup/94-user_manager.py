class UserManager(PersistentListInteractingWithGUI):

    def __init__(self, json_file_path = f'{ROOT_PATH_SHARED}/settings/user_management/user_manager.json'):
        super().__init__(json_file_path)

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

    def check_if_user_is_new(self, first_name, last_name):
        for user in self.users:
            if (user['first_name'] == first_name) and (user['last_name'] == last_name):
                return False
        return True


    @emit_list_update_signal_decorator
    def add_user(self, first_name, last_name, affiliation):
        if self.check_if_user_is_new(first_name, last_name):
            uid = str(uuid.uuid4())
            user_dict = {'uid': uid, 'first_name': first_name, 'last_name': last_name, 'affiliation': affiliation}
            self.users.append(user_dict)

user_manager = UserManager()


