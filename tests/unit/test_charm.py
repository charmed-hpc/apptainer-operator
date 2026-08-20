# Copyright 2025-2026 Canonical Ltd.
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

import ops
import pytest
from charmed_hpc_libs.errors import AptError
from charmed_hpc_libs.ops import AptOpsManager
from ops import testing
from pytest_mock import MockerFixture

from apptainer import ApptainerManager
from constants import OCI_RUNTIME_INTEGRATION_NAME


@pytest.mark.parametrize(
    "mock_install,expected",
    (
        pytest.param(None, ops.ActiveStatus(), id="success"),
        pytest.param(
            AptError("install failed"),
            ops.BlockedStatus("Failed to install Apptainer. See `juju debug-log` for details"),
            id="fail",
        ),
    ),
)
def test_on_install(mock_charm, mocker: MockerFixture, mock_install, expected) -> None:
    """Test the `_on_install` event handler."""
    mocker.patch.object(AptOpsManager, "install", side_effect=mock_install)
    mocker.patch.object(AptOpsManager, "is_installed", return_value=True)
    mocker.patch.object(AptOpsManager, "version", return_value="1.3.4")
    # Mock AppArmor side effects introduced by `ApptainerManager.install`.
    mocker.patch("apptainer._APPARMOR_PROFILE_PATH")
    mocker.patch("apptainer.systemctl")

    state = mock_charm.run(mock_charm.on.install(), testing.State())

    assert state.unit_status == expected
    if isinstance(expected, ops.BlockedStatus):
        assert len(state.deferred) == 1
    else:
        assert len(state.deferred) == 0


@pytest.mark.parametrize(
    "mock_remove,expected",
    (
        pytest.param(None, ops.BlockedStatus("Apptainer is not installed"), id="success"),
        pytest.param(
            AptError("remove failed"),
            ops.BlockedStatus("Failed to remove Apptainer. See `juju debug-log` for details"),
            id="fail",
        ),
    ),
)
def test_on_stop(mock_charm, mocker: MockerFixture, mock_remove, expected) -> None:
    """Test the `_on_stop` event handler."""
    mocker.patch.object(AptOpsManager, "remove", side_effect=mock_remove)
    mocker.patch.object(AptOpsManager, "is_installed", return_value=False)
    # Mock AppArmor side effects introduced by `ApptainerManager.remove`.
    mocker.patch("apptainer._APPARMOR_PROFILE_PATH")
    mocker.patch("apptainer.systemctl")

    state = mock_charm.run(mock_charm.on.stop(), testing.State())

    assert state.unit_status == expected


@pytest.mark.parametrize(
    "leader,executable_path,expected_status,expected_app_data,expected_deferred",
    (
        pytest.param(
            True,
            "/usr/bin/apptainer",
            ops.ActiveStatus(),
            {"type": '"apptainer"', "executable_path": '"/usr/bin/apptainer"'},
            0,
            id="leader_success",
        ),
        pytest.param(
            False,
            "/usr/bin/apptainer",
            ops.UnknownStatus(),
            {},
            0,
            id="non_leader",
        ),
        pytest.param(
            True,
            FileNotFoundError("apptainer executable not found on PATH"),
            ops.BlockedStatus(
                "Failed to provide OCI runtime data. See `juju debug-log` for details"
            ),
            {},
            1,
            id="leader_executable_not_found",
        ),
    ),
)
def test_on_slurmctld_connected(
    mock_charm,
    mocker: MockerFixture,
    leader,
    executable_path,
    expected_status,
    expected_app_data,
    expected_deferred,
) -> None:
    """Test the `_on_slurmctld_connected` event handler."""
    if isinstance(executable_path, FileNotFoundError):
        mocker.patch.object(
            ApptainerManager,
            "executable_path",
            new_callable=mocker.PropertyMock,
            side_effect=executable_path,
        )
    else:
        mocker.patch.object(
            ApptainerManager, "executable_path", new_callable=lambda: executable_path
        )
    mocker.patch.object(AptOpsManager, "is_installed", return_value=True)

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
    assert integration.local_app_data == expected_app_data
    assert state.unit_status == expected_status
    assert len(state.deferred) == expected_deferred
