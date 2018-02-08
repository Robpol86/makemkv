# Headless DVD/BD Backups with MakeMKV

[circleci]: https://img.shields.io/circleci/project/github/Robpol86/makemkv/master.svg?style=flat-square&label=CircleCI "Build Status"
[![Build Status][circleci]](https://circleci.com/gh/Robpol86/makemkv)

Automatically backup your DVD and Bluray discs to local storage. When this Docker image is used together with
[udev rules](http://www.reactivated.net/writing_udev_rules.html) backups are as easy as inserting discs and then sitting
back until the drive ejects them. Rinse and repeat.

Note that this Docker image only decrypts and rips to MKV files. It does not transcode/convert files into smaller sizes
or other formats (this can be accomplished using hook scripts, more info below). Ripped Blurays may take up around
**40 GB** or so in my experience.

## Variables and Volumes

Below are the available environment variables you may use to configure this Docker image:

* **DEBUG** Enables debug output if set to "true".
* **DEVNAME** The path to the optical device (e.g. `/dev/cdrom`).
* **FAILED_EJECT** Eject the disc even when ripping fails if set to "true".
* **MKV_GID** The group ID of the `mkv` user inside the container.
* **MKV_UID** The user ID of the `mkv` user inside the container.
* **NO_EJECT** Disables ejecting the disc if set to "true".
* **UMASK** The umask to create directories and MKV files with.
* **TO_EMAIL** This is only usable if AWS Access Key and AWS Secret Access Key are set. The 'to' address that email notifications will be sent to on success and failure. You must verify this email or domain in AWS SES.
* **FROM_EMAIL** This is only usable if AWS Access Key and AWS Secret Access Key are set. The 'from' address that email notifications will come from on success and failure. You must verify this email in AWS SES.
* **AWS_ACCESS_KEY_ID** The AWS Access Key generated in AWS Identity and Access Management.
* **AWS_SECRET_ACCESS_KEY** The AWS Secret Access Key, also generated in AWS IAM.

By default **DEVNAME** is automatically detected. If you use the Docker `--privileged` flag (not needed nor recommended)
and have more than one optical device on your system this automated detection may not work. In these cases you'd want to
explicitly specify the path to the desired optical device.

Below are the available volumes used by the Docker image:

* **/output** Ripped MKV files are written to this directory inside the container.

## Hooks

This image exposes a few hooks you can use to add or alter functionality of most of the ripping process. An example use
case is to encode ripped files with ffmpeg after a successful rip. All hook files should be copied **to the root of the
image** and be named `hook-*.sh`. They'll be sourced by the main script so you'll have access to all of the environment
variables in your hook scripts.

* **/hook-post-env.sh** The start of the main script after defining some env variables.
* **/hook-pre-on-err.sh** When something fails `on_err` is called. This hook is fired before the call.
* **/hook-post-on-err.sh** Fired after `on_err` is called.
* **/hook-pre-prepare.sh** Before `prepare` is called, which finishes initializing the environment.
* **/hook-post-prepare.sh** After `prepare` is called.
* **/hook-pre-rip.sh** Before makemkvcon is executed.
* **/hook-post-title.sh** While makemkvcon runs after an MKV file is done.
* **/hook-post-rip.sh** After makemkvcon successfully exits.
* **/hook-end.sh** At the end of the main script after a successful run of makemkvcon.

The **/hook-post-title.sh** hook allows you to process an MKV file (named `$TITLE_PATH`) as soon as it's done ripping,
while makemkvcon rips the next file. Due to the way I've setup bash and makemkvcon to communicate (using a FIFO/named
pipe) your hook script shouldn't block. If you want to start a long-running process you should run it in the background
(the main script waits for all jobs to exit). Otherwise bash won't read from the pipe and makemkvcon will block (and
stop ripping) until your script is done.

The following hooks are only fired when `NO_EJECT!=true` and when makemkvcon successfully exits:

* **/hook-pre-success-eject.sh** Before the disc is ejected.
* **/hook-post-success-eject.sh** After the disc is ejected.

The following hooks are only fired when an error occurs:

* **/hook-pre-on-err-touch.sh** If the final directory is created before touching the `failed` file.
* **/hook-post-on-err-touch.sh** After touching the `failed` file.
* **/hook-pre-failed-eject.sh** When `NO_EJECT!=true` and `FAILED_EJECT==true` before the disc is ejected.
* **/hook-post-failed-eject.sh** When `NO_EJECT!=true` and `FAILED_EJECT==true` after the disc is ejected.

An example of hook scripts used with MakeMKV can be found in my orphaned branch here:
https://github.com/Robpol86/makemkv/tree/robpol86

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
mkdir /tmp/MakeMKV
sudo docker run -it --device=/dev/cdrom \
    -e MKV_GID=$(id -g) -e MKV_UID=$(id -u) \
    -v /tmp/MakeMKV:/output robpol86/makemkv
```

You should see something like this:

```
Unable to find image 'robpol86/makemkv:latest' locally
latest: Pulling from robpol86/makemkv
691bc14ee274: Pull complete
1197e486c122: Pull complete
7b1362b91005: Pull complete
0895c2c006e9: Pull complete
4d8ee1e190c3: Pull complete
438cb789657c: Pull complete
ad875900bb11: Pull complete
Digest: sha256:9ee3d0f93215c2dfda24f56c951c6a38a205f3d6fbb1fc7ee3f79d3
Status: Downloaded newer image for robpol86/makemkv:latest
Defaults umask = 0022
Ripping...
MakeMKV v1.10.5 linux(x64-release) started
Current operation: Scanning CD-ROM devices
Current action: Scanning CD-ROM devices
Current progress - 0%  , Total progress - 0%
...
Current progress - 92%  , Total progress - 0%
Current action: Saving to MKV file
Current progress - 0%  , Total progress - 0%
...
Current progress - 100%  , Total progress - 100%
8 titles saved
Copy complete. 8 titles saved.
Ejecting...
Done after 00:25:54
```

## Automated Run

Once you've verified this Docker image works fine on your system it's time to automate it. All you need is a simple udev
rule that runs the image and then cleans up by deleting the container after it's done ripping (leaving the ripped files
intact since they're in a volume). Note the udev rule file contents below. You'll want to change:

1. The **MKV_GID** and **MKV_UID** IDs to your user's.
2. The **/tmp/MakeMKV** file path to the directory that'll hold MKVs.

```
# Save as: /etc/udev/rules.d/85-makemkv.rules
SUBSYSTEM=="block", KERNEL=="sr[0-9]*", ACTION=="change", ENV{ID_CDROM_MEDIA}=="1", \
ENV{DEBUG}="true", ENV{MKV_GID}="1001", ENV{MKV_UID}="1001", \
RUN+="/bin/bash -c 'docker run -d --rm --device=%E{DEVNAME} --env-file=<(env) \
    -v /tmp/MakeMKV:/output robpol86/makemkv'"
```

After saving the file you don't need to reload anything or reboot. It should Just Work. Insert a disc and look for the
container in `sudo docker ps`. Make sure it's working by tailing the output with `sudo docker logs <CID> --follow`.

### Notifications

The one downside to the above automated run is that it deletes the container as soon as it finishes regardless if the
rip was successful. This means that you cannot look at the output when something fails (e.g. not enough disk space).

My solution to this problem is having the Docker daemon log to journald and setup a systemd service unit file that
watches for failed Docker containers and emails you the log output. More information on that here:
https://robpol86.github.io/influxdb/prepare.html#email-notifications
