# AIPY
CLI de apoio para uso do Ollama.

## Dependencias
- Python >=3.11,<3.14
- Docker >=28.0.2
- Docker-Compose >=2.34.0

## Como usar
```sh
python aipy.py --help

# output
usage: aipy [-h] {version,run,update,pull,list,open-webui,chat} ...

aipy - ollama's support tools (docker is required)

positional arguments:
  {version,run,update,pull,list,open-webui,chat}
    version             show aipy version
    run                 start/stop ollama
    update              update ollama
    pull                pull model (ollama running is required)
    list                list model (ollama running is required)
    open-webui          open webui (ollama running is required)
    chat                ollama's chat (depends ollama running)

options:
  -h, --help            show this help message and exit
```
