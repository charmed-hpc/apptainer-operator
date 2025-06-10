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

"""Configure unit tests for the `apptainer` charm."""

from importlib import reload
from typing import Any

import pytest
from ops import testing
from pytest_mock import MockerFixture
from slurmutils import OCIConfig

import apptainer
import constants
from charm import ApptainerCharm


@pytest.fixture(scope="function")
def mock_charm() -> testing.Context[ApptainerCharm]:
    """Mock `ApptainerCharm`."""
    return testing.Context(ApptainerCharm)


@pytest.fixture(scope="session")
def mock_ociconfig() -> OCIConfig:
    """Mock `oci.conf` configuration data."""
    config = OCIConfig()
    config.ignore_file_config_json = True
    config.env_exclude = "^(SLURM_CONF|SLURM_CONF_SERVER)="
    config.run_time_env_exclude = "^(SLURM_CONF|SLURM_CONF_SERVER)="
    config.run_time_run = "apptainer exec --userns %r %@"
    config.run_time_kill = "kill -s SIGTERM %p"
    config.run_time_delete = "kill -s SIGKILL %p"

    return config


@pytest.fixture(scope="function")
def mock_is_container(request, mocker: MockerFixture) -> None:
    mocker.patch("hpc_libs.is_container.is_container", request.param)

    # The `apptainer` and `constants` modules must be reloaded because the value of
    # `APPTAINER_PACKAGES` constant is calculated when the unit tests are collected by
    # `pytest` before the patch to the `is_container` function is applied.
    # Reloading the modules within the test forces the `APPTAINER_PACKAGES` constant to be
    # re-calculated using the mocked return value of `is_container`.
    reload(constants)
    reload(apptainer)


@pytest.fixture(scope="function")
def expected(request) -> Any:
    return request.param
