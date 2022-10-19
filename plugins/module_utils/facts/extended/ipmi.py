# Collect facts related to IPMI
#
# This file is part of Ansible Extended Facts
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

from ansible.module_utils.facts.collector import BaseFactCollector
from ansible.module_utils.facts.utils import get_file_lines

class IpmiFactCollector(BaseFactCollector):
    name = 'ipmi'
    _fact_ids = set()

    def collect(self, module = None, collected_facts = None):
        facts_dict = {}
        ipmi_dict = {}
        ipmi_present = False # This is default

        # Find loaded kernel modules for IPMI Adapter
        if os.path.exists('/proc/modules'):
            for line in get_file_lines('/proc/modules'):
                # If have module ipmi_si or ipmi_ssif return true
                if re.search('^ipmi_si\s+|^ipmi_ssif\s+', line): ipmi_present = True

        facts_dict['ipmi'] = ipmi_present

        ipmitool_bin = module.get_bin_path('ipmitool')
        facts_dict['ipmitool'] = bool(ipmitool_bin)

        def convert_lines2dict(input_str: str) -> dict:
            if not input_str: return {}
            ret_dict = {}
            for l in input_str.splitlines():
                name, __, value = l.partition(' : ')
                if name.strip(): ret_dict[name.strip()] = value.strip()
            return ret_dict

        if ipmi_present and ipmitool_bin:
            rc, ipmi_lan_out, err = module.run_command([ipmitool_bin, 'lan', 'print'])
            ipmi_lan_dict = convert_lines2dict(ipmi_lan_out) if ipmi_lan_out else {}
            if ipmi_lan_dict: ipmi_dict['lan'] = ipmi_lan_dict

            rc, ipmi_fru_out, err = module.run_command([ipmitool_bin, 'fru'])
            ipmi_fru_dict = convert_lines2dict(ipmi_fru_out) if ipmi_fru_out else {}
            if ipmi_fru_dict: ipmi_dict['fru'] = ipmi_fru_dict

        if ipmi_dict: facts_dict['ipmi_info'] = ipmi_dict
        return facts_dict
