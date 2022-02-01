#!/usr/bin/env python
# encoding: utf-8
#
# Copyright 2021-2022 Greg Neagle.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Parses Apple's feed of macOS IPSWs and lets you download one'''

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import os
import plistlib
import subprocess
import sys
try:
    # python 2
    from urllib.parse import urlsplit
except ImportError:
    # python 3
    from urlparse import urlsplit
from xml.parsers.expat import ExpatError


class ReplicationError(Exception):
    '''A custom error when replication fails'''
    pass


def get_url(url,
            download_dir='/tmp',
            show_progress=False,
            attempt_resume=False):
    '''Downloads a URL and stores it in the download_dir.
       Returns a path to the replicated file.'''

    path = urlsplit(url)[2]
    filename = os.path.basename(path)
    local_file_path = os.path.join(download_dir, filename)
    if show_progress:
        options = '-fL'
    else:
        options = '-sfL'
    need_download = True
    while need_download:
        curl_cmd = ['/usr/bin/curl', options,
                    '--create-dirs',
                    '-o', local_file_path,
                    '-w', '%{http_code}']
        if not url.endswith(".gz"):
            # stupid hack for stupid Apple behavior where it sometimes returns
            # compressed files even when not asked for
            curl_cmd.append('--compressed')
        resumed = False
        if os.path.exists(local_file_path):
            if not attempt_resume:
                curl_cmd.extend(['-z', local_file_path])
            else:
                resumed = True
                curl_cmd.extend(['-z', '-' + local_file_path, '-C', '-'])
        curl_cmd.append(url)
        print("Downloading %s..." % url)
        need_download = False
        try:
            _ = subprocess.check_output(curl_cmd)
        except subprocess.CalledProcessError as err:
            if not resumed or not err.output.isdigit():
                raise ReplicationError(err)
            # HTTP error 416 on resume: the download is already complete and the
            # file is up-to-date
            # HTTP error 412 on resume: the file was updated server-side
            if int(err.output) == 412:
                print("Removing %s and retrying." % local_file_path)
                os.unlink(local_file_path)
                need_download = True
            elif int(err.output) != 416:
                raise ReplicationError(err)
    return local_file_path


def get_input(prompt=None):
    '''Python 2 and 3 wrapper for raw_input/input'''
    try:
        return raw_input(prompt)
    except NameError:
        # raw_input doesn't exist in Python 3
        return input(prompt)


def read_plist(filepath):
    '''Wrapper for the differences between Python 2 and Python 3's plistlib'''
    try:
        with open(filepath, "rb") as fileobj:
            return plistlib.load(fileobj)
    except AttributeError:
        # plistlib module doesn't have a load function (as in Python 2)
        return plistlib.readPlist(filepath)


def read_plist_from_string(bytestring):
    '''Wrapper for the differences between Python 2 and Python 3's plistlib'''
    try:
        return plistlib.loads(bytestring)
    except AttributeError:
        # plistlib module doesn't have a load function (as in Python 2)
        return plistlib.readPlistFromString(bytestring)

IPSW_DATA = None
def get_ipsw_data():
    '''Return data from com_apple_macOSIPSW.xml (which is actually a plist)'''
    global IPSW_DATA
    IPSW_FEED = "https://mesu.apple.com/assets/macos/com_apple_macOSIPSW/com_apple_macOSIPSW.xml"

    if not IPSW_DATA:
        try:
            ipsw_plist = get_url(IPSW_FEED)
            IPSW_DATA = read_plist(ipsw_plist)
        except (OSError, IOError, ExpatError, ReplicationError) as err:
            print(err, file=sys.stderr)
            exit(1)

    return IPSW_DATA

def getMobileDeviceSoftwareVersionsByVersion():
    '''return the MobileDeviceSoftwareVersionsByVersion dict'''
    ipsw_data = get_ipsw_data()
    return ipsw_data.get("MobileDeviceSoftwareVersionsByVersion", {})


def getMobileDeviceSoftwareVersions(version=1):
    '''Return the dict under the version number key. Current xml has only "1"'''
    return getMobileDeviceSoftwareVersionsByVersion().get("%s" % version, {})


def getMachineModelsForMobileDeviceSoftwareVersions(version=1):
    '''Get the model keys'''
    versions = getMobileDeviceSoftwareVersions(version=version).get(
        "MobileDeviceSoftwareVersions", {})
    return versions.keys()


def getSoftwareVersionsForMachineModel(model, version=1):
    '''Get the dict for a specific model'''
    versions = getMobileDeviceSoftwareVersions(version=version).get(
        "MobileDeviceSoftwareVersions", {})
    return versions[model]


def getIPSWInfoForMachineModel(model, version=1):
    '''Build and return a list of dict describing the available
       ipsw file for a specific model'''
    model_info_list = []
    model_versions = getSoftwareVersionsForMachineModel(model, version=version)
    for key in model_versions:
        if key == "Unknown":
            build_dict = model_versions["Unknown"].get("Universal", {})
        else:
            build_dict = model_versions[key]
        restore_info = build_dict.get("Restore")
        if restore_info:
            model_info = {"model": model}
            model_info.update(restore_info)
            model_info_list.append(model_info)
    return model_info_list


def getAllModelInfo(version=1):
    '''Build and return a list of all available ipsws'''
    all_model_info = []
    available_models = getMachineModelsForMobileDeviceSoftwareVersions(
        version=version)
    for model in available_models:
        model_info = getIPSWInfoForMachineModel(model, version=version)
        all_model_info.extend(model_info)
    return all_model_info


def main():
    '''Our main thing to do'''
    all_model_info = getAllModelInfo()
    # display a menu of choices
    print('%2s  %16s %10s %8s %11s'
          % ('#', 'Model', 'Version', 'Build', 'Checksum'))
    for index, item in enumerate(all_model_info):
        print('%2s  %16s %10s %8s %11s' % (
            index + 1,
            item["model"],
            item.get('ProductVersion', 'UNKNOWN'),
            item.get('BuildVersion', 'UNKNOWN'),
            item.get('FirmwareSHA1', 'UNKNOWN')[-6:]))

    answer = get_input(
        '\nChoose a product to download (1-%s): ' % len(all_model_info))
    try:
        index = int(answer) - 1
        if index < 0:
            raise ValueError
    except (ValueError, IndexError):
        print('Exiting.')
        exit(0)

    download_url = getAllModelInfo()[index].get("FirmwareURL")
    if download_url:
        try:
            filepath = get_url(download_url,
                download_dir=".", show_progress=True, attempt_resume=True)
            print("IPSW downloaded to: %s" % filepath)
        except (ReplicationError, IOError, OSError) as err:
            print(err, file=sys.stderr)
            exit(1)
    else:
        print("No valid download URL for that item.", file=sys.stderr)
        exit(1)


if __name__ == '__main__':
    main()
