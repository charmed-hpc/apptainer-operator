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

"""Manage `apptainer` installation on Juju units."""

import logging
import shutil
import subprocess
from string import Template

import charms.operator_libs_linux.v0.apt as apt
import distro

from constants import APPTAINER_PACKAGES, APPTAINER_PPA_KEY, APPTAINER_PPA_URL

_logger = logging.getLogger(__name__)


class ApptainerOpsError(Exception):
    """Exception raised when an `apptainer`-related operation on the unit has failed."""

    @property
    def message(self) -> str:
        """Return message passed as argument to exception."""
        return self.args[0]


def install() -> None:
    """Install `apptainer`.

    Raises:
        ApptainerOpsError: Raised if `apt` fails to install `apptainer` on the unit.

    Notes:
        This function uses the `apptainer` packages hosted within the
        upstream Apptainer PPA located at https://ppa.launchpadcontent.net/apptainer/ppa/ubuntu.
    """
    try:
        _logger.info("adding `apptainer` ppa '%s' to /etc/apt/sources.list.d", APPTAINER_PPA_URL)
        ppa = apt.DebianRepository(
            enabled=True,
            repotype="deb",
            uri=APPTAINER_PPA_URL,
            release=distro.codename(),
            groups=["main"],
        )
        ppa.import_key(APPTAINER_PPA_KEY)
        repositories = apt.RepositoryMapping()
        repositories.add(ppa)
        _logger.info(
            "`apptainer` ppa '%s' successfully added to /etc/apt/sources.list.d", APPTAINER_PPA_URL
        )

        apt.update()
        _logger.info("installing packages `%s` using apt", APPTAINER_PACKAGES)
        apt.add_package(APPTAINER_PACKAGES)
        _logger.info("packages `%s` successfully installed on unit", APPTAINER_PACKAGES)
    except (apt.GPGKeyError, apt.PackageNotFoundError, apt.PackageError) as e:
        raise ApptainerOpsError(
            f"failed to install apptainer packages `{APPTAINER_PACKAGES}`. reason: {e}"
        )


def upgrade() -> None:
    """Upgrade `apptainer` to the latest available version.

    Raises:
        ApptainerOpsError: Raised if `apt` fails to upgrade the version of `apptainer` on the unit.
    """
    for name in APPTAINER_PACKAGES:
        try:
            package = apt.DebianPackage.from_installed_package(name)
            package.ensure(apt.PackageState.Latest)
        except (apt.PackageNotFoundError, apt.PackageError) as e:
            raise ApptainerOpsError(
                (
                    f"failed to upgrade packages `{APPTAINER_PACKAGES}` to the latest version. "
                    + f"reason: {e}"
                )
            )


def remove() -> None:
    """Remove `apptainer`."""
    try:
        _logger.info("removing packages `%s` using apt", APPTAINER_PACKAGES)
        apt.remove_package(APPTAINER_PACKAGES)
        _logger.info("packages `%s` successfully removed from unit", APPTAINER_PACKAGES)
    except apt.PackageNotFoundError as e:
        raise ApptainerOpsError(
            f"failed to remove apptainer packages `{APPTAINER_PACKAGES}`. reason: {e}"
        )


def version() -> str:
    """Get the current version of `apptainer` installed on the unit.

    Raises:
        ApptainerOpsError: Raised if `apptainer` is not installed on unit.
    """
    error_msg = Template("failed to get the version of `apptainer` installed. reason: $reason")
    try:
        result = subprocess.check_output(["apptainer", "--version"], text=True)
        return result.split()[-1]
    except FileNotFoundError as e:
        raise ApptainerOpsError(error_msg.substitute(reason=str(e).lower()))
    except subprocess.CalledProcessError as e:
        raise ApptainerOpsError(error_msg.substitute(reason=(str(e) + f" {e.stderr}").lower()))


def installed() -> bool:
    """Check if `apptainer` is both installed on the unit and available on `$PATH`."""
    try:
        apt.DebianPackage.from_installed_package("apptainer")
    except apt.PackageNotFoundError:
        return False

    return True if shutil.which("apptainer") else False
