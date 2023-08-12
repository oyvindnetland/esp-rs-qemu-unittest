FROM rust
ARG USERNAME=esp
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN apt update \
    && apt install -y libudev-dev \
    python3 \
    python3-virtualenv \
    python3-pip \
    libxml2-dev \
    libclang-dev \
    libgcrypt20-dev \
    ninja-build \
    flex \
    bison

WORKDIR "/usr/local/src"
RUN git clone https://github.com/espressif/qemu.git
RUN mkdir qemu/build
WORKDIR "/usr/local/src/qemu/build"
RUN ../configure --target-list=xtensa-softmmu \
    --enable-gcrypt --enable-debug \
    --enable-sanitizers \
    --disable-strip --disable-user \
    --disable-capstone --disable-vnc \
    --disable-sdl --disable-gtk
RUN make

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # [Optional] Add sudo support. Omit if you don't need to install software after connecting.
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME

RUN cargo install cargo-generate
RUN cargo install ldproxy
RUN cargo install espup
RUN cargo install espflash
RUN cargo install cargo-espflash
RUN espup install --toolchain-version 1.69.0
RUN . ~/export-esp.sh
RUN rustup default esp

RUN echo "source ~/export-esp.sh" >> ~/.bashrc
ENV SHELL /bin/bash
