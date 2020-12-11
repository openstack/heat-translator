#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
from unittest import mock

from translator.conf.config import ConfigProvider as translatorConfig
from translator.tests.base import TestCase


def reload_config(func):
    '''Decorator to reload config.

    Set to default values defined in translator.conf file

    '''

    def reload(*args):
        func(*args)
        path = os.path.dirname(os.path.abspath(__file__)) + '/../conf/'
        conf_file = os.path.join(path, 'translator.conf')
        translatorConfig._load_config(conf_file)

    return reload


class ConfTest(TestCase):

    @reload_config
    @mock.patch('configparser.ConfigParser')
    def test_load_config(self, mock_config_parser):
        translatorConfig._translator_config.read = mock.MagicMock()
        translatorConfig._load_config('fake_file.conf')
        self.assertTrue(translatorConfig._translator_config.read.called)

    @mock.patch.object(translatorConfig._translator_config, 'get')
    def test_get_value(self, mock_translator_config):
        mock_translator_config.return_value = 'hot'
        value = translatorConfig.get_value('DEFAULT', 'language')
        self.assertTrue(translatorConfig._translator_config.get.called)
        self.assertEqual(value, 'hot')

    @mock.patch.object(translatorConfig._translator_config, 'items')
    def test_get_all_values(self, mock_translator_config):
        mock_translator_config.return_value = ['hot']
        values = translatorConfig.get_all_values()
        self.assertTrue(translatorConfig._translator_config.items.called)
        self.assertEqual(values[0], 'hot')
