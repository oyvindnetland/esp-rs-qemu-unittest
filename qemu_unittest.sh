#!/bin/sh

# You might need to change this...
ESP_QEMU_PATH=/usr/local/src/qemu/build
BUILD=debug
TARGET=xtensa-esp32-espidf # Don't change this. Only the ESP32 chip is supported in QEMU for now

output_path=$(cargo test --no-run 2>&1 | grep -oP '(?<=Executable unittests src/main.rs \().*?(?=\))')
espflash save-image --chip esp32 --merge $output_path target/$TARGET/$BUILD/esp-rs-qemu-unittest.bin
$ESP_QEMU_PATH/qemu-system-xtensa -nographic -machine esp32 -drive file=target/$TARGET/$BUILD/esp-rs-qemu-unittest.bin,if=mtd,format=raw -no-reboot
