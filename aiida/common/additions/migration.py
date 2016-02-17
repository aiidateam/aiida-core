from aiida.common.setup import (aiidadb_backend_key,
                                aiidadb_backend_value_django)
from aiida.common.setup import get_config, store_config, get_profiles_list
from aiida.common.utils import query_string

import os

class Migration(object):

    # Profile key
    _profiles_key = "profiles"

    def adding_backend(self):
        conf = get_config()
        get_profiles_list()
        print("Configuration {}".format(conf))
        print(type(conf).__name__)
        print("{}".format(conf.keys()))

        # Identifying all the available profiles
        if self._profiles_key in conf.keys():
            profiles = get_profiles_list()
            print("{}".format(profiles))
            p_keys = profiles.keys()
            print("p_keys: {}".format(p_keys))
            # For every profile
            for p_key in p_keys:
                print("{}".format(p_key))
                # get the
                curr_profile = profiles[p_key]

                print("{}".format(curr_profile))
                # Check if there is a specific backend in the profile
                # and if not, add Django as backend
                if aiidadb_backend_key not in curr_profile.keys():
                    curr_profile[aiidadb_backend_key] = \
                        aiidadb_backend_value_django

        # Saving the profile back to the right place
        store_config(conf)

    def install_deamon_file(self):
        pass

    def main_method(self):

        while True:
            aiida_directory = query_string("Please provide your AiiDA "
                                           "directory: ", None)
            if os.path.isdir(aiida_directory):
                break
            print("The given directory ({}) is not valid. Please try again"
                  .format(aiida_directory))

        while True:
            default_daemon_dir = os.path.join(aiida_directory, "daemon")
            aiida_daemon_directory = query_string("Please provide your AiiDA "
                                           "daemon directory. Usually it is "
                                           "in the AiiDA directory: ",
                                                  default_daemon_dir)

            if os.path.isdir(aiida_daemon_directory):
                break
            print("The given directory ({}) is not valid. Please try again"
                  .format(aiida_daemon_directory))


if __name__ == '__main__':
    Migration().main_method()