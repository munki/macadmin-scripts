### createbootvolfromautonbi.py

A tool to make bootable disk volumes from the output of autonbi. Especially
useful to make bootable disks containing Imagr and the 'SIP-ignoring' kernel,
which allows Imagr to run scripts that affect SIP state, set UAKEL options, and
run the `startosinstall` component, all of which might otherwise require network
booting from a NetInstall-style nbi.

Imagr (https://github.com/grahamgilbert/imagr) is a nice tool for automating Mac setup workflows. It is/was originally designed to be run from a Netboot volume, especially one created with the AutoNBI tool (https://github.com/bruienne/autonbi/). When run from a Netboot image created this way, Imagr runs as root, and SIP is ignored, enabling Imagr to do many of the needed tasks around setting up a machine for initial use.

But Netboot might not be available in your environment. And the new iMac Pro does not support Netboot. `createbootvolfromautonbi.py` allows you to create a bootable external drive (USB/Firewire/Thunderbolt) from the output of autonbi, and more specifically, the output of the `make nbi` Makefile target included with Imagr.

This would allow you to create an external boot drive with Imagr that can do what you can do with Imagr from an AutoNBI image.

#### Usage

```./createbootvolfromautonbi.py --nbi /path/to/Imagr.nbi --volume /Volumes/SomeEmptyExternalHFSPlusVolume```

