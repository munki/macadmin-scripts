### macadmin-scripts

Some scripts that might be of use to macOS admins. Might be related to Munki;
might not.

These are currently only supported using Apple's Python on macOS. There is no support for running these on Windows or Linux.

In macOS 12.3, Apple will be removing its Python 2.7 install. You'll need to provide your own Python to use these scripts. You may also need to install additional Python modules.

#### getmacosipsws.py

Quick-and-dirty tool to download the macOS IPSW files currently advertised by Apple in the https://mesu.apple.com/assets/macos/com_apple_macOSIPSW/com_apple_macOSIPSW.xml feed.

#### installinstallmacos.py

This script can create disk images containing macOS Installer applications available via Apple's softwareupdate catalogs.

Run `python ./installinstallmacos.py --help` to see the available options.

The tool assembles "Install macOS" applications by downloading the packages from Apple's softwareupdate servers and then installing them into a new empty disk image.

If `/usr/bin/installer` returns errors during this process, it can be useful to examine `/var/log/install.log` for clues.

Since it is using Apple's installer, any install check or volume check scripts are run. This means that you can only use this tool to create a diskimage containing the versions of macOS that will run on the exact machine you are running the script on.

For example, to create a diskimage containing the version 10.13.6 that runs on 2018 MacBook Pros, you must run this script on a 2018 MacBook Pro, and choose the proper version.

Typically "forked" OS build numbers are 4 digits, so when this document was last updated, build 17G2208 was the correct build for 2018 MacBook Pros; 17G65 was the correct build for all other Macs that support High Sierra.

If you attempt to install an incompatible version of macOS, you'll see an error similar to the following:

```
Making empty sparseimage...
installer: Error - ERROR_B14B14D9B7
Command '['/usr/sbin/installer', '-pkg', './content/downloads/07/20/091-95774/awldiototubemmsbocipx0ic9lj2kcu0pt/091-95774.English.dist', '-target', '/private/tmp/dmg.Hf0PHy']' returned non-zero exit status 1
Product installation failed.
```

Use a compatible Mac or select a different build compatible with your current hardware and try again. You may also have success running the script in a VM; the InstallationCheck script in versions of the macOS installer to date skips the checks (and returns success) when run on a VM. 

##### Important note for Catalina+
macOS privacy protections might interfere with the operation of this tool if you run it from ~/Desktop, ~/Documents, ~/Downloads or other directories protected in macOS Catalina or later. Consider using /Users/Shared (or subdirectory) as the "working space" for this tool.


##### Alternate implementations
Graham Pugh has a fork with a lot more features and bells and whistles. Check it out if your needs aren't met by this tool.
https://github.com/grahampugh/macadmin-scripts

