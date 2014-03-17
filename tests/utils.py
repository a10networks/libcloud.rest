# -*- coding:utf-8 -*-
import copy

from libcloud_rest.api.providers import get_driver_instance

from tests.compute.drivers_patches import PATCHES as COMPUTE_PATCHES
from tests.dns.drivers_patches import PATCHES as DNS_PATCHES
from tests.loadbalancer.drivers_patches import PATCHES as LB_PATCHES
from tests.storage.drivers_patches import PATCHES as STORAGE_PATCHES


def get_test_driver_instance(Driver, data):
    if Driver.__name__ not in DRIVERS_PATCHES:
        raise NotImplementedError('Unknown driver %s' % (Driver.__name__))
    Driver_copy = copy.deepcopy(Driver)
    driver_patch = DRIVERS_PATCHES[Driver_copy.__name__]
    driver_patch.pre_process(Driver_copy)
    driver_instance = get_driver_instance(Driver_copy, data)
    driver_patch.post_process(driver_instance)
    return driver_instance


DRIVERS_PATCHES = COMPUTE_PATCHES
DRIVERS_PATCHES.update(DNS_PATCHES)
DRIVERS_PATCHES.update(LB_PATCHES)
DRIVERS_PATCHES.update(STORAGE_PATCHES)
