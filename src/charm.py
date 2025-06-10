#!/usr/bin/env python3
# Copyright 2025 Vantage Compute Corporation
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
from hpc_libs.interfaces import OCIRuntimeData, OCIRuntimeProvider, SlurmctldConnectedEvent
from hpc_libs.utils import StopCharm, leader, refresh
from slurmutils import OCIConfig

import apptainer
from constants import OCI_RUNTIME_INTEGRATION_NAME


def _apptainer_status_check(_: ops.CharmBase) -> ops.StatusBase:
    """Check the state of the unit after a charm method has completed."""
    if not apptainer.installed():
        return ops.BlockedStatus("Apptainer is not installed")

    return ops.ActiveStatus()


logger = logging.getLogger(__name__)
refresh = refresh(check=_apptainer_status_check)


class ApptainerCharm(ops.CharmBase):
    """Charmed operator for Apptainer, a container runtime for HPC clusters."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        framework.observe(self.on.install, self._on_install)
        framework.observe(self.on.stop, self._on_stop)
        framework.observe(self.on.upgrade_action, self._on_upgrade)

        self._oci_runtime = OCIRuntimeProvider(self, OCI_RUNTIME_INTEGRATION_NAME)
        framework.observe(self._oci_runtime.on.slurmctld_connected, self._on_slurmctld_connected)

    @refresh
    def _on_install(self, event: ops.InstallEvent) -> None:
        """Handle when unit is installed onto a machine."""
        self.unit.status = ops.MaintenanceStatus("Installing Apptainer")
        try:
            apptainer.install()
            self.unit.set_workload_version(apptainer.version())
        except apptainer.ApptainerOpsError as e:
            logger.error(e)
            event.defer()
            raise StopCharm(
                ops.BlockedStatus("Failed to install Apptainer. See `juju debug-log` for details.")
            )

        self.unit.status = ops.ActiveStatus()

    @refresh
    def _on_stop(self, _: ops.RemoveEvent) -> None:
        """Handle when Juju starts teardown process of unit."""
        try:
            self.unit.status = ops.MaintenanceStatus("Removing Apptainer")
            apptainer.remove()
            self.unit.status = ops.MaintenanceStatus("Apptainer removed")
        except apptainer.ApptainerOpsError as e:
            logger.error(e.message)
            raise StopCharm(
                ops.BlockedStatus("Failed to remove Apptainer. See `juju debug-log` for details.")
            )

    @leader
    def _on_slurmctld_connected(self, event: SlurmctldConnectedEvent) -> None:
        """Handle when the Slurm controller `slurmctld` is connected to application."""
        config = OCIConfig()
        config.ignore_file_config_json = True
        config.env_exclude = "^(SLURM_CONF|SLURM_CONF_SERVER)="
        config.run_time_env_exclude = "^(SLURM_CONF|SLURM_CONF_SERVER)="
        config.run_time_run = "apptainer exec --userns %r %@"
        config.run_time_kill = "kill -s SIGTERM %p"
        config.run_time_delete = "kill -s SIGKILL %p"

        self._oci_runtime.set_oci_runtime_data(
            OCIRuntimeData(ociconfig=config), integration_id=event.relation.id
        )

    @refresh
    def _on_upgrade(self, _: ops.ActionEvent) -> None:
        """Perform upgrade to latest operations."""
        try:
            apptainer.upgrade()
            self.unit.set_workload_version(apptainer.version())
        except apptainer.ApptainerOpsError as e:
            logger.error(e.message)
            raise StopCharm(
                ops.BlockedStatus("Failed to upgrade Apptainer. See `juju debug-log` for details.")
            )


if __name__ == "__main__":  # pragma: nocover
    ops.main(ApptainerCharm)
