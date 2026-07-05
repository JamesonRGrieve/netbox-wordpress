# SPDX-License-Identifier: AGPL-3.0-or-later
"""Real-object builders for the NetBox test DB (no mocks). WordPressSite host-binds to a real
dcim.Device or virtualization.VirtualMachine; these helpers mint them cheaply."""
from utilities.testing import create_test_device
from virtualization.models import Cluster, ClusterType, VirtualMachine

from netbox_wordpress.models import WordPressSite


def create_test_vm(name):
    ctype = ClusterType.objects.create(name=f"ctype-{name}", slug=f"ctype-{name}")
    cluster = Cluster.objects.create(name=f"cluster-{name}", type=ctype)
    return VirtualMachine.objects.create(name=name, cluster=cluster)


def create_wp_site(name, device=None):
    return WordPressSite.objects.create(name=name, device=device or create_test_device(f"host-{name}"))
