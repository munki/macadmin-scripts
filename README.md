### macadmin-scripts

Some scripts that might be of use to macOS admins. Might be related to Munki;
might not.

#### installinstallmacos.py

This script can create disk images containing macOS Installer applications available via Apple's softwareupdate catalogs.

Run `./installinstallmacos.py --help` to see the available options.

The tool assembles "Install macOS" applications by downloading the packages from Apple's softwareupdate servers and then installing them into a new empty disk image.

If `/usr/bin/installer` returns errors during this process, it can be useful to examine `/var/log/install.log` for clues.

Disk images of "forked" OS builds can now be made from any Mac that supports the tool, because
install checks on packages are bypassed with the `CM_BUILD` environmental variable set to `CM_BUILD`.

Graham Pugh has a fork with a lot more features and bells and whistles. Check it out if your needs aren't met by this tool. https://github.com/grahampugh/macadmin-scripts

#### createbootvolfromautonbi.py

(This tool has not been tested/updated since before 10.14 shipped. It may not work as expected with current versions of macOS. There are currently no plans to update it.)

A tool to make bootable disk volumes from the output of autonbi. Especially
useful to make bootable disks containing Imagr and the 'SIP-ignoring' kernel,
which allows Imagr to run scripts that affect SIP state, set UAKEL options, and
run the `startosinstall` component, all of which might otherwise require network
booting from a NetInstall-style nbi.

This provides a way to create a bootable external disk that acts like the Netboot environment used by/needed by Imagr.

This command converts the output of Imagr's `make nbi` into a bootable external USB disk:
`sudo ./createbootvolfromautonbi.py --nbi ~/Desktop/10.13.6_Imagr.nbi --volume /Volumes/ExternalDisk`


#### make_firmwareupdater_pkg.sh

This script was used to extract the firmware updaters from early High Sierra installers and make a standalone installer package that could be used to upgrade Mac firmware before installing High Sierra via imaging.

Later High Sierra installer changes have broken this script; since installing High Sierra via imaging is not recommended or supported by Apple and several other alternatives are now available, I don't plan on attempting to fix or upgrade this tool.

