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
    sudo docker run -it --device=/dev/cdrom -e MKV_GID=$(id -g media) -e MKV_UID=$(id -u media) -e UMASK=0002 \
        -v /storage/Local/MakeMKV:/output --log-opt tag=makemkv makemkv
