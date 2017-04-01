FROM fedora:25
MAINTAINER Robpol86 <robpol86@gmail.com>

RUN dnf update -y && \
    dnf install -y dnf-plugins-core sudo && \
    dnf config-manager --add-repo=http://negativo17.org/repos/fedora-multimedia.repo && \
    dnf install -y makemkv && \
    dnf clean all && \
    sudo useradd -Ms /sbin/nologin -G cdrom mkv

VOLUME /output
WORKDIR /output
COPY run.sh /run.sh
COPY settings.conf /root/.MakeMKV/settings.conf

CMD ["/run.sh"]
