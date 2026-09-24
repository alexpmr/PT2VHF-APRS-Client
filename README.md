# PT2VHF APRS Client - v1.1

Cliente APRS-IS multiplataforma para **Windows, Linux e macOS**, com mapa, mensagens, estações, tracklogs, topologia observada, Log TNC2 e banco SQLite local.

A v1.1 adota a nova identidade visual **PT2VHF / APRS / CLIENT**, amplia a configuração da estação, adiciona editor gráfico de filtro APRS-IS, localização atual, entrada de coordenadas em decimal ou DMS, interface Português/English e inicia a distribuição para macOS.

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
- `PT2VHF_APRS_Client_Manual_vX.Y.pdf` - manual completo gerado automaticamente a partir de `VERSION` e `CHANGELOG.md`.

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

## Configuração v1.1

A tela é dividida em:

1. **APRS / Estação** - indicativo, SSID, passcode, posição, ícone, servidor, porta, filtro e beacon.
2. **Aplicativo** - mapa, cores, topologia, tema, idioma, fontes, comportamento e backup.

### Coordenadas

Latitude e longitude podem ser informadas em:

- decimal;
- graus/minutos/segundos (DMS).

O botão **Usar minha localização atual** solicita permissão de geolocalização e preenche latitude/longitude quando o ambiente fornece esses dados. A altitude só é preenchida quando a plataforma a disponibiliza; caso contrário, deve ser informada manualmente.

Ao tentar conectar sem Indicativo, Latitude, Longitude ou Altitude, o programa direciona o usuário para **Configuração > APRS / Estação** e destaca o primeiro campo ausente.

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
