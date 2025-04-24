#! /usr/bin/python3

import argparse
import os
import platform
import shlex
import subprocess
import sys
import time
import tomllib
import urllib.request
from functools import cache
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
APP_CMD_UPGRADE = f"{DOCKER_COMPOSE_INIT} pull"
APP_CMD_PULL = f"{DOCKER_COMPOSE_EXEC} ollama pull " + "{model}"
APP_CMD_RM = f"{DOCKER_COMPOSE_EXEC} ollama rm " + "{model}"
CMD_OPEN = (
    "powershell.exe -c 'start {}'"
    if (platform.system() == "Windows" or os.getenv("WSL_DISTRO_NAME"))
    else "sh -c 'xdg-open {}'"
)
WEBUI_URL = "http://localhost:8080"
APP_CMD_OPEN_WEBUI = CMD_OPEN.format(shlex.quote(WEBUI_URL))
APP_CMD_LIST_LOCAL = f"{DOCKER_COMPOSE_EXEC} ollama list"
APP_CMD_LIST_REMOTE = f"{DOCKER_COMPOSE_EXEC} ollama list all models"
USER_WAIT_TIME = 2.5
USER_RETRY = 10


def shell_run(
    command: str | list[str], capture_output=False
) -> subprocess.CompletedProcess[str]:
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
        kwargs = {
            "args": cmd_system,
            "shell": True,
        }
        if capture_output:
            kwargs.update(
                {
                    "text": True,
                    "capture_output": capture_output,
                }
            )
        return subprocess.run(**kwargs)
    except KeyboardInterrupt:
        pass


def browser_open_url() -> int:
    count = 0
    while True:
        if not (count < USER_RETRY):
            print(
                f"the limit of {USER_RETRY} attempts has been exceeded, probably the {AI_GUI} server is not running"
            )
            return 1
        try:
            with urllib.request.urlopen(WEBUI_URL) as response:
                if response.getcode() == 200:
                    break
        except BaseException:
            pass
        count += 1
        time.sleep(USER_WAIT_TIME)
    shell_run(APP_CMD_OPEN_WEBUI)
    return 0


@cache
def get_local_models() -> list[str]:
    result = shell_run(
        f"{APP_CMD_LIST_LOCAL} | awk '{{print $1}}'", capture_output=True
    )
    models = [m.strip() for m in result.stdout.splitlines()[1:]]
    return models


def ollama_is_running() -> bool:
    result = shell_run(f"{DOCKER_COMPOSE_EXEC} ollama --version", capture_output=True)
    return True if result.stdout else False


def docker_is_running() -> bool:
    result = shell_run("docker --version", capture_output=True)
    docker_is_enable = True if result.stdout else False
    result = shell_run("docker compose version", capture_output=True)
    compose_is_enable = True if result.stdout else False
    return docker_is_enable is True and compose_is_enable is True


def main() -> int | None:
    extras = []
    if NVIDIA_GPU:
        extras.append("gpu=on")
    extras_help = (" [" + ",".join(extras) + "]") if extras else ""
    models_help = ", ".join([f"'{m}'" for m in MODELS_CHOICE])
    local_models_help = ", ".join([f"'{m}'" for m in get_local_models()])
    ollama_running_help = (
        "" if ollama_is_running() else f" ({AI_CORE} running is required)"
    )
    docker_running_help = "" if docker_is_running() else " (docker is required)"
    kw_choice = {}
    if models_installed := get_local_models():
        kw_choice["choices"] = models_installed

    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=f"{APP_NAME} - {APP_DESCRIPTION}{docker_running_help}{extras_help}",
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
        "--daemon",
        "-d",
        action="store_true",
        default=False,
        help="server in daemon mode",
    )

    run_toggle_start_parser.add_argument(
        "--with-webui",
        "-ww",
        action="store_true",
        default=False,
        help=f"start {AI_GUI} gui server{ollama_running_help}",
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
        "upgrade",
        help=f"upgrade {AI_CORE} and {AI_GUI}",
        description=f"upgrade {AI_CORE} and {AI_GUI}",
    )

    pull_parser = subparsers.add_parser(
        "pull",
        help=f"pull model{ollama_running_help}",
        description=f"Pull model{ollama_running_help}",
    )

    pull_parser.add_argument(
        "model_name",
        metavar="MODEL_NAME",
        nargs="+",
        type=str,
        help=f"model's name with tag (ex.: {models_help})",
    )

    rm_parser = subparsers.add_parser(
        "rm",
        help=f"remove model{ollama_running_help}",
        description=f"Remove model{ollama_running_help}",
    )

    rm_parser.add_argument(
        "model_name",
        metavar="MODEL_NAME",
        nargs="+",
        type=str,
        **kw_choice,
        help=f"model's name with tag{f' (ex.: {local_models_help})' if local_models_help else ''}",
    )

    list_parser = subparsers.add_parser(
        "list",
        help=f"list model{ollama_running_help}",
        description=f"list model{ollama_running_help}",
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

    open_webui_parser = subparsers.add_parser(
        "open-webui",
        help=f"open {AI_GUI}{ollama_running_help}",
        description=f"open {AI_GUI}{ollama_running_help}",
    )

    open_webui_parser.add_argument(
        "--with-webui",
        "-ww",
        action="store_true",
        default=False,
        help=f"start {AI_GUI} gui server{ollama_running_help}",
    )

    chat_parser = subparsers.add_parser(
        "chat",
        help=f"{AI_CORE}'s chat{ollama_running_help}",
        description=f"{AI_CORE}'s chat{ollama_running_help}",
    )

    chat_parser.add_argument(
        "model_name",
        metavar="MODEL_NAME",
        nargs=1,
        type=str,
        **kw_choice,
        help=f"initialize chat of the {AI_CORE}{f' (ex.: {local_models_help})' if local_models_help else ''}",
    )

    args = parser.parse_args().__dict__
    print(args)
    match args["subcommand"]:
        case "version":
            print(f"{APP_NAME}-v{APP_VERSION}{extras_help}")
        case "run":
            if args["toggle"] == "stop":
                shell_run(APP_CMD_RUN_STOP)
            else:
                print(f"> gpu mode: {'on' if NVIDIA_GPU else 'off'}")
                time.sleep(USER_WAIT_TIME)
                if args.get("with_webui", False) is True:
                    if args.get("open", False) is True:
                        Thread(
                            target=browser_open_url,
                            daemon=True,
                        ).start()
                    shell_run(
                        APP_CMD_RUN_START + " -d" if args["daemon"] is True else ""
                    )
                else:
                    shell_run(
                        APP_CMD_RUN_API_ONLY + " -d" if args["daemon"] is True else ""
                    )
        case "upgrade":
            shell_run(APP_CMD_UPGRADE)
        case "pull":
            for model in args.get("model_name") or []:
                shell_run(APP_CMD_PULL.format(model=model))
        case "rm":
            for model in args.get("model_name") or []:
                shell_run(APP_CMD_RM.format(model=model))
        case "list":
            if args.get("source", "local") == "remote":
                shell_run(APP_CMD_LIST_REMOTE)
            else:
                shell_run(APP_CMD_LIST_LOCAL)
        case "open-webui":
            if args.get("with_webui", False) is True:
                Thread(
                    target=browser_open_url,
                    daemon=True,
                ).start()
                shell_run(APP_CMD_RUN_WEBUI)
            else:
                return browser_open_url()
        case "chat":
            for model in args.get("model_name") or []:
                print(f"> set model: {model}{extras_help}")
                time.sleep(USER_WAIT_TIME)
                shell_run(APP_CMD_RUN_CHAT.format(model=model))
                break


if __name__ == "__main__":
    sys.exit(main())
