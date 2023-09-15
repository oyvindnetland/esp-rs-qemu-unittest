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
- A qemu.py script that can bulid and run in QEMU

## qemu.py

### Run app

`./qemu.py app` will build and run the normal rust application in QEMU. The 
example applicaiton in this project is very simple and works well in QEMU, but 
more complicated applications that use the HW the ESP will probably work less well.

`./qemu.py unittest` will build and run the rust unittest in QEMU. It will also
exit QEMU when the test is done, so it could easily work in automated tests.

`./qemu.py vscode` generates entries to task.json and launch.json which can be used 
to debug unittests within vscode.
