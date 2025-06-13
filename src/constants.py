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

"""Constants used within the Apptainer charmed operator."""

from hpc_libs.is_container import is_container

OCI_RUNTIME_INTEGRATION_NAME = "oci-runtime"

APPTAINER_PACKAGES = ["apptainer"] if is_container() else ["apptainer", "apptainer-suid"]
APPTAINER_PPA_URL = "https://ppa.launchpadcontent.net/apptainer/ppa/ubuntu/"
APPTAINER_PPA_KEY = """
-----BEGIN PGP PUBLIC KEY BLOCK-----
.
mQINBGPKLe0BEADKAHtUqLFryPhZ3m6uwuIQvwUr4US17QggRrOaS+jAb6e0P8kN
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
tBtMYXVuY2hwYWQgUFBBIGZvciBBcHB0YWluZXKJAk4EEwEKADgWIQT2sPUZPU8z
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
=kwio
-----END PGP PUBLIC KEY BLOCK-----
"""
