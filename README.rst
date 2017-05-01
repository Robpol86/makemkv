=======
MakeMKV
=======

This branch is what I use on my home server. It uses the main Dockerfile with some bash hooks for my needs.

Quick Start
===========

.. code-block:: bash

    sudo mkdir /opt/makemkv; cd $_
    sudo git clone -b robpol86 https://github.com/Robpol86/makemkv.git .
    sudo docker build -t makemkv .
    sudo docker run -it --device=/dev/cdrom -v /storage/Local/MakeMKV:/output --log-opt tag=makemkv \
        -e MKV_GID=$(id -g media) -e MKV_UID=$(id -u media) -e UMASK=0002 makemkv

udev
====

.. code-block:: bash

    sudo tee /etc/udev/rules.d/85-makemkv.rules << EOF
    SUBSYSTEM=="block", KERNEL=="sr[0-9]*", ACTION=="change", ENV{ID_CDROM_MEDIA}=="1", \
    ENV{DEBUG}="true", ENV{UMASK}="0002", ENV{MKV_GID}="$(id -g media)", ENV{MKV_UID}="$(id -u media)", \
    RUN+="/bin/bash -c 'docker run -d --rm --device=%E{DEVNAME} --env-file=<(env) \
        --log-opt tag=makemkv -v /storage/Local/MakeMKV:/output makemkv'"
    EOF
