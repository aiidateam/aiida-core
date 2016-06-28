
import pip
installed_packages = [p.project_name for p in pip.get_installed_distributions()]


KOMBU_FOUND = 'kombu' in installed_packages
