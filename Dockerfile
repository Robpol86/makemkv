FROM fedora:25
MAINTAINER Robpol86 <robpol86@gmail.com>

RUN dnf update -y && \
    dnf install -y dnf-plugins-core procps-ng sudo && \
    dnf config-manager --add-repo=http://negativo17.org/repos/fedora-multimedia.repo && \
    dnf install -y makemkv && \
    dnf clean all && \
    sudo useradd -s /sbin/nologin -G cdrom mkv && \
    sudo -u mkv mkdir /home/mkv/.MakeMKV

VOLUME /output
WORKDIR /output
COPY bin/env.sh /
COPY bin/rip.sh /
COPY etc/settings.conf /home/mkv/.MakeMKV/
COPY lib/wrappers.so /

CMD ["/rip.sh"]
