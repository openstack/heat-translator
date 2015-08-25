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

''' Provide a global configuration for the TOSCA translator'''

from six.moves import configparser

from toscaparser.utils.gettextutils import _
import translator.common.exception as exception


class ConfigProvider(object):
    '''Global config proxy that wraps a ConfigParser object.

    Allows for class based access to config values. Should only be initialized
    once using the corresponding translator.conf file in the conf directory.

    '''

    # List that captures all of the conf file sections.
    # Append any new sections to this list.
    _sections = ['DEFAULT']
    _translator_config = None

    @classmethod
    def _load_config(cls, conf_file):
        '''Private method only to be called once from the __init__ module'''

        cls._translator_config = configparser.ConfigParser()
        try:
            cls._translator_config.read(conf_file)
        except configparser.ParsingError:
            msg = _('Unable to parse translator.conf file.'
                    'Check to see that it exists in the conf directory.')
            raise exception.ConfFileParseError(message=msg)

    @classmethod
    def get_value(cls, section, key):
        try:
            value = cls._translator_config.get(section, key)
        except configparser.NoOptionError:
            raise exception.ConfOptionNotDefined(key=key, section=section)
        except configparser.NoSectionError:
            raise exception.ConfSectionNotDefined(section=section)

        return value

    @classmethod
    def get_all_values(cls):
        values = []
        for section in cls._sections:
            try:
                values.extend(cls._translator_config.items(section=section))
            except configparser.NoOptionError:
                raise exception.ConfSectionNotDefined(section=section)

        return values
