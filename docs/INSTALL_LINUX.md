# PT2VHF APRS Client — instalação no Linux

O projeto publica versões oficiais para **Linux x86_64 / amd64** em .deb, AppImage e tar.gz.


## Arquiteturas suportadas

A partir da v1.8.18 existem pacotes oficiais para **x86_64/amd64** e **ARM64/aarch64**.

- x86_64: use arquivos com `x86_64` ou `amd64`.
- ARM64: use arquivos com `arm64`.
- Não misture arquiteturas. O updater integrado seleciona o pacote correspondente à arquitetura em execução.

## Arquivos da Release

- `PT2VHF_APRS_Client_x86_64_vX.Y.AppImage` — AppImage portátil.
- `PT2VHF_APRS_Client_Linux_x86_64_vX.Y.tar.gz` — pacote portátil genérico.
- `pt2vhf-aprs-client_X.Y_amd64.deb` — pacote para Debian/Ubuntu e derivados.

O cliente tenta abrir uma janela integrada. Se o ambiente gráfico não oferecer um backend WebView compatível, ele abre automaticamente a interface local no navegador padrão.

## Debian/Ubuntu — pacote .deb

Baixe o arquivo da Release e execute:

```bash
cd ~/Downloads
sudo apt install ./pt2vhf-aprs-client_1.6.22_amd64.deb
pt2vhf-aprs-client
```

Para remover o programa:

```bash
sudo apt remove pt2vhf-aprs-client
```

A remoção do pacote **não apaga** o banco local do usuário.

## AppImage

```bash
cd ~/Downloads
chmod +x PT2VHF_APRS_Client_x86_64_v1.6.22.AppImage
./PT2VHF_APRS_Client_x86_64_v1.6.22.AppImage
```

O AppImage é a opção portátil recomendada na v1.6.22. Quando o cliente indicar **Nova versão**, clicar no aviso baixa o AppImage correspondente, valida o arquivo, encerra a instância atual e substitui/reabre a nova versão automaticamente.

## Pacote portátil .tar.gz

```bash
cd ~/Downloads
mkdir -p ~/Aplicativos/PT2VHF-APRS-Client
tar -xzf PT2VHF_APRS_Client_Linux_x86_64_v1.6.22.tar.gz -C ~/Aplicativos/PT2VHF-APRS-Client
chmod +x ~/Aplicativos/PT2VHF-APRS-Client/PT2VHF_APRS_Client_Linux_x86_64_v1.6.22
~/Aplicativos/PT2VHF-APRS-Client/PT2VHF_APRS_Client_Linux_x86_64_v1.6.22
```

Quando a execução atual é identificada como pacote TAR.GZ, o atualizador integrado baixa o novo TAR.GZ, faz extração segura, preserva o banco local separado, substitui o executável e relança a nova versão. A atualização manual continua possível.

## Dados do usuário

Por padrão:

```text
~/.local/share/PT2VHF-APRS-Client/data/pt2vhf_aprs.db
```

Se a variável `XDG_DATA_HOME` estiver definida, o diretório passa a ser:

```text
$XDG_DATA_HOME/PT2VHF-APRS-Client/data/pt2vhf_aprs.db
```

## Janela integrada e fallback pelo navegador

A execução normal tenta usar a janela integrada. Em desktops onde GTK/WebKit2GTK ou outro backend compatível não estiver disponível, o programa informa a situação no terminal e abre a interface local. A aplicação começa tentando **127.0.0.1:8080**; se a porta já estiver ocupada, tenta **8081, 8082, 8083...** até encontrar uma livre.

Para forçar o navegador desde o início:

```bash
pt2vhf-aprs-client --browser
```

ou, na versão portátil:

```bash
~/Aplicativos/PT2VHF-APRS-Client/PT2VHF_APRS_Client_Linux_x86_64_v1.6.22 --browser
```

A interface continua restrita a `127.0.0.1`; não exponha a porta interna diretamente à Internet. A porta efetivamente escolhida aparece na própria aplicação e no terminal.

## Abrir também no navegador

Em **Configuração**, a opção **Abrir também no navegador ao iniciar** abre o navegador além da janela integrada. O padrão é desligado.

## Iniciar automaticamente com a sessão

Para o pacote .deb:

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/pt2vhf-aprs-client.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=PT2VHF APRS Client
Exec=/usr/local/bin/pt2vhf-aprs-client
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
```

Para a versão portátil, troque o caminho em `Exec=` pelo caminho completo do executável.

## Diagnóstico

Verifique primeiro qual porta foi informada como **Interface local** pela aplicação e teste essa URL, por exemplo:

```bash
curl -I http://127.0.0.1:8082/
```

Se a janela integrada não abrir, execute em modo navegador:

```bash
pt2vhf-aprs-client --browser
```

Para iniciar manualmente a versão Python a partir do código-fonte:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-linux.txt
python linux_app.py
```

## Testes e notificações

O workflow da v1.6 executa testes de núcleo em Ubuntu 22.04 e Ubuntu 24.04. Em desktops que fornecem `notify-send`, mensagens pessoais podem gerar notificações nativas quando o aviso de mensagem está habilitado.
