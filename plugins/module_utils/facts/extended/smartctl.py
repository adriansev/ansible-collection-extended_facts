# Collect facts related to smartctl
#
# This file is part of Ansible Extended Facts
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
from ansible.module_utils.facts.collector import BaseFactCollector

class SmartctlFactCollector(BaseFactCollector):
    name = 'smartctl'
    _fact_ids = set()

    def collect(self, module = None, collected_facts = None):
        facts_dict = {}

        lspci_bin = module.get_bin_path('lspci')
        if lspci_bin:
            rc, lspci_out, err = module.run_command([lspci_bin])

        # parse /sys/class/scsi_generic to get sgX RAID Controller
        # /sys/class/scsi_generic/sg2/device/inquiry

        # Identify controler type from lspci to establish how we parse the drives

        # Identify block devices that are volumes of RAID to remove them from smartctl list to be checked

        smartctl_bin = module.get_bin_path('smartctl')
        if not smartctl_bin: return facts_dict

        rc, smartctl_output, err = module.run_command([smartctl_bin, '--scan-open'])
        smartctl_output_dev_list = []
        for dev_line in smartctl_output.splitlines():
            dev, __sep, __comment = dev_line.partition(' # ')
            get_smart_cmd = [smartctl_bin, '--json', '-x']
            get_smart_cmd.extend(dev.split())
            rc, smartctl_disk_json_str, err = module.run_command(get_smart_cmd)
            smartctl_dict = json.loads(str(smartctl_disk_json_str))
            smartctl_output_dev_list.append(smartctl_dict)

        if smartctl_output_dev_list:
            facts_dict['smartctl'] = smartctl_output_dev_list

        return facts_dict
