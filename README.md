# esp-rs-qemu-unittest
Example project for running esp-rs unit tests on QEMU

This is currently very much an experiment and work in progress.

## Motivation
I wanted to make it possibly to use test driven development on esp-rs, and I didn't find a way to do that easily and efficient.

Running `cargo test`, when in esp context, automatically flashed test application to a target, which i guess is fine in some cases, but it does mean that running tests take longer time. Also, obviously, it means that you need a esp device connected to do tests.

Running `cargo test` outside of esp context means that it will try to compile the project for host, which will fail out of the box. This could probably be fixed by defining a whole set of rules for how to build for host vs esp, but that will take significant effort to set up and maintain.

Using Wokwi might be a possibility, but I did not manage to set that up in a convenient way. Also, sending unit tests to run on an external server seems unnecessary.

So, then I started to look at QEMU, which at least has the potential of nice combination of running on host and target.
- Since its an emulator, it can run code built for esp without having to remove all the code and libraries that does not build for host.
- Since its an emulator, it can run the test on host.

## Content of this repo
- Dockerfile that build a container with xtensa (esp32) qemu.
- .devcontainer.json that can be used by vscode to start a devcontainer (the rest of this readme will assume this is done, if the Dockerfile is used in another way or this is set up on host directly the results may vary).
- Basic cargo/rust files for a esp32 project.
- A main.rs file with a very simple application (main function) and a very simple unit test.
- A qemu_application.sh script that will build and run the application in QEMU.
- A qemu_unittest.sh script that will build and run the unit tests in QEMU.

## Known issues
- The bash scripts feels a bit clunky, but works for now. Might attempt to make it a `cargo qemu-test` command or something similar (but i don't really know how that works)
- If the unit tests pass then the qemu command will not exit, just freeze (Ctrl-A X to exit). Hopefully this is possible to fix somehow (if unittest fails, the command will exit due to `-no-reboot`).
- The output is currently a bit verbose, would be nice to get just the unit test output.
- Will not work for testing drivers/hardware abstraction layers (maybe possible if used with https://github.com/dbrgn/embedded-hal-mock). Many would argue that this might not be the best use for unit tests, but would be nice to provide the possibility at some point.
