#!/bin/sh

# You might need to change this...
ESP_QEMU_PATH=/usr/local/src/qemu/build
BUILD=debug
TARGET=xtensa-esp32-espidf # Don't change this. Only the ESP32 chip is supported in QEMU for now

cargo build
cargo espflash save-image --partition-table partitions.csv --chip esp32 --merge target/$TARGET/$BUILD/esp-rs-qemu-unittest-app.bin
$ESP_QEMU_PATH/qemu-system-xtensa -nographic -machine esp32 -drive file=target/$TARGET/$BUILD/esp-rs-qemu-unittest-app.bin,if=mtd,format=raw
