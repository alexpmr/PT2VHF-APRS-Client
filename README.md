# PT2VHF APRS Client — v0.2.1

Cliente APRS-IS para Windows, desenvolvido em Python, com interface web local, banco SQLite, mapa, mensagens e histórico de estações.

## Windows — distribuição principal

A partir da v0.2.0, o projeto é **Windows-first**. O usuário final não precisa instalar Python.

Os artefatos previstos para cada versão são:

- `PT2VHF_APRS_Client_Setup_x64.exe` — instalador recomendado.
- `PT2VHF_APRS_Client_Portable_x64.zip` — versão portátil.

O instalador utiliza **PyInstaller + Inno Setup**. A aplicação executa sem janela de console, inicia um servidor HTTP apenas em `127.0.0.1`, abre o navegador e permanece disponível pela bandeja do Windows.

### Dados do usuário

O programa é instalado em `Program Files`, mas o banco e os dados persistentes ficam em:

```text
%LOCALAPPDATA%\PT2VHF APRS Client\data\pt2vhf_aprs.db
```

Assim, uma atualização ou desinstalação do executável não precisa apagar configuração, mensagens, estações e tracklogs.

### Ícone na bandeja

O aplicativo oferece:

- Abrir PT2VHF APRS Client.
- Conectar ao APRS-IS.
- Desconectar do APRS-IS.
- Abrir a pasta de dados.
- Sair.

## Recursos

### MAPA

- OpenStreetMap/Leaflet.
- Estações exibidas conforme são recebidas do APRS-IS.
- Símbolos APRS conforme `symbol_table` + `symbol`.
- Tracklog automático de estações móveis.
- Popup com indicativo, posição, velocidade, curso, altitude, comentário/informação e path.
- Centro e zoom persistidos no SQLite.
- Botão para centralizar o mapa na localização indicada pelo navegador.
- CSS do Leaflet empacotado localmente para maior estabilidade dos tiles.

### Mensagens

- De, Para, Mensagem, Hora e Status.
- Ordenação pelas colunas.
- Filtro parcial por indicativo de origem.
- Autocomplete do destino usando indicativos conhecidos, sem impedir indicativos novos.
- IDs de mensagem APRS, ACK/REJ e ACK automático.

### Estações

- Nome/indicativo.
- Última recepção.
- Distância da estação local.
- Velocidade, curso, altitude e informação.
- Filtro parcial e ordenação por colunas.

### Log APRS-IS

- Monitor bruto do tráfego TNC2 recebido e transmitido.
- Direções **RX** e **TX** identificadas visualmente.
- Filtro de texto e filtro por direção.
- Auto-rolagem para acompanhar o tráfego em tempo real.
- Seleção de quantidade de linhas exibidas.
- Histórico persistido no SQLite com retenção dos 100.000 registros mais recentes.
- Passcode APRS-IS mascarado na linha de login antes de ser salvo/exibido.

### Configuração

- Indicativo e SSID.
- Comentário, latitude, longitude e altitude.
- E-mail.
- Seletor de símbolo APRS.
- Beacon periódico.
- Servidor padrão `brazil.aprs2.net`.
- Porta padrão `14580`.
- Passcode APRS-IS.
- Filtro APRS-IS.
- `r/500` é expandido usando a posição configurada.
- Conectar ao iniciar.
- Importação/exportação JSON.

## Build automático no GitHub

O workflow `.github/workflows/build-windows.yml` executa:

1. testes automatizados;
2. empacotamento PyInstaller `onedir`;
3. criação do instalador Inno Setup;
4. criação do ZIP portátil;
5. upload dos dois artefatos;
6. publicação automática dos arquivos em uma Release quando o build é disparado por uma tag `v*`.

## Build manual no Windows

Em PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\windows\build_windows.ps1
```

Os resultados são gravados em `dist-installer`.

## Desenvolvimento

Para executar pelo código-fonte:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Abra `http://127.0.0.1:8080`.

## Segurança

- A interface escuta apenas em localhost por padrão.
- Não exponha a porta 8080 diretamente à Internet.
- O JSON exportado pode conter o passcode APRS-IS; trate-o como arquivo sensível.
- O instalador atual não possui assinatura Authenticode. Portanto, o Windows pode exibir aviso de **editor desconhecido** ou aplicar políticas de Application Control. Consulte [CODE_SIGNING_POLICY.md](CODE_SIGNING_POLICY.md).

## Banco local

Tabelas principais:

- `config`
- `map_state`
- `stations`
- `tracks`
- `messages`
- `packets`
- `aprs_log`

## Créditos técnicos

- APRS-IS: https://www.aprs-is.net/
- aprslib: https://pypi.org/project/aprslib/
- Leaflet: https://leafletjs.com/
- OpenStreetMap: https://www.openstreetmap.org/
- PyInstaller: https://pyinstaller.org/
- Inno Setup: https://jrsoftware.org/isinfo.php


## Licença

O código-fonte autoral do **PT2VHF APRS Client** é distribuído sob a [MIT License](LICENSE).

Os componentes de terceiros mantêm suas próprias licenças. Em particular, o build atual utiliza `aprslib` sob GNU GPL v2. Consulte [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) antes de redistribuir binários.

## Code signing policy

A política de assinatura está documentada em [CODE_SIGNING_POLICY.md](CODE_SIGNING_POLICY.md).

**Status atual:** as releases Windows ainda são não assinadas enquanto o projeto conclui o processo de onboarding para assinatura Open Source. A integração planejada é SignPath.io / SignPath Foundation; ela só será ativada depois da aprovação externa e da configuração dos identificadores/segredos necessários.

Consulte também o [plano de integração com SignPath](docs/SIGNPATH_SETUP.md).

## Privacidade e segurança

- [Política de privacidade](PRIVACY.md)
- [Política de segurança](SECURITY.md)
- [Avisos e licenças de terceiros](THIRD_PARTY_NOTICES.md)
