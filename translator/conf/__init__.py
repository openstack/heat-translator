#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

''' Initialize the global configuration for the translator '''

import os

from translator.conf.config import ConfigProvider

CONF_FILENAME = 'translator.conf'


def init_global_conf():
    '''Initialize the configuration provider.

    Allows the configuration to be shared throughout the translator code.
    The file used is translator.conf, and is within the conf/ directory. It
    is a standard ini format, and is prcessed using the ConfigParser module.

    '''
    conf_path = os.path.dirname(os.path.abspath(__file__))
    conf_file = os.path.join(conf_path, CONF_FILENAME)
    ConfigProvider._load_config(conf_file)


init_global_conf()
