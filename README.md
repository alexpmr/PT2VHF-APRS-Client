# PT2VHF APRS Client - v1.4

Cliente APRS-IS multiplataforma para **Windows, Linux e macOS**, com mapa, mensagens, estações, tracklogs, topologia observada, Log TNC2 e banco SQLite local.

A v1.4 é um hotfix de estabilidade: evita que o carregamento do mapa bloqueie toda a interface e torna a conexão APRS-IS mais rápida para falhar, mais clara para diagnosticar e mais tolerante a problemas de IPv6, DNS ou servidor.

## Downloads

Cada Release publica, conforme o build:

### Windows
- `PT2VHF_APRS_Client_Setup_x64_vX.Y.exe` - instalador recomendado.
- `PT2VHF_APRS_Client_Portable_x64_vX.Y.exe` - versão portátil.

### Linux
- `PT2VHF_APRS_Client_Linux_x86_64_vX.Y.tar.gz` - pacote portátil.
- `pt2vhf-aprs-client_X.Y_amd64.deb` - Debian/Ubuntu e derivados.

### macOS
- `PT2VHF_APRS_Client_macOS_arm64_vX.Y.dmg` - Apple Silicon.
- `PT2VHF_APRS_Client_macOS_x86_64_vX.Y.dmg` - Macs Intel.

### Manual
- `PT2VHF_APRS_Client_Manual_vX.Y.pdf` - manual profissional com capa azul, logo oficial, screenshots reais e changelog da versão.

## Principais recursos

### Mapa
- OpenStreetMap, OpenTopoMap e Esri World Imagery.
- Símbolos APRS.
- Tracklogs automáticos de estações móveis.
- Topologia observada a partir de paths APRS.
- Filtros da topologia por 1 h, 6 h, 24 h e 7 dias.
- Cor dos enlaces RF e IGate e espessura das linhas configuráveis.
- Centro e zoom persistidos.
- Controle para centralizar na localização disponibilizada pelo sistema/navegador.

### Mensagens
- Mensagens individuais APRS com IDs, ACK/REJ e ACK automático.
- Boletins gerais e de grupo.
- Fluxo de chat com mensagens novas na parte inferior.
- Opção **Agrupar por remetente**.
- Clique nos indicativos **De** ou **Para** para responder.
- Mensagens longas divididas automaticamente em partes APRS.
- Aviso compacto e não bloqueante quando a aba Mensagens está aberta, com duração configurável.

### Estações e Log
- Última recepção, distância, velocidade, curso, altitude e informação.
- Clique na estação para abri-la no mapa.
- Log bruto TNC2 RX/TX com filtros.
- Passcode mascarado no Log.
- Formatação independente para Mensagens, Estações e Logs: fonte, tamanho, negrito e espaçamento entre linhas.

## Configuração v1.4

A tela é dividida em:

1. **APRS / Estação** - indicativo, SSID, passcode, posição, ícone, servidor, porta, filtro e beacon.
2. **Aplicativo** - mapa, cores, topologia, tema, idioma, fontes, comportamento e backup.

### Coordenadas

Latitude e longitude podem ser informadas em:

- decimal;
- graus/minutos/segundos (DMS).

Na primeira execução, o cliente solicita permissão de geolocalização. Quando autorizada, Latitude e Longitude são pré-preenchidas e o mapa é centralizado na posição atual. O botão **Usar minha localização atual** permanece disponível para atualizar esses dados depois.

Quando o sistema não fornece altitude confiável, o cliente usa **0 m** para não bloquear a conexão e mostra um aviso recomendando informar a altitude real. Uma altitude manual não é substituída por esse valor automático.

Ao tentar conectar sem Indicativo, Latitude, Longitude ou Altitude, o programa mostra um **pop-up com os campos ausentes** e um botão **Ir para Configuração**. Ao abrir **Configuração > APRS / Estação**, todos os campos pendentes ficam destacados.

### APRS-IS

O servidor padrão da v1.3 é `soam.aprs2.net:14580`. O campo de servidor oferece sugestões regionais, continua aceitando valores manuais e o cliente tenta `rotate.aprs2.net` como alternativa quando o servidor sul-americano não pode ser alcançado.

O **Passcode APRS-IS** é calculado automaticamente a partir do indicativo-base; o SSID não altera o código.

### Filtro APRS-IS

O campo de string manual continua disponível. A v1.1 também oferece um **editor gráfico** para ajudar a compor:

- filtro radial;
- prefixos de indicativo;
- indicativos exatos;
- tipos de pacote.

O filtro padrão continua sendo `r/2000` em novas instalações.

Se o campo ficar vazio ao salvar a configuração APRS, o programa pede confirmação e informa que, dependendo do servidor e da porta, a conexão poderá receber um volume muito maior de tráfego.

### Tema e idioma

- Tema **Escuro** - padrão.
- Tema **Claro**.
- **Português** - idioma padrão.
- **English**.

## Dados persistentes

### Windows
`%LOCALAPPDATA%\PT2VHF APRS Client\data\pt2vhf_aprs.db`

### Linux
`~/.local/share/PT2VHF-APRS-Client/data/pt2vhf_aprs.db`

Se `XDG_DATA_HOME` estiver definido, ele é respeitado.

### macOS
`~/Library/Application Support/PT2VHF APRS Client/data/pt2vhf_aprs.db`

A atualização do executável/aplicativo não deve apagar o banco local.

## Instalação

- Linux: [docs/INSTALL_LINUX.md](docs/INSTALL_LINUX.md)
- macOS: [docs/INSTALL_MACOS.md](docs/INSTALL_MACOS.md)
- Windows: use o instalador da Release.

## Build automático

O workflow `.github/workflows/build-windows.yml` executa:

1. validação de sintaxe Python/JavaScript;
2. testes automatizados;
3. build Windows x64;
4. build Linux x86_64/amd64;
5. build macOS Apple Silicon e Intel;
6. geração de SBOM e inventário de licenças;
7. geração automática do manual PDF;
8. geração das notas da Release a partir do changelog;
9. publicação dos artefatos na mesma Release.

## Build manual no Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\windows\build_windows.ps1
```

## Desenvolvimento

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Segurança

- A interface local escuta apenas em `127.0.0.1` por padrão.
- Não exponha a porta 8080 diretamente à Internet.
- O JSON exportado pode conter o passcode APRS-IS em texto legível.
- Os builds Windows podem permanecer sem assinatura Authenticode durante o processo de integração de assinatura.
- Os builds macOS podem permanecer sem Developer ID/notarização; siga `docs/INSTALL_MACOS.md` e não desative globalmente o Gatekeeper.

Consulte:
- [PRIVACY.md](PRIVACY.md)
- [SECURITY.md](SECURITY.md)
- [CODE_SIGNING_POLICY.md](CODE_SIGNING_POLICY.md)
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

## Créditos técnicos

- APRS-IS: https://www.aprs-is.net/
- aprslib: https://pypi.org/project/aprslib/
- Leaflet: https://leafletjs.com/
- OpenStreetMap: https://www.openstreetmap.org/
- pywebview: https://pywebview.flowrl.com/
- PyInstaller: https://pyinstaller.org/
- Inno Setup: https://jrsoftware.org/isinfo.php
- ReportLab: https://www.reportlab.com/

## Licença

O código-fonte autoral do **PT2VHF APRS Client** é distribuído sob a [MIT License](LICENSE). Dependências de terceiros mantêm suas próprias licenças.

**Projeto por Alex, PT2VHF.**
