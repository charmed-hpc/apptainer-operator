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

"""Unit tests for the `apptainer` manager."""

from charmed_hpc_libs.ops import AptOpsManager
from pytest_mock import MockerFixture

from apptainer import _APPARMOR_PROFILE, ApptainerManager


class TestApptainerManager:
    """Unit tests for the `ApptainerManager` class."""

    def test_install(self, mocker: MockerFixture) -> None:
        """Verify `install` writes the profile and reloads apparmor."""
        mock_install = mocker.patch.object(AptOpsManager, "install")
        mock_path = mocker.patch("apptainer._APPARMOR_PROFILE_PATH")
        mock_systemctl = mocker.patch("apptainer.systemctl")

        ApptainerManager().install()

        mock_install.assert_called_once_with(update=True)
        mock_path.write_text.assert_called_once_with(_APPARMOR_PROFILE)
        mock_systemctl.assert_called_once_with("reload", "apparmor")

    def test_remove(self, mocker: MockerFixture) -> None:
        """Verify `remove` unlinks the profile and reloads apparmor."""
        mock_remove = mocker.patch.object(AptOpsManager, "remove")
        mock_path = mocker.patch("apptainer._APPARMOR_PROFILE_PATH")
        mock_systemctl = mocker.patch("apptainer.systemctl")

        ApptainerManager().remove()

        mock_remove.assert_called_once_with(purge=True)
        mock_path.unlink.assert_called_once_with(missing_ok=True)
        mock_systemctl.assert_called_once_with("reload", "apparmor")
