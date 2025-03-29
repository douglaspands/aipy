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
    chat                ollama's chat (ollama running is required)

options:
  -h, --help            show this help message and exit
```

Para inicializar o Ollama e o WebUI, execute o comando:
```sh
python iapy.py run start --with-webui --open
```
> Após a inicialização, será aberto no navegador para uso da interface WebUI. Tambem é possivel acessar usando o endereço: [http://localhost:8080](http://localhost:8080).
   
> O terminal fica preso para que sejá possivel finalizar os processo apenas encerrando o terminal. Então, para executar os proximos passos é necessario abrir outro terminal.

## Recomendações de modelos
Para instalar um modelo, recomendo acessar o site [Ollama's Model](https://ollama.com/search) e pesquisar que mais interesse.
Para baixar um modelo, execute o comando:
```sh
python aipy.py pull gemma3:1b
```
> `gemma3:1b` é um modelo bom e compativel com muitos hardwares.

Abaixo citarei modelos mais robustos que rodam somente em GPU e outros modelos que rodam em maquinas sem GPU.

#### Maquina com GPU
- `gemma3:4b`
- `llama3.1:8b`
- `qwen2.5:7b`
- `qwen2.5-coder:3b-base`

#### Maquina sem GPU
- `gemma3:1b`
- `llama3.2:1b`
- `llama3.2:3b`
- `qwen2.5:3b`
- `qwen2.5-coder:1.5b-base`
