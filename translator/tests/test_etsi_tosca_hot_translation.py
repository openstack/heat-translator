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

    def test_hot_translate_etsi_nfv_cp(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_cp.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_cp.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_cp_with_extended_vnic_type(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_cp_with_extended_vnic_type.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_cp_with_extended_vnic_type.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_check_cp_order(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_check_cp_order.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_check_cp_order.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_vl(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vl.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_vl.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_vl_with_unsupported_protocol(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vl_with_unsupported_protocol.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_vl_with_unsupported_protocol.yaml',
        ]
        expected_msgs = (
            'Unsupported layer_protocols, virtual_link_name:VL3, '
            'protocol_name:[\'ethernet\']',
            'Unsupported layer_protocols, virtual_link_name:VL4, '
            'protocol_name:[\'mpls\']',
            'Unsupported layer_protocols, virtual_link_name:VL5, '
            'protocol_name:[\'odu2\']',
            'Unsupported layer_protocols, virtual_link_name:VL6, '
            'protocol_name:[\'pseudo-wire\']'
        )
        self._test_successful_translation(tosca_file, hot_files, params={})
        for expected_msg in expected_msgs:
            self.assertIn(
                expected_msg,
                self.log_fixture.output
            )

    def test_hot_translate_etsi_nfv_non_leaf_in_vl(self):
        vl_name = 'VL1'
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_non_leaf_in_vl.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_non_leaf_in_vl.yaml',
        ]
        expected_msgs = (
            'Can not set the required properties '
            'max_kbps on HOT.'
            'virtual_link_name:%s' % vl_name,)
        self._test_successful_translation(tosca_file, hot_files, params={})
        for expected_msg in expected_msgs:
            self.assertIn(
                expected_msg,
                self.log_fixture.output
            )

    def test_hot_translate_etsi_nfv_blockstorage(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_blockstorage.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_blockstorage.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_vnf_vdu_cp_vl_blockstorage_with_scaling(
            self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vnf_vdu_cp_vl_blockstorage_with_scaling.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'vnf_vdu_cp_vl_blockstorage_with_scaling/'
            'hot_nfv_vnf_vdu_cp_vl_blockstorage_with_scaling.yaml',
            '../tests/data/hot_output/etsi_nfv/'
            'vnf_vdu_cp_vl_blockstorage_with_scaling/'
            'worker_instance.hot.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_vdu_cp_vl_with_mixed_scaling(
            self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vdu_cp_vl_with_mixed_scaling.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'vdu_cp_vl_with_mixed_scaling/'
            'hot_nfv_vdu_cp_vl_with_mixed_scaling.yaml',
            '../tests/data/hot_output/etsi_nfv/'
            'vdu_cp_vl_with_mixed_scaling/'
            'worker_instance.hot.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_vdu_cp_with_scaling_multi_aspects(
            self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vdu_cp_with_scaling_multi_aspects.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'vdu_cp_with_scaling_multi_aspects/'
            'hot_nfv_vdu_cp_with_scaling_multi_aspects.yaml',
            '../tests/data/hot_output/etsi_nfv/'
            'vdu_cp_with_scaling_multi_aspects/'
            'worker_instance1.hot.yaml',
            '../tests/data/hot_output/etsi_nfv/'
            'vdu_cp_with_scaling_multi_aspects/'
            'worker_instance2.hot.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_scaling_non_target_vdu_in_initial_delta(
            self):
        aspect_name = 'worker_instance'
        vdu_name = 'VDU1'
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_scaling_non_target_vdu_in_initial_delta.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'scaling_non_target_vdu_in_initial_delta/'
            'hot_nfv_scaling_non_target_vdu_in_initial_delta.yaml',
            '../tests/data/hot_output/etsi_nfv/'
            'scaling_non_target_vdu_in_initial_delta/'
            'worker_instance.hot.yaml',
        ]
        expected_msgs = (
            'Can not set the required properties '
            'min_size and max_size on HOT.'
            'aspect_name:%s' % aspect_name,
        )
        expected_msgs = (
            'No min_size or(and) max_size is found for '
            'aspect_name:%s, VDU:%s' % (
                aspect_name, vdu_name)
        )

        self._test_successful_translation(tosca_file, hot_files, params={})
        for expected_msg in expected_msgs:
            self.assertIn(
                expected_msg,
                self.log_fixture.output
            )

    def test_hot_translate_etsi_nfv_scaling_non_target_vdu_in_aspect_delta(
            self):
        aspect_name = 'worker_instance'
        vdu_name = None
        delta_name = None
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_scaling_non_target_vdu_in_aspect_delta.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'scaling_non_target_vdu_in_aspect_delta/'
            'hot_nfv_scaling_non_target_vdu_in_aspect_delta.yaml',
            '../tests/data/hot_output/etsi_nfv/'
            'scaling_non_target_vdu_in_aspect_delta/'
            'worker_instance.hot.yaml',
        ]
        expected_msgs = (
            'Can not create %s node '
            'because target vdu does not defined.'
            % aspect_name,
            'No ScalingAspectDelta for %s of %s, %s is '
            'found' % (vdu_name, aspect_name, delta_name)
        )
        self._test_successful_translation(tosca_file, hot_files, params={})
        for expected_msg in expected_msgs:
            self.assertIn(
                expected_msg,
                self.log_fixture.output
            )

    def test_hot_translate_etsi_nfv_scaling_non_deltas_in_aspect_delta(self):
        aspect_name = 'worker_instance'
        vdu_name = 'VDU1'
        delta_name = 'delta_2'
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_scaling_non_deltas_in_aspect_delta.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'scaling_non_deltas_in_aspect_delta/'
            'hot_nfv_scaling_non_deltas_in_aspect_delta.yaml',
            '../tests/data/hot_output/etsi_nfv/'
            'scaling_non_deltas_in_aspect_delta/'
            'worker_instance.hot.yaml',
        ]
        expected_msgs = (
            'No ScalingAspectDelta for %s of %s, %s is '
            'found' % (vdu_name, aspect_name, delta_name)
        )
        self._test_successful_translation(tosca_file, hot_files, params={})
        for expected_msg in expected_msgs:
            self.assertIn(
                expected_msg,
                self.log_fixture.output
            )

    def test_hot_translate_etsi_nfv_vdu_with_scope_nfvi(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vdu_affinity_with_scope_nfvi.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_vdu_affinity_with_scope_nfvi.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_vdu_with_unsupported_scope(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vdu_affinity_with_unsupported_scope.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_vdu_affinity_with_unsupported_scope.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})

    def test_hot_translate_etsi_nfv_vdu_with_unsupported_targets(self):
        tosca_file = '../tests/data/etsi_nfv/' \
            'tosca_nfv_vdu_affinity_with_unsupported_targets.yaml'
        hot_files = [
            '../tests/data/hot_output/etsi_nfv/'
            'hot_nfv_vdu_affinity_with_unsupported_targets.yaml',
        ]
        self._test_successful_translation(tosca_file, hot_files, params={})
