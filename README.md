# Headless DVD/BD Backups with MakeMKV

> NOTE: This repo is a work in progress.

Automatically backup your DVD and Bluray discs to local storage. When this Docker image is used together with
[udev rules](http://www.reactivated.net/writing_udev_rules.html) backups are as easy as inserting discs and then sitting
back until the drive ejects the disc. Rinse and repeat.

## Variables and Volumes

Below are the available environment variables you may use to configure this Docker image:

* **MKV_GID** The group ID of the `mkv` user inside the container.
* **MKV_UID** The user ID of the `mkv` user inside the container.

And below are the available volumes used by the Docker image:

* **/output** Ripped MKV files are written to this directory inside the container.

## Run Manually

Before setting up the automated run it's a good idea to try running this manually to see the output it produces in case
there are any compatibility or other issues. First make sure you've got your optical drive plugged in (if it's external)
and that you can see `/dev/cdrom` on your system:

```
$ ls -lah /dev/cdrom
lrwxrwxrwx. 1 root root 3 Mar 31 17:12 /dev/cdrom -> sr0
```

Now go ahead and run the image:

```bash
mkdir ~/videos
sudo docker run -it \
    --device=/dev/cdrom \
    -e MKV_GID=$(id -g) \
    -e MKV_UID=$(id -u) \
    -v ~/videos:/output \
    robpol86/makemkv
```

You should see something like this:

```
TODO
```
## Automated Run

TODO
