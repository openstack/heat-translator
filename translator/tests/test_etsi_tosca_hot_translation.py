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

import json
import os

from toscaparser.common.exception import ExceptionCollector
from toscaparser.utils.gettextutils import _
from translator.common.utils import TranslationUtils
from translator.tests.base import TestCase


class EtsiToscaHotTranslationTest(TestCase):

    def _test_successful_translation(self, tosca_file, hot_files, params=None):
        if not params:
            params = {}
        if not isinstance(hot_files, list):
            hot_files = [hot_files]
        diff = TranslationUtils.compare_tosca_translation_with_hot(tosca_file,
                                                                   hot_files,
                                                                   params)
        self.assertEqual({}, diff, '<difference> : ' +
                         json.dumps(diff, indent=4, separators=(', ', ': ')))

    def _test_failed_translation(self, tosca_file, hot_file, params, msg,
                                 msg_path, error_raise, error_collect):
        if msg_path:
            path = os.path.normpath(os.path.join(
                os.path.dirname(os.path.realpath(__file__)), tosca_file))
            msg = msg % path
        self.assertRaises(
            error_raise,
            TranslationUtils.compare_tosca_translation_with_hot,
            tosca_file, hot_file, params)
        ExceptionCollector.assertExceptionMessage(error_collect, msg)

    def test_hot_translate_etsi_nfv_vnf(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vnf.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_vnf.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_vdu(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vdu.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_vdu.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_vdu_with_compute_requirements(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vdu_with_compute_requirements.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_vdu_with_compute_requirements.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_vdu_with_invalid_compute_requirements(
            self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vdu_with_invalid_compute_requirements.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_vdu_with_invalid_compute_requirements.yaml',
        ]
        expected_msg = _('Unsupported format of '
                         'compute_requirements, '
                         'vdu_name:VDU1, nova_extra_specs:dummy: ][')
        self._test_successful_translation(tosca_file, hot_files, params={})
        self.assertIn(
            expected_msg,
            self.log_fixture.output
        )

    def test_hot_translate_etsi_nfv_vdu_with_logical_node(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vdu_with_logical_node.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_vdu_with_logical_node.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_vdu_with_unsupported_storage(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vdu_with_unsupported_storage.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_vdu_with_unsupported_storage.yaml',
        ]
        expected_msg = _('Unsupported virtual_storage, '
                         'vdu_name:VDU1, '
                         'virtual_storage_name:UnsupportedStorage')
        self._test_successful_translation(tosca_file, hot_files, params={})
        self.assertIn(
            expected_msg,
            self.log_fixture.output
        )
