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

"""Unit tests for `apptainer` charm module."""

import subprocess

import charms.operator_libs_linux.v0.apt as apt
import pytest
from pytest_mock import MockerFixture

import apptainer


def test_apptainer_ops_error() -> None:
    """Test `apptainer.ApptainerOpsError(...)` exception."""
    message = "an apptainer operation has failed"
    try:
        raise apptainer.ApptainerOpsError(message)
    except apptainer.ApptainerOpsError as e:
        assert e.message == message


@pytest.mark.parametrize(
    "mock_is_container,expected",
    (
        pytest.param(lambda: True, ["apptainer"], id="system container"),
        pytest.param(lambda: False, ["apptainer", "apptainer-suid"], id="virtual machine"),
    ),
    indirect=True,
)
def test_install(mocker: MockerFixture, mock_is_container, expected) -> None:
    """Test `apptainer.install()` function."""
    mocker.patch.object(apt, "RepositoryMapping")
    mocker.patch.object(apt, "DebianRepository")
    mocker.patch.object(apt, "update")
    mock_add_package = mocker.patch.object(apt, "add_package")
    mock_add_package.side_effect = [None, apt.PackageError("failed to install apptainer!!")]

    # Test `apptainer.install()` succeeds without errors.
    apptainer.install()
    assert mock_add_package.call_args[0][0] == expected

    # Test `apptainer.install()` fails with the appropriate error message.
    with pytest.raises(apptainer.ApptainerOpsError) as exec_info:
        apptainer.install()

    assert exec_info.type == apptainer.ApptainerOpsError
    assert exec_info.value.args[0] == (
        f"failed to install apptainer packages `{expected}`. "
        + "reason: failed to install apptainer!!"
    )


@pytest.mark.parametrize(
    "mock_is_container,expected",
    (
        pytest.param(lambda: True, ["apptainer"], id="system container"),
        pytest.param(lambda: False, ["apptainer", "apptainer-suid"], id="virtual machine"),
    ),
    indirect=True,
)
def test_upgrade(mocker: MockerFixture, mock_is_container, expected) -> None:
    """Test `apptainer.upgrade()` function."""
    mock_deb_package = mocker.patch.object(apt.DebianPackage, "from_installed_package")

    # Test `apptainer.upgrade()` succeeds without errors.
    apptainer.upgrade()

    # Test `apptainer.upgrade()` fails with the appropriate error message.
    mock_deb_package.side_effect = [
        apt.PackageError("apptainer is not installed on the system :("),
    ]
    with pytest.raises(apptainer.ApptainerOpsError) as exec_info:
        apptainer.upgrade()

    assert exec_info.type == apptainer.ApptainerOpsError
    assert exec_info.value.args[0] == (
        f"failed to upgrade packages `{expected}` to the latest version. "
        + "reason: apptainer is not installed on the system :("
    )


@pytest.mark.parametrize(
    "mock_is_container,expected",
    (
        pytest.param(lambda: True, ["apptainer"], id="container"),
        pytest.param(lambda: False, ["apptainer", "apptainer-suid"], id="not container"),
    ),
    indirect=True,
)
def test_remove(mocker: MockerFixture, mock_is_container, expected) -> None:
    """Test `apptainer.remove()` function."""
    mock_remove_package = mocker.patch.object(apt, "remove_package")
    mock_remove_package.side_effect = [
        None,
        apt.PackageNotFoundError("no `apptainer` package found to remove :("),
    ]

    # Test `apptainer.remove()` succeeds without errors.
    apptainer.remove()
    assert mock_remove_package.call_args[0][0] == expected

    # Test `apptainer.remove()` fails with the appropriate error message.
    with pytest.raises(apptainer.ApptainerOpsError) as exec_info:
        apptainer.remove()

    assert exec_info.type == apptainer.ApptainerOpsError
    assert exec_info.value.args[0] == (
        f"failed to remove apptainer packages `{expected}`. "
        + "reason: no `apptainer` package found to remove :("
    )


def test_version(mocker: MockerFixture) -> None:
    """Test `apptainer.version()` function."""
    mock_run = mocker.patch.object(subprocess, "run")
    mock_run.side_effect = [
        subprocess.CompletedProcess([], returncode=0, stdout="apptainer version 1.3.4"),
        subprocess.CalledProcessError(returncode=5, cmd=[], stderr="unknown flag: --version"),
    ]

    # Test `apptainer.version()` when `apptainer` is found on `$PATH`.
    assert apptainer.version() == "1.3.4"

    # Test `apptainer.version()` when `apptainer` is not installed.
    with pytest.raises(apptainer.ApptainerOpsError) as exec_info:
        apptainer.version()

    assert exec_info.type == apptainer.ApptainerOpsError
    assert exec_info.value.args[0] == (
        "failed to get the version of `apptainer` installed. " + "reason: unknown flag: --version"
    )


def test_installed(mocker: MockerFixture) -> None:
    """Test `apptainer.installed()` function."""
    mock_deb_package = mocker.patch.object(apt.DebianPackage, "from_installed_package")
    mock_which = mocker.patch("shutil.which")
    mock_which.side_effect = ["/usr/bin/apptainer", None]

    # Test `apptainer.installed()` when `apptainer` package is installed and on `$PATH`.
    assert apptainer.installed() is True

    # Test `apptainer.installed()` when `apptainer` package is installed, but not on `$PATH`.
    assert apptainer.installed() is False

    mock_deb_package.side_effect = [apt.PackageNotFoundError("apptainer not found :(")]

    # Test `apptainer.installed()` when `apptainer` package is not installed.
    assert apptainer.installed() is False
