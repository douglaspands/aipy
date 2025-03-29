#! /usr/bin/python3
"""Support tools for Ollama"""

import argparse
import os
import platform
import shlex
import subprocess
import sys
import time
import tomllib
from pathlib import Path
from threading import Thread

with open(Path(__file__).parent.joinpath("pyproject.toml"), "rb") as file:
    pyproject = tomllib.load(file)

try:
    subprocess.check_output("nvidia-smi")
    NVIDIA_GPU = True
except BaseException:
    NVIDIA_GPU = False

APP_NAME = pyproject["project"]["name"]
APP_DESCRIPTION = pyproject["project"]["description"]
APP_VERSION = pyproject["project"]["version"]
AI_CORE = "ollama"
AI_GUI = "open-webui"
MODELS_CHOICE = [
    "gemma3:1b",
    "gemma3:4b",
    "llama3.1:8b",
    "llama3.2:1b",
    "llama3.2:3b",
    "qwen2.5:1.5b",
    "qwen2.5:3b",
    "qwen2.5:7b",
    "qwen2.5-coder:1.5b-base",
    "qwen2.5-coder:3b-base",
]
MODEL_DEFAULT = list(
    filter(lambda m: m == ("qwen2.5:7b" if NVIDIA_GPU else "qwen2.5:3b"), MODELS_CHOICE)
)[0]
DOCKER_COMPOSE_CHOICES = ["docker-compose.cpu.yaml", "docker-compose.gpu.yaml"]
DOCKER_COMPOSE_DEFAULT = (
    DOCKER_COMPOSE_CHOICES[1] if NVIDIA_GPU else DOCKER_COMPOSE_CHOICES[0]
)
DOCKER_COMPOSE_INIT = f"docker compose -f {DOCKER_COMPOSE_DEFAULT}"
DOCKER_COMPOSE_EXEC = f"{DOCKER_COMPOSE_INIT} exec {AI_CORE}"
APP_CMD_RUN_START = f"{DOCKER_COMPOSE_INIT} up"
APP_CMD_RUN_STOP = f"{DOCKER_COMPOSE_INIT} stop"
APP_CMD_RUN_CHAT = f"{DOCKER_COMPOSE_EXEC} ollama run " + "{model}"
APP_CMD_RUN_API_ONLY = f"{APP_CMD_RUN_START} {AI_CORE}"
APP_CMD_RUN_WEBUI = f"{APP_CMD_RUN_START} {AI_GUI}"
APP_CMD_UPDATE = f"{DOCKER_COMPOSE_INIT} pull"
APP_CMD_PULL = f"{DOCKER_COMPOSE_EXEC} ollama pull " + "{model}"
CMD_OPEN = (
    "powershell.exe -c 'start {}'"
    if (platform.system() == "Windows" or os.getenv("WSL_DISTRO_NAME"))
    else "sh -c 'xdg-open {}'"
)
APP_CMD_OPEN_WEBUI = CMD_OPEN.format(shlex.quote("http://localhost:8080"))
APP_CMD_OPEN_WEBUI_TIMER = 10.001
APP_CMD_LIST_LOCAL = f"{DOCKER_COMPOSE_EXEC} ollama list"
APP_CMD_LIST_REMOTE = f"{DOCKER_COMPOSE_EXEC} ollama list all models"


def shell_run(command: str | list[str]):
    cmd_prefix = f"cd {Path(__file__).resolve().parent}"
    cmd_system = " && ".join(
        [
            cmd
            for cmd in (
                [cmd_prefix] + command
                if isinstance(command, list)
                else [cmd_prefix, command]
            )
        ]
    )
    try:
        subprocess.run(cmd_system, shell=True, check=True)
    except KeyboardInterrupt:
        pass


def timer_run(command: str | list[str], ttl: int | float):
    time.sleep(ttl)
    shell_run(command)


def main():
    extras = []
    if NVIDIA_GPU:
        extras.append("gpu=on")
    exmsg = ("[" + ",".join(extras) + "]") if extras else ""

    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=f"{APP_NAME} - {APP_DESCRIPTION} (docker is required) {exmsg}",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    subparsers.add_parser(
        "version",
        help=f"show {APP_NAME} version",
        description=f"show {APP_NAME} version",
    )

    run_parser = subparsers.add_parser(
        "run",
        help=f"start/stop {AI_CORE}",
        description=f"start/stop {AI_CORE}",
    )

    run_toggle_parser = run_parser.add_subparsers(
        dest="toggle", help=f"start/stop {AI_CORE}", description=f"start/stop {AI_CORE}"
    )

    run_toggle_start_parser = run_toggle_parser.add_parser(
        "start",
        help=f"start {AI_CORE}",
        description=f"start {AI_CORE}",
    )

    run_toggle_start_parser.add_argument(
        "--with-webui",
        "-ww",
        action="store_true",
        default=False,
        help=f"start {AI_GUI} gui server ({AI_CORE} running is required)",
    )
    run_toggle_start_parser.add_argument(
        "--open",
        "-o",
        action="store_true",
        default=False,
        help=f"open page {AI_GUI} in browser (--with-webui before is required)",
    )

    run_toggle_parser.add_parser(
        "stop",
        help=f"stop {AI_CORE}",
        description=f"stop {AI_CORE}",
    )

    subparsers.add_parser(
        "update",
        help=f"update {AI_CORE}",
        description=f"update {AI_CORE}",
    )

    pull_parser = subparsers.add_parser(
        "pull",
        help=f"pull model ({AI_CORE} running is required)",
        description=f"Pull model ({AI_CORE} running is required)",
    )
    pull_help = ", ".join([f"'{m}'" for m in MODELS_CHOICE])
    pull_parser.add_argument(
        "model_name",
        metavar="MODEL_NAME",
        nargs=1,
        type=str,
        choices=MODELS_CHOICE,
        help=f"model's name with tag (ex.: {pull_help})",
    )

    list_parser = subparsers.add_parser(
        "list",
        help=f"list model ({AI_CORE} running is required)",
        description=f"list model ({AI_CORE} running is required)",
    )
    list_parser.add_argument(
        "source",
        metavar="SOURCE",
        nargs="?",
        type=str,
        choices=["local", "remote"],
        const="local",
        default="local",
        help=f"source of models for {AI_CORE}",
    )

    subparsers.add_parser(
        "open-webui",
        help=f"open {AI_GUI} ({AI_CORE} running is required)",
        description=f"open {AI_GUI} ({AI_CORE} running is required)",
    )

    chat_parser = subparsers.add_parser(
        "chat",
        help=f"{AI_CORE}'s chat ({AI_CORE} running is required)",
        description=f"{AI_CORE}'s chat ({AI_CORE} running is required)",
    )

    chat_parser.add_argument(
        "model_name",
        metavar="MODEL_NAME",
        nargs="?",
        type=str,
        const=MODEL_DEFAULT,
        default=MODEL_DEFAULT,
        choices=MODELS_CHOICE,
        help=f"initialize chat of the {AI_CORE} (default: '{MODEL_DEFAULT}')",
    )

    args = parser.parse_args().__dict__
    # print(f"{args=}")
    match args["subcommand"]:
        case "version":
            print(f"{APP_NAME}-v{APP_VERSION} {exmsg}")
        case "run":
            if args["toggle"] == "stop":
                shell_run(APP_CMD_RUN_STOP)
            else:
                if args.get("with_webui", False) is True:
                    if args.get("open", False) is True:
                        Thread(
                            target=timer_run,
                            args=(APP_CMD_OPEN_WEBUI, APP_CMD_OPEN_WEBUI_TIMER),
                            daemon=True,
                        ).start()
                    shell_run(APP_CMD_RUN_START)
                else:
                    shell_run(APP_CMD_RUN_API_ONLY)
        case "update":
            shell_run(APP_CMD_UPDATE)
        case "pull":
            model = args.get("model_name", MODEL_DEFAULT)
            shell_run(APP_CMD_PULL.format(model=model))
        case "list":
            if args.get("source", "local") == "remote":
                shell_run(APP_CMD_LIST_REMOTE)
            else:
                shell_run(APP_CMD_LIST_LOCAL)
        case "open_webui":
            Thread(
                target=timer_run,
                args=(APP_CMD_OPEN_WEBUI, APP_CMD_OPEN_WEBUI_TIMER),
                daemon=True,
            ).start()
            shell_run(APP_CMD_RUN_WEBUI)
        case "chat":
            model = args.get("model_name", MODEL_DEFAULT)
            print(f"> set model: {model} {exmsg}")
            shell_run(APP_CMD_RUN_CHAT.format(model=model))


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.exit()
