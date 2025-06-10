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

"""Integration tests for the `apptainer` charm."""

from io import StringIO

import jubilant
import pytest
from dotenv import dotenv_values

from constants import APPTAINER_APP_NAME, DEFAULT_APPTAINER_CHARM_CHANNEL, UBUNTU_APP_NAME


@pytest.mark.order(1)
def test_deploy(juju: jubilant.Juju, base, apptainer) -> None:
    """Test if `apptainer` can successfully reach active status."""
    # Deploy `apptainer` and `ubuntu` charms. `ubuntu` is the principal for `apptainer`.
    juju.deploy(
        apptainer,
        APPTAINER_APP_NAME,
        base=base,
        channel=DEFAULT_APPTAINER_CHARM_CHANNEL if isinstance(apptainer, str) else None,
    )
    juju.deploy(
        "ubuntu",
        UBUNTU_APP_NAME,
        base=base,
    )

    # Integrate applications together.
    juju.integrate(APPTAINER_APP_NAME, UBUNTU_APP_NAME)

    # Wait for `apptainer` application to reach active status.
    juju.wait(lambda status: jubilant.all_active(status, APPTAINER_APP_NAME))


@pytest.mark.order(2)
def test_apptainer_exec(juju: jubilant.Juju) -> None:
    """Test that `apptainer` can successfully pull and exec commands from a container image."""
    unit = f"{APPTAINER_APP_NAME}/0"

    # Cache image locally before calling `apptainer exec ...`.
    juju.ssh(unit, "apptainer pull ubuntu.sif docker://ubuntu:jammy")
    result = juju.ssh(unit, "apptainer exec ubuntu.sif cat /etc/os-release")
    config = dotenv_values(stream=StringIO(result))

    assert config["VERSION_CODENAME"] == "jammy"

    # Call `apptainer exec ...` on remote image.
    result = juju.ssh(unit, "apptainer --silent exec docker://alpine:latest cat /etc/os-release")
    config = dotenv_values(stream=StringIO(result))

    assert config["ID"] == "alpine"
