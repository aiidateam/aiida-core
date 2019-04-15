# -*- coding: utf-8 -*-

import pip

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

installed_packages = [p.project_name for p in pip.get_installed_distributions()]


KOMBU_FOUND = 'kombu' in installed_packages
