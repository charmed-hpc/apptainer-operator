#!/usr/bin/env python3
"""Apptainer operations."""
import logging
from pathlib import Path
from typing import Optional

import charms.operator_libs_linux.v0.apt as apt
import distro

logger = logging.getLogger()


APPTAINER_PPA_KEY: str = """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Comment: Hostname:
Version: Hockeypuck 2.1.0-223-gdc2762b

xsFNBGPKLe0BEADKAHtUqLFryPhZ3m6uwuIQvwUr4US17QggRrOaS+jAb6e0P8kN
1clzJDuh3C6GnxEZKiTW3aZpcrW/n39qO263OMoUZhm1AliqiViJgthnqYGSbMgZ
/OB6ToQeHydZ+MgI/jpdAyYSI4Tf4SVPRbOafLvnUW5g/vJLMzgTAxyyWEjvH9Lx
yjOAXpxubz0Wu2xcoefN0mKCpaPsa9Y8xmog1lsylU+H/4BX6yAG7zt5hIvadc9Z
Y/vkDLh8kNaEtkXmmnTqGOsLgH6Nc5dnslR6Gwq966EC2Jbw0WbE50pi4g21s6Wi
wdU27/XprunXhhLdv6PYUaqdXxPRdBh+9u0LmNZsAyUxT6EgN05TAWFtaMOz7I3B
V6IpHuLqmIcnqulHrLi+0D/aiCv53WEZrBRmDBGX7p52lcyS+Q+LFf0+iYeY7pRG
fPXboBDr+6DelkYFIxam06purSGR3T9RJyrMP7qMWiInWxcxBoCMNfy8VudP0DAy
r2yXmHZbgSGjfJey03dnNwQH7huBcQ1VLEqtL+bjn3HubmYK87FltX7xomETFqcl
QmiT+WBttFRGtO6SFHHiBXOXUn0ihwabtr6gRKeJssCnFS3Y46RDv4z3Je92roLt
TPY8F9CgZrGiAoKq530BzEhJB6vfW3faRnLKdLePX/LToCP0g2t2jKwkzQARAQAB
zRtMYXVuY2hwYWQgUFBBIGZvciBBcHB0YWluZXLCwY4EEwEKADgWIQT2sPUZPU8z
Ae9JH/Cv42U0/GIYrgUCY8ot7QIbAwULCQgHAgYVCgkICwIEFgIDAQIeAQIXgAAK
CRCv42U0/GIYrut4EAC06vTJP2wgnh3BIZ3n2HKaSp4QsuYKS7F7UQJ5Yt+PpnKn
Pgjq3R4fYzOHyASv+TCj9QkMaeqWGWb6Zw0n47EtrCW9U5099Vdk2L42KjrqZLiW
qQ11hwWXUlc1ZYSOb0J4WTumgO6MrUCFkmNrbRE7yB42hxr/AU/XNM38YjN2NyOK
2gvORRKFwlLKrjE+70HmoCW09Yk64BZl1eCubM/qy5tKzSlC910uz87FvZmrGKKF
rXa2HGlO4O3Ty7bMSeRKl9m1OYuffAXNwp3/Vale9eDHOeq58nn7wU9pSosmqrXb
SLOwqQylc1YoLZMj+Xjx644xm5e2bhyD00WiHeqHmvlfQQWCWaPt4i4K0nJuYXwm
BCA6YUgSfDZJfg/FxJdU7ero5F9st2GK4WDBiz+1Eftw6Ik/WnMDSxXaZ8pwnd9N
+aAEc/QKP5e8kjxJMC9kfvXGUVzZuMbkUV+PycZhUWl4Aelua91lnTicVYfpuVCC
GqY0StWQeOxLJneI+1FqLFoBOZghzoTY5AYCp99RjKqQvY1vF4uErltmNeN1vtBm
CZyDOLQuQfqWWAunUwXVuxMJIENSVeLXunhu9ac24Vnf2rFqH4XVMDxiKc6+sv+v
fKpamSQOUSmfWJTnry/LiYbspi1OB2x3GQk3/4ANw0S4L83A6oXHUMg8x7/sZw==
=E71P
-----END PGP PUBLIC KEY BLOCK-----
"""


class Apptainer:
    """Facilitate apptainer package lifecycle ops."""

    _package_name: str = "apptainer"
    _keyring_path: Path = Path("/usr/share/keyrings/apptainer.asc")

    def _repo(self) -> None:
        """Return the apptainer repo."""
        ppa_url: str = "https://ppa.launchpadcontent.net/apptainer/ppa/ubuntu"
        sources_list: str = (
            f"deb [signed-by={self._keyring_path}] {ppa_url} {distro.codename()} main"
        )
        return apt.DebianRepository.from_repo_line(sources_list)

    def install(self) -> None:
        """Install the apptainer package using lib apt."""
        # Install the key.
        if self._keyring_path.exists():
            self._keyring_path.unlink()
        self._keyring_path.write_text(APPTAINER_PPA_KEY)

        # Add the repo.
        repositories = apt.RepositoryMapping()
        repositories.add(self._repo())

        # Install the apptainer package.
        try:
            # Run `apt-get update`
            apt.update()
            apt.add_package(self._package_name)
        except apt.PackageNotFoundError:
            logger.error(f"{self._package_name} not found in package cache or on system")
        except apt.PackageError as e:
            logger.error(f"Could not install {self._package_name}. Reason: %s", e.message)

    def uninstall(self) -> None:
        """Uninstall the apptainer package using libapt."""
        # Uninstall the apptainer package.
        if apt.remove_package(self._package_name):
            logger.info(f"{self._package_name} removed from system.")
        else:
            logger.error(f"{self._package_name} not found on system")

        # Disable the apptainer repo.
        repositories = apt.RepositoryMapping()
        repositories.disable(self._repo())

        # Remove the key.
        if self._keyring_path.exists():
            self._keyring_path.unlink()

    def upgrade_to_latest(self) -> None:
        """Upgrade apptainer to latest."""
        try:
            apptainer = apt.DebianPackage.from_system(self._package_name)
            apptainer.ensure(apt.PackageState.Latest)
            logger.info("updated vim to version: %s", apptainer.fullversion)
        except apt.PackageNotFoundError:
            logger.error("a specified package not found in package cache or on system")
        except apt.PackageError as e:
            logger.error("could not install package. Reason: %s", e.message)

    def version(self) -> Optional[str]:
        """Return the apptainer version."""
        try:
            apptainer = apt.DebianPackage.from_installed_package(self._package_name)
        except apt.PackageNotFoundError:
            logger.error(f"{self.package_name} not found on system")
            return None
        return apptainer.fullversion
