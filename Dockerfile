FROM espressif/idf-rust:all_1.71.0.1
ARG USERNAME=esp
ARG USER_UID=1000
ARG USER_GID=$USER_UID

USER root

RUN apt update \
    && apt install -y libudev-dev \
    sudo \
    python3 \
    python3-virtualenv \
    python3-pip \
    libxml2-dev \
    libclang-dev \
    libgcrypt20-dev \
    ninja-build \
    flex \
    bison \
    libglib2.0-dev \
    libpixman-1-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgif-dev \
    procps \
    htop

RUN echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

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

# add to dialout group for serial port access
RUN usermod --append --groups dialout $USERNAME

USER $USERNAME

# re-install espflash and cargo-espflash since the supplied versions have library issues
RUN cargo install espflash -f
RUN cargo install cargo-espflash -f
RUN rustup default esp

# store bash history in a folder that can be mounted to the host
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=~/history/.bash_history" \
    && mkdir /home/$USERNAME/history/ \
    && touch /home/$USERNAME/history/.bash_history \
    && chown -R $USERNAME /home/$USERNAME/history \ 
    && echo "$SNIPPET" >> ~/.bashrc

# makes sure the correct clang library is used for esp-rs
RUN echo "export CLANG_LIB=$(find /home/${USERNAME} -name libclang.so)" >> ~/.bashrc

ENV SHELL /bin/bash
