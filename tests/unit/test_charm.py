# Copyright 2025 Canonical Ltd.
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

"""Unit tests for the `apptainer` charm."""

from collections import defaultdict

import ops
import pytest
from hpc_libs.interfaces import SlurmctldConnectedEvent
from ops import testing
from slurmutils import OCIConfig

import apptainer
from constants import OCI_RUNTIME_INTEGRATION_NAME


@pytest.mark.parametrize(
    "mock_install,expected",
    (
        pytest.param(lambda: None, ops.ActiveStatus(), id="success"),
        pytest.param(
            lambda: (_ for _ in ()).throw(apptainer.ApptainerOpsError("install failed")),
            ops.BlockedStatus("Failed to install Apptainer. See `juju debug-log` for details."),
            id="fail",
        ),
    ),
)
def test_on_install(monkeypatch, mock_charm, mock_install, expected) -> None:
    """Test the `_on_install` event handler."""
    monkeypatch.setattr(apptainer, "install", mock_install)
    monkeypatch.setattr(apptainer, "installed", lambda: True)
    monkeypatch.setattr(apptainer, "version", lambda: "1.3.4")

    state = mock_charm.run(mock_charm.on.install(), testing.State())

    assert state.unit_status == expected
    if isinstance(expected, ops.BlockedStatus):
        assert len(state.deferred) == 1
    else:
        assert len(state.deferred) == 0


@pytest.mark.parametrize(
    "mock_remove,expected",
    (
        pytest.param(lambda: None, ops.BlockedStatus("Apptainer is not installed"), id="success"),
        pytest.param(
            lambda: (_ for _ in ()).throw(apptainer.ApptainerOpsError("install failed")),
            ops.BlockedStatus("Failed to remove Apptainer. See `juju debug-log` for details."),
            id="fail",
        ),
    ),
)
def test_on_stop(monkeypatch, mock_charm, mock_remove, expected) -> None:
    """Test the `_on_stop` event handler."""
    monkeypatch.setattr(apptainer, "remove", mock_remove)
    monkeypatch.setattr(apptainer, "installed", lambda: False)

    state = mock_charm.run(mock_charm.on.stop(), testing.State())

    assert state.unit_status == expected


@pytest.mark.parametrize(
    "leader", (pytest.param(True, id="unit_leader"), pytest.param(False, id="not_unit_leader"))
)
def test_on_slurmctld_connected(mock_charm, mock_ociconfig, leader) -> None:
    """Test the `_on_slurmctld_connected` event handler."""
    oci_runtime_integration_id = 25
    oci_runtime_integration = testing.Relation(
        endpoint=OCI_RUNTIME_INTEGRATION_NAME,
        interface="slurm-oci-runtime",
        id=oci_runtime_integration_id,
        remote_app_name="slurmctld",
    )

    state = mock_charm.run(
        mock_charm.on.relation_created(oci_runtime_integration),
        testing.State(relations={oci_runtime_integration}, leader=leader),
    )

    integration = state.get_relation(oci_runtime_integration_id)
    if leader:
        # Verify that the leader unit has set `oci.conf` data after `slurmctld` is connected.
        assert "ociconfig" in integration.local_app_data
        config = OCIConfig.from_json(integration.local_app_data["ociconfig"])
        assert config.dict() == mock_ociconfig.dict()
    else:
        # Verify that non-leader has not set any `oci.conf` configuration data.
        assert integration.local_app_data == {}

    # Assert that `SlurmctldConnectedEvent` was emitted on all units.
    assert isinstance(mock_charm.emitted_events[-1], SlurmctldConnectedEvent)

    # Assert that `SlurmctldConnectedEvent` was only emitted once.
    occurred = defaultdict(lambda: 0)
    for event in mock_charm.emitted_events:
        occurred[type(event)] += 1

    assert occurred[SlurmctldConnectedEvent] == 1


@pytest.mark.parametrize(
    "mock_upgrade,mock_version,expected_status,expected_version",
    (
        pytest.param(lambda: None, lambda: "1.4.0", ops.ActiveStatus(), "1.4.0", id="success"),
        pytest.param(
            lambda: (_ for _ in ()).throw(apptainer.ApptainerOpsError("upgrade failed")),
            lambda: "",
            ops.BlockedStatus("Failed to upgrade Apptainer. See `juju debug-log` for details."),
            "",
            id="fail",
        ),
    ),
)
def test_on_upgrade(
    monkeypatch,
    mock_charm,
    mock_upgrade,
    mock_version,
    expected_status,
    expected_version,
) -> None:
    """Test the `_on_upgrade` action event handler."""
    monkeypatch.setattr(apptainer, "upgrade", mock_upgrade)
    monkeypatch.setattr(apptainer, "version", mock_version)
    monkeypatch.setattr(apptainer, "installed", lambda: True)

    state = mock_charm.run(mock_charm.on.action("upgrade"), testing.State())

    assert state.unit_status == expected_status
    assert state.workload_version == expected_version
