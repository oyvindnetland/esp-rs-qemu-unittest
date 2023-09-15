#!/usr/bin/env python3

import json
import sys
import subprocess
import os
import argparse
import pathlib
from typing import Dict, Optional


class Command:
    def __init__(self, cmd: str, env: Dict[str, str] = os.environ.copy()):
        self._cmd = cmd
        self._env = env
        self._process: Optional[subprocess.Popen] = None
        self._running = False

    def start(self, cwd: Optional[str] = None):
        self._process = subprocess.Popen(
            self._cmd,
            env=self._env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            encoding='utf-8',
            errors='replace',
            universal_newlines=True,
        )
        self._running = True

    def readline(self) -> str:
        s = self._process.stdout.readline()
        if len(s) == 0:
            if self._process.poll() is not None:
                self._running = False
        if len(s) > 1:
            while s[-1] == '\n':
                s = s[:-1]
        return s

    def is_running(self) -> bool:
        return self._running

    def kill(self):
        self._running = False
        self._process.kill()

    def exit_code(self) -> Optional[int]:
        if self._running:
            return None
        self._process.wait()
        return self._process.returncode


def get_qemu_build_env() -> Dict[str, str]:
    build_env = os.environ.copy()
    build_env['ESP_IDF_SDKCONFIG_DEFAULTS'] = 'sdkconfig.defaults;sdkconfig.defaults.qemu'
    build_env['WIFI_SSID'] = ''
    build_env['WIFI_PASS'] = ''
    build_env['MQTT_URL'] = ''
    return build_env


def build_app_image() -> Optional[str]:
    output = 'target/xtensa-esp32-espidf/debug/esp-rs-qemu.bin'
    cmd = f'cargo espflash save-image --target xtensa-esp32-espidf --partition-table partitions.csv --chip esp32 --merge {output}'
    saving = Command(cmd, env=get_qemu_build_env())
    saving.start()
    while saving.is_running():
        print(saving.readline())
    if saving.exit_code() != 0:
        print(f'Running "{cmd}" failed: {saving.exit_code()}')
        return None

    print(f'Saving image to {output}')
    return output


def build_unittest() -> Optional[str]:
    cmd = 'cargo test --target xtensa-esp32-espidf --no-run'
    building = Command(cmd, env=get_qemu_build_env())
    building.start()

    found_exec = None
    while building.is_running():
        realtime_output = building.readline()
        if realtime_output:
            print(realtime_output)
            if 'Executable unittests' in realtime_output:
                found_exec = realtime_output.split('(')[1].split(')')[0]
    if building.exit_code() != 0:
        print(f'Running "{cmd}" failed: {building.exit_code()}')
        return None

    if found_exec is None:
        print('No executable found')
        return None

    print(f'Found executable {found_exec}')
    return found_exec


def save_unittest_image(found_exec: str) -> Optional[str]:
    output = 'target/xtensa-esp32-espidf/debug/esp-rs-qemu-unittest.bin'
    cmd = f'espflash save-image --partition-table partitions.csv  --chip esp32 --merge {found_exec} {output}'
    saving = Command(cmd)
    saving.start()
    while saving.is_running():
        print(saving.readline())
    if saving.exit_code() != 0:
        print(f'Running "{cmd}" failed: {saving.exit_code()}')
        return None

    print(f'Saving image to {output}')
    return output


def run_qemu(output: str, qemu_bin_path: str, debugging: bool = False) -> bool:
    cmd = f'{qemu_bin_path} -nographic -machine esp32 '
    if debugging:
        cmd += '-gdb tcp::1234 -S '
    cmd += f'-drive file={output},if=mtd,format=raw -no-reboot'
    qemu_run = Command(cmd)
    qemu_run.start()

    test_result = False
    while qemu_run.is_running():
        line = qemu_run.readline()
        print(line)
        if line.startswith('test result:'):
            test_result = 'ok' in line
            pids = subprocess.check_output(
                ['pidof', 'qemu-system-xtensa']).decode().split(' ')
            for pid in pids:
                try:
                    os.kill(int(pid), subprocess.signal.SIGKILL)
                except ValueError:
                    pass
            qemu_run.kill()
            break

    if qemu_run.exit_code() != -subprocess.signal.SIGKILL:  # if not killed
        print(f'Running "{cmd}" failed: {qemu_run.exit_code()}')
        return False

    if not test_result:
        print('Test failed')
        return False

    return True


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-q', '--qemu-bin-path',
                        default='/usr/local/src/qemu/build/qemu-system-xtensa', help='Path to qemu binary')
    subparsers = parser.add_subparsers(title='actions', dest='subcmd')

    subp_app = subparsers.add_parser(
        'app', description='Start application in QMEU')
    subp_app.add_argument(
        '-n', '--no-run', help='Only build, do not run', action='store_true')
    subp_app.add_argument(
        '-d', '--debugging', help='Run app in debugging mode', action='store_true')

    subp_unittest = subparsers.add_parser(
        'unittest', description='Start unittest in QMEU')
    subp_unittest.add_argument(
        '-n', '--no-run', help='Only build, do not run', action='store_true')
    subp_unittest.add_argument(
        '-d', '--debugging', help='Run unittest in debugging mode', action='store_true')

    subparsers.add_parser('vscode', description='Outputs json for vscode')

    args = parser.parse_args()

    if args.subcmd == 'app':
        print('Build app')
        image = build_app_image()
        if image is None:
            sys.exit(1)

        if not args.no_run:
            print('Run app in QEMU')
            res = run_qemu(image, args.qemu_bin_path, args.debugging)
            if not res:
                sys.exit(1)

        print('Done')

    if args.subcmd == 'unittest':
        print('Build unittest')
        exec = build_unittest()
        if exec is None:
            sys.exit(1)

        print('Save unittest image')
        image = save_unittest_image(exec)
        if image is None:
            sys.exit(1)

        if not args.no_run:
            print('Run unittest in QEMU')
            res = run_qemu(image, args.qemu_bin_path, args.debugging)
            if not res:
                sys.exit(1)

        print('Done')

    if args.subcmd == 'vscode':
        print('build unittests to get updated path names')
        exec = build_unittest()
        if exec is None:
            sys.exit(1)

        image = save_unittest_image(exec)
        if image is None:
            sys.exit(1)

        build_unittest_task = {
            'label': 'Build unittests for QEMU',
            'type': 'shell',
            'command': '${workspaceFolder}/qemu.py unittest --no-run',
            'problemMatcher': [],
            'group': {
                'kind': 'build',
                'isDefault': True
            }
        }

        print('task.json entry for building QMEU unittests:')
        print(json.dumps(build_unittest_task, indent=2))

        run_qmeu_unittest_debug_task = {
            'label': 'Run unittest on QEMU for debugging',
            'type': 'shell',
            'isBackground': True,
            'dependsOn': [
                'Build unittests for QEMU'
            ],
            'command': f'{args.qemu_bin_path} -gdb tcp::1234 -S -nographic -machine esp32 -drive file=${{workspaceFolder}}/{image},if=mtd,format=raw -no-reboot',
            'problemMatcher': [
                {
                    'pattern': [
                        {
                            'regexp': '.',
                            'file': 1,
                            'location': 2,
                            'message': 3
                        }
                    ],
                    'background': {
                        'activeOnStart': True,
                        'beginsPattern': '.',
                        'endsPattern': '.'
                    }
                }
            ],
        }

        print('task.json entry for building QMEU unittests:')
        print(json.dumps(run_qmeu_unittest_debug_task, indent=2))

        gdb_path = list(pathlib.Path('/workspaces/esp-rs-weather/.embuild').glob('**/xtensa-esp32-elf-gdb'))[0]
        attach_debug_unittest = {
            'preLaunchTask': 'Run unittest on QEMU for debugging',
            'name': 'Debug unittest on QEMU',
            'type': 'cppdbg',
            'request': 'launch',
            'program': f'${{workspaceFolder}}/{exec}',
            'args': [],
            'cwd': '${workspaceFolder}',
            'stopAtEntry': True,
            'environment': [],
            'externalConsole': False,
            'MIMode': 'gdb',
            'setupCommands': [
                {
                'description': 'Enable pretty-printing for gdb',
                'text': '-enable-pretty-printing',
                'ignoreFailures': True
                }
            ],
            'miDebuggerPath': str(gdb_path),
            'miDebuggerServerAddress': 'localhost:1234'
        }

        print('launch.json entry for attaching debug to QEMU unit tests:')
        print(json.dumps(attach_debug_unittest, indent=2))


if __name__ == '__main__':
    main()
