#!/usr/bin/env python3
# Copyright 2025-2026 Vantage Compute Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Charmed operator for Apptainer, a container runtime for HPC clusters."""

import logging

import ops
from charmed_hpc_libs.errors import AptError
from charmed_hpc_libs.ops import StopCharm, leader, refresh
from charmed_slurm_oci_runtime_interface import OCIRuntimeData, OCIRuntimeProvider
from charmed_slurm_slurmctld_interface import SlurmctldConnectedEvent

from apptainer import ApptainerManager
from constants import OCI_RUNTIME_INTEGRATION_NAME


def _apptainer_status_check(charm: "ApptainerCharm") -> ops.StatusBase:
    """Check the state of the unit after a charm method has completed."""
    if not charm.apptainer.is_installed():
        return ops.BlockedStatus("Apptainer is not installed")

    return ops.ActiveStatus()


logger = logging.getLogger(__name__)
refresh = refresh(hook=_apptainer_status_check)


class ApptainerCharm(ops.CharmBase):
    """Charmed operator for Apptainer, a container runtime for HPC clusters."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)

        self.apptainer = ApptainerManager()
        framework.observe(self.on.install, self._on_install)
        framework.observe(self.on.stop, self._on_stop)

        self._oci_runtime = OCIRuntimeProvider(self, OCI_RUNTIME_INTEGRATION_NAME)
        framework.observe(self._oci_runtime.on.slurmctld_connected, self._on_slurmctld_connected)

    @refresh
    def _on_install(self, event: ops.InstallEvent) -> None:
        """Handle when unit is installed onto a machine."""
        self.unit.status = ops.MaintenanceStatus("Installing Apptainer")
        try:
            self.apptainer.install()
            self.unit.set_workload_version(self.apptainer.version())
        except AptError as e:
            logger.error(e.message)
            event.defer()
            raise StopCharm(
                ops.BlockedStatus("Failed to install Apptainer. See `juju debug-log` for details")
            )

        self.unit.status = ops.ActiveStatus()

    @refresh
    def _on_stop(self, _: ops.RemoveEvent) -> None:
        """Handle when Juju starts teardown process of unit."""
        try:
            self.unit.status = ops.MaintenanceStatus("Removing Apptainer")
            self.apptainer.remove()
            self.unit.status = ops.MaintenanceStatus("Apptainer removed")
        except AptError as e:
            logger.error(e.message)
            raise StopCharm(
                ops.BlockedStatus("Failed to remove Apptainer. See `juju debug-log` for details")
            )

    @leader
    @refresh
    def _on_slurmctld_connected(self, event: SlurmctldConnectedEvent) -> None:
        """Handle when the Slurm controller `slurmctld` is connected to application."""
        try:
            self._oci_runtime.set_oci_runtime_data(
                OCIRuntimeData(
                    type="apptainer",
                    executable_path=str(self.apptainer.executable_path),
                ),
                integration_id=event.relation.id,
            )
        except FileNotFoundError as e:
            logger.exception(e)
            event.defer()
            raise StopCharm(
                ops.BlockedStatus(
                    "Failed to provide OCI runtime data. See `juju debug-log` for details"
                )
            )


if __name__ == "__main__":  # pragma: nocover
    ops.main(ApptainerCharm)
