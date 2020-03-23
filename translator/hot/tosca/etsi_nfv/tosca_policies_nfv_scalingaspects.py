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

import logging

from translator.hot.syntax.hot_resource import HotResource
from translator.hot.tosca.etsi_nfv.scalingaspect.\
    tosca_policies_nfv_scalingaspect import ToscaNfvScalingAspect
log = logging.getLogger('heat-translator')

# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaNfvScalingAspects'


class ToscaNfvScalingAspects(HotResource):
    """Translate TOSCA policy type tosca.policies.nfv.ScalingAspects."""

    toscatype = 'tosca.policies.nfv.ScalingAspects'

    def __init__(self, policy, csar_dir=None, hot_template_parameters=None,
                 nested_template=None,
                 extra_flg=None):
        hot_type = "OS::Heat::ScalingPolicy"

        if extra_flg is None:
            # Multi aspects support
            self.aspect_names = policy.properties['aspects'].keys()
            self.scaling_aspect_objs = []
            for aspect_name in self.aspect_names:
                self.scaling_aspect_objs.append(
                    ToscaNfvScalingAspect(policy,
                                          aspect_name,
                                          csar_dir,
                                          hot_template_parameters)
                )

        super(ToscaNfvScalingAspects, self).__init__(
            policy,
            type=hot_type,
            csar_dir=csar_dir)

        self.policy = policy
        self.hot_template_parameters = hot_template_parameters
        self.multi_nested_templates = {}
        self.nested_template = \
            {} if nested_template is None else nested_template

    def handle_properties(self, resources):
        for aspect_obj in self.scaling_aspect_objs:
            resources, nstd_tmpt = aspect_obj.handle_properties(resources)
            self.multi_nested_templates[aspect_obj.aspect_name] = nstd_tmpt

        resources = self._create_scale_out_in_resources(resources)
        return resources

    def extract_substack_templates(self, base_filename, hot_template_version):
        return self.nested_template

    def _create_scale_out_in_resources(self, resources):
        for asp_obj in self.scaling_aspect_objs:
            asp_name = asp_obj.aspect_name

            # Create scale_out and scale_in resources
            scl_out_rsrc = ToscaNfvScalingAspects(
                self.policy,
                csar_dir=self.csar_dir,
                hot_template_parameters=self.
                hot_template_parameters,
                nested_template=self.
                multi_nested_templates[asp_name],
                extra_flg=True
            )
            scl_in_rsrc = ToscaNfvScalingAspects(
                self.policy,
                csar_dir=self.csar_dir,
                hot_template_parameters=self.
                hot_template_parameters,
                nested_template=self.
                multi_nested_templates[asp_name],
                extra_flg=True
            )
            scl_out_rsrc.name = asp_name + '_scale_out'
            scl_in_rsrc.name = asp_name + '_scale_in'

            if asp_obj.scaling_adjustment is not None:
                scaling_adjustment = \
                    int(asp_obj.scaling_adjustment)
                scl_out_rsrc.properties['scaling_adjustment'] = \
                    scaling_adjustment
                scl_in_rsrc.properties['scaling_adjustment'] = \
                    -1 * scaling_adjustment
            else:
                log.warning('No ScalingAspectDelta for %s of %s, %s is found'
                            % (asp_obj.vdu_name, asp_name, asp_obj.delta_name))

            scl_out_rsrc.properties["auto_scaling_group_id"] = {
                'get_resource': asp_name
            }
            scl_out_rsrc.properties["adjustment_type"] = \
                "change_in_capacity"
            resources.append(scl_out_rsrc)

            scl_in_rsrc.properties["auto_scaling_group_id"] = {
                'get_resource': asp_name
            }
            scl_in_rsrc.properties["adjustment_type"] = \
                "change_in_capacity"
            resources.append(scl_in_rsrc)

        # This resource has already created scale_out and
        # scale_in resources, so remove it.
        resources.remove(self)

        return resources
