#!/usr/bin/env python3
# Copyright 2024 Omnivector, LLC.
# See LICENSE file for licensing details.

"""ApptainerOperatorCharm."""
from apptainer import Apptainer
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus


class ApptainerOperatorCharm(CharmBase):
    """Apptainer Operator lifecycle events."""

    def __init__(self, *args, **kwargs):
        """Init _stored attributes and interfaces, observe events."""
        super().__init__(*args, **kwargs)

        event_handler_bindings = {
            self.on.install: self._on_install,
            self.on.remove: self._on_uninstall,
            self.on.upgrade_action: self._on_upgrade_apptainer,
        }
        for event, handler in event_handler_bindings.items():
            self.framework.observe(event, handler)

    def _set_workload_version(self, apptainer: Apptainer) -> None:
        """Set the charmed workload version."""
        apptainer_version = Apptainer().version()
        self.unit.set_workload_version(apptainer_version)

    def _on_install(self, event) -> None:
        """Perform installation operations for apptainer."""
        apptainer = Apptainer()
        try:
            self.unit.status = WaitingStatus("Installing apptainer")
            apptainer.install()
            self.unit.status = ActiveStatus("Apptainer installed")
            self.unit.status = ActiveStatus("")
        except Exception:
            self.unit.status = BlockedStatus("Trouble installing apptainer, please debug.")
            event.defer()
            return
        # Set the workload version
        self._set_workload_version(apptainer)

    def _on_uninstall(self, event) -> None:
        """Perform uninstallation operations for apptainer."""
        apptainer = Apptainer()
        try:
            self.unit.status = WaitingStatus("Uninstalling apptainer")
            apptainer.uninstall()
        except Exception:
            self.unit.status = BlockedStatus("Trouble uninstalling apptainer, please debug.")
            event.defer()
            return

    def _on_upgrade_apptainer(self, event) -> None:
        """Perform upgrade to latest operations."""
        apptainer = Apptainer()
        apptainer.upgrade_to_latest()
        # Set the workload version
        self._set_workload_version(apptainer)


if __name__ == "__main__":  # pragma: nocover
    main(ApptainerOperatorCharm)
