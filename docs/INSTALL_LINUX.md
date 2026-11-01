# PT2VHF APRS Client — Linux x86_64 e Raspberry Pi ARM64

A versão atual **1.15.6** tem distribuição nativa para duas arquiteturas. Para **Raspberry Pi 4 ou 5**, instale **Raspberry Pi OS 64-bit** (ou Debian/Ubuntu ARM64) e use um arquivo **arm64**. Raspberry Pi OS 32-bit (`armv7l`) e Raspberry Pi 3 com SO de 32 bits não são suportados pelos pacotes ARM64.

Confirme no terminal:

```bash
uname -m
dpkg --print-architecture
```

O resultado esperado no Raspberry Pi de 64 bits é `aarch64` e `arm64`. O AppImage `x86_64` não funciona nativamente em ARM64; o instalador Windows ARM64 também não funciona em Linux.

## Download para Raspberry Pi (Linux ARM64)

Obtenha os arquivos oficiais em https://www.pt2vhf.com/aprs:

- `PT2VHF_APRS_Client_arm64_v1.15.6.AppImage` — portátil, sem instalação.
- `pt2vhf-aprs-client_1.15.6_arm64.deb` — recomendado para Raspberry Pi OS 64-bit (Debian).
- `PT2VHF_APRS_Client_Linux_arm64_v1.15.6.tar.gz` — pacote portátil.

### Opção 1: DEB

```bash
cd ~/Downloads
sudo apt install ./pt2vhf-aprs-client_1.15.6_arm64.deb
pt2vhf-aprs-client --browser
```

### Opção 2: AppImage ARM64

```bash
cd ~/Downloads
chmod +x PT2VHF_APRS_Client_arm64_v1.15.6.AppImage
APPIMAGE_EXTRACT_AND_RUN=1 ./PT2VHF_APRS_Client_arm64_v1.15.6.AppImage --browser
```

O parâmetro `APPIMAGE_EXTRACT_AND_RUN=1` evita a dependência de FUSE e costuma ser útil no Raspberry Pi OS.

### Opção 3: TAR.GZ ARM64

```bash
cd ~/Downloads
mkdir -p ~/Aplicativos/PT2VHF-APRS-Client
tar -xzf PT2VHF_APRS_Client_Linux_arm64_v1.15.6.tar.gz -C ~/Aplicativos/PT2VHF-APRS-Client
chmod +x ~/Aplicativos/PT2VHF-APRS-Client/PT2VHF_APRS_Client_Linux_arm64_v1.15.6
~/Aplicativos/PT2VHF-APRS-Client/PT2VHF_APRS_Client_Linux_arm64_v1.15.6 --browser
```

## Linux x86_64 (Intel/AMD)

Continue usando `PT2VHF_APRS_Client_x86_64_v1.15.6.AppImage`, `pt2vhf-aprs-client_1.15.6_amd64.deb` ou `PT2VHF_APRS_Client_Linux_x86_64_v1.15.6.tar.gz`. São arquiteturas diferentes; nunca renomeie um pacote de uma arquitetura para outra.

## Janela integrada e navegador

A interface tenta usar WebView (GTK/WebKit), mas pode abrir pelo navegador local se o Raspberry Pi OS não tiver as bibliotecas gráficas necessárias. `--browser` força essa alternativa. É necessário ambiente gráfico/navegador para interagir com os mapas. Caso não abra, consulte o endereço da interface local exibido no terminal.

A aplicação começa tentando `127.0.0.1:8080` e usa portas seguintes quando necessário. Não exponha diretamente esse serviço à Internet. Em Configuração, a opção de acesso Web pela LAN possui controles próprios.

## Dados, atualização e desinstalação

Os dados são preservados fora dos executáveis, normalmente em `~/.local/share/PT2VHF-APRS-Client/data/pt2vhf_aprs.db` (ou sob `XDG_DATA_HOME`). O atualizador seleciona um instalador da **mesma arquitetura e formato**.

Remoção do DEB: `sudo apt remove pt2vhf-aprs-client`; o banco pessoal não é apagado.

Para conferir o serviço iniciado: `curl -I http://127.0.0.1:8080/` (ajuste a porta conforme o terminal).
