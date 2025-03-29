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

APP_NAME = pyproject["project"]["name"]
APP_DESCRIPTION = pyproject["project"]["description"]
APP_VERSION = pyproject["project"]["version"]
AI_CORE = "ollama"
MODELS_CHOICE = ["gemma3:1b", "qwen2.5:1.5b", "qwen2.5:3b"]
MODEL_DEFAULT = MODELS_CHOICE[2]  # "qwen2.5:3b"
DOCKER_COMPOSE_CHOICES = ["docker-compose.cpu.yaml", "docker-compose.gpu.yaml"]
DOCKER_COMPOSE_DEFAULT = DOCKER_COMPOSE_CHOICES[0]  # cpu
DOCKER_COMPOSE_INIT = f"docker compose -f {DOCKER_COMPOSE_DEFAULT}"
DOCKER_COMPOSE_EXEC = f"{DOCKER_COMPOSE_INIT} exec ollama"
APP_CMD_RUN_START = f"{DOCKER_COMPOSE_INIT} up"
APP_CMD_RUN_STOP = f"{DOCKER_COMPOSE_INIT} stop"
APP_CMD_RUN_CHAT = f"{DOCKER_COMPOSE_EXEC} ollama run " + "{model}"
APP_CMD_RUN_API_ONLY = f"{APP_CMD_RUN_START} ollama"
APP_CMD_RUN_WEBUI = f"{APP_CMD_RUN_START} open-webui"
APP_CMD_UPDATE = f"{DOCKER_COMPOSE_INIT} pull"
APP_CMD_PULL = f"{DOCKER_COMPOSE_EXEC} ollama pull " + "{model}"
CMD_OPEN = (
    "powershell.exe -c 'start {}'"
    if (platform.system() == "Windows" or os.getenv("WSL_DISTRO_NAME"))
    else "sh -c 'xdg-open {}'"
)
APP_CMD_OPEN_WEBUI = CMD_OPEN.format(shlex.quote("http://localhost:8080"))
APP_CMD_OPEN_WEBUI_TIMER = 10.001
APP_CMD_LIST_LOCAL = "docker exec -it ollama ollama list"
APP_CMD_LIST_REMOTE = "docker exec -it ollama ollama list all models"


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
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=f"{APP_NAME} - {APP_DESCRIPTION} (docker is required)",
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

    run_parser.add_argument(
        "run_switch",
        choices=["start", "stop"],
        default="start",
        help=f"initialize or stopped the {AI_CORE}",
    )
    run_parser.add_argument(
        "--with-webui",
        action="store_true",
        default=False,
        help=f"running webui gui of the {AI_CORE}",
    )
    run_parser.add_argument(
        "-og",
        "--open-webui",
        action="store_true",
        default=False,
        help=f"open page webui in browser after initialize the {AI_CORE} (only --with-webui)",
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
        help=f"model's name with tag (ex.: {pull_help})",
    )

    list_parser = subparsers.add_parser(
        "list",
        help=f"list model ({AI_CORE} running is required)",
        description=f"list model ({AI_CORE} running is required)",
    )
    list_parser.add_argument(
        "source",
        nargs="?",
        type=str,
        choices=["local", "remote"],
        default="local",
        help=f"source of models for {AI_CORE}",
    )

    subparsers.add_parser(
        "open-webui",
        help=f"open webui ({AI_CORE} running is required)",
        description=f"open webui ({AI_CORE} running is required)",
    )

    chat_parser = subparsers.add_parser(
        "chat",
        help=f"{AI_CORE}'s chat (depends ollama running)",
        description=f"{AI_CORE}'s chat (depends ollama running)",
    )

    chat_parser.add_argument(
        "model_name",
        nargs="?",
        type=str,
        default=MODEL_DEFAULT,
        choices=MODELS_CHOICE,
        help=f"initialize chat of the {AI_CORE} (default: '{MODEL_DEFAULT}')",
    )

    args = parser.parse_args().__dict__
    # print(args)
    match args["subcommand"]:
        case "version":
            print(f"{APP_NAME}-v{APP_VERSION}")
        case "run":
            if args["run_switch"] == "stop":
                shell_run(APP_CMD_RUN_STOP)
            else:
                if args["with_webui"] is True:
                    if args["open"] is True:
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
            shell_run(APP_CMD_PULL.format(model=args["model_name"]))
        case "list":
            if args["source"] == "local":
                shell_run(APP_CMD_LIST_LOCAL)
            else:
                shell_run(APP_CMD_LIST_REMOTE)
        case "open_webui":
            Thread(
                target=timer_run,
                args=(APP_CMD_OPEN_WEBUI, APP_CMD_OPEN_WEBUI_TIMER),
                daemon=True,
            ).start()
            shell_run(APP_CMD_RUN_WEBUI)
        case "chat":
            shell_run(APP_CMD_RUN_CHAT.format(model=args["model_name"]))


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.exit()
