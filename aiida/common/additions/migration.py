import getpass
import os

from aiida.common.setup import (AIIDA_CONFIG_FOLDER, DAEMON_SUBDIR, LOG_DIR)
from aiida.common.setup import (aiidadb_backend_key,
                                aiidadb_backend_value_django)
from aiida.common.setup import (get_config, store_config, get_profiles_list,
                                install_daemon_files)
from aiida.common.utils import query_string

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

        # Returning the configuration
        return conf

    def install_deamon_file(self):
        pass

    def main_method(self):

        # Verify the AiiDA directory
        while True:
            aiida_directory = os.path.expanduser(
                query_string("Please provide your AiiDA "
                             "directory: ", AIIDA_CONFIG_FOLDER))
            if os.path.isdir(aiida_directory):
                print("The given directory is: {}".format(aiida_directory))
                break

            print("The given directory ({}) is not valid. Please try again"
                  .format(aiida_directory))

        # Verify the daemon directory
        while True:
            daemon_dir = os.path.join(aiida_directory, DAEMON_SUBDIR)
            daemon_dir = query_string("Please provide your AiiDA "
                                           "daemon directory. Usually it is "
                                           "in the AiiDA directory: ",
                                                  daemon_dir)

            if os.path.isdir(daemon_dir):
                print("The given directory is: {}".format(daemon_dir))
                break

            print("The given directory ({}) is not valid. Please try again"
                  .format(daemon_dir))

        # Verify the log directory
        while True:
            log_dir = os.path.join(aiida_directory, LOG_DIR)
            log_dir = query_string("Please provide your AiiDA "
                                           "log directory. Usually it is "
                                           "in the AiiDA daemon directory: ",
                                                  log_dir)

            if os.path.isdir(log_dir):
                print("The given directory is: {}".format(log_dir))
                break

            print("The given directory ({}) is not valid. Please try again"
                  .format(log_dir))

        # We update the configuration if needed
        self.adding_backend()

        # We store the configuration
        store_config()

        # We update the daemon directory
        db_user = getpass.getuser()
        install_daemon_files(aiida_directory, daemon_dir, log_dir, db_user)

if __name__ == '__main__':
    Migration().main_method()