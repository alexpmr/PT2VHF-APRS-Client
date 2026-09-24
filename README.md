# PT2VHF APRS Client — v1.0

Cliente APRS-IS para Windows e Linux, desenvolvido em Python, com banco SQLite, mapa, mensagens, histórico de estações e topologia observada. No Windows, a interface usa Microsoft Edge WebView2; no Linux, tenta uma janela WebView compatível e usa o navegador local como fallback.

## Windows — distribuição principal

A distribuição Windows continua sendo a opção mais integrada. A partir da **v1.0**, o projeto também publica artefatos oficiais para **Linux x86_64/amd64**. O usuário final não precisa instalar Python em nenhum dos dois sistemas.

Os artefatos previstos para cada versão são:

- `PT2VHF_APRS_Client_Setup_x64_vX.Y.Z.exe` — instalador recomendado.
- `PT2VHF_APRS_Client_Portable_x64_vX.Y.Z.exe` — versão portátil em executável único.

O instalador utiliza **PyInstaller + Inno Setup**. A aplicação executa sem janela de console, inicia um servidor HTTP apenas em `127.0.0.1` e exibe a interface dentro de uma janela própria usando **Microsoft Edge WebView2**. O navegador padrão não é aberto durante o uso normal. Enquanto estiver em execução, o aplicativo também oferece controles pela bandeja do Windows.

### Janela integrada

A partir da v0.3.0, a interface deixa de depender de uma aba do navegador e passa a rodar dentro da própria janela do PT2VHF APRS Client.

- Janela inicial: aproximadamente **1400 × 850**.
- Tamanho mínimo: **1100 × 700**.
- Desde a **v0.3.2**, clicar no **X** pergunta **“Deseja realmente sair do PT2VHF APRS Client?”**.
- **Não** cancela o fechamento; **Sim** desconecta do APRS-IS, encerra a janela, remove o ícone da bandeja e finaliza o processo.
- O menu da bandeja continua permitindo restaurar a janela, conectar/desconectar do APRS-IS, abrir a pasta de dados ou sair.
- Links externos, como GitHub, WhatsApp e e-mail, são enviados ao navegador padrão do Windows.
- O modo de diagnóstico `--browser` força a interface a abrir no navegador.
- Se o Microsoft Edge WebView2 Runtime estiver indisponível, o aplicativo informa o problema e usa o navegador como fallback.

### Dados do usuário

O programa é instalado em `Program Files`, mas o banco e os dados persistentes ficam em:

```text
%LOCALAPPDATA%\PT2VHF APRS Client\data\pt2vhf_aprs.db
```

Assim, uma atualização ou desinstalação do executável não precisa apagar configuração, mensagens, estações e tracklogs.

A versão portátil em `.EXE` usa **o mesmo banco local** em `%LOCALAPPDATA%`, portanto compartilha dados e configurações com a versão instalada. Ela é portátil quanto ao executável, não quanto aos dados persistentes.

### Ícone na bandeja

O aplicativo oferece:

- Abrir PT2VHF APRS Client.
- Conectar ao APRS-IS.
- Desconectar do APRS-IS.
- Abrir a pasta de dados.
- Sair.

## Recursos

- Contadores de estações e pacotes APRS-IS no cabeçalho principal.
- O mapa não possui mais a barra flutuante de diagnóstico/manutenção.

### MAPA

- OpenStreetMap/Leaflet.
- Estações exibidas conforme são recebidas do APRS-IS.
- Símbolos APRS conforme `symbol_table` + `symbol`.
- Tracklog automático de estações móveis.
- **Topologia observada APRS** opcional, com linhas entre estações/digipeaters/IGates quando o path recebido fornece evidência e ambos os nós possuem posição conhecida.
- Filtros da topologia por 1 h, 6 h, 24 h e 7 dias.
- Cor dos enlaces RF, cor dos enlaces via IGate e espessura das linhas configuráveis.
- Botão para restaurar o visual da topologia aos valores padrão.
- Popup com indicativo, posição, velocidade, curso, altitude, comentário/informação e path.
- Centro e zoom persistidos no SQLite.
- Botão para centralizar o mapa na localização disponibilizada pelo mecanismo WebView2/navegador.
- CSS do Leaflet empacotado localmente para maior estabilidade dos tiles.

### Mensagens

- De, Para, Tipo, Mensagem, Hora e Status.
- Fluxo padrão em estilo chat: mensagens antigas em cima e as mais novas na parte inferior.
- A rolagem acompanha novas mensagens somente quando o usuário já está no fim da conversa.
- Opção **Agrupar por remetente**, persistida localmente, com lista de conversas, última mensagem, horário e não lidas.
- Clique nos indicativos **De** ou **Para** para preencher o destinatário e responder; ao clicar no próprio indicativo, o outro participante é usado quando possível.
- Ordenação pelas colunas na visualização cronológica.
- Filtro parcial por indicativo de origem.
- Autocomplete do destino usando indicativos conhecidos, sem impedir indicativos novos.
- IDs de mensagem APRS, ACK/REJ e ACK automático.
- Boletins APRS gerais e de grupo.
- Botão **Minhas mensagens** para mostrar apenas mensagens de/para a estação configurada.
- Popup de alerta para novas mensagens individuais destinadas à estação configurada.
- Quando a aba Mensagens já está aberta, o alerta é compacto, não bloqueante, pode ser fechado manualmente e fecha automaticamente após o número de segundos definido em Configuração.
- Botão **Limpar mensagens** para apagar todo o histórico local de mensagens e boletins, com confirmação.
- Compositor de mensagem ampliado, sem o antigo limite curto para mensagens individuais.
- **Enter envia**; **Shift+Enter** cria nova linha.
- Mensagens longas são divididas automaticamente em partes APRS numeradas, cada uma com ID e ACK próprios.
- Ao receber ACK, a linha correspondente fica verde e o status aparece como **Lido**.

### Estações

- Indicativo como identificação principal.
- Última recepção.
- Distância da estação local.
- Velocidade, curso, altitude e informação.
- Filtro parcial e ordenação por colunas.
- Clique na estação para centralizá-la no mapa.
- Botão **Limpar estações** para apagar todas as estações e tracklogs locais, com confirmação.

### Ajuda

- Guia rápido de configuração da estação e APRS-IS.
- Explicação de mapa, mensagens, boletins, estações, Log, atualizações e backup.
- Diagnóstico rápido para problemas comuns.
- Contatos de suporte e sugestões diretamente na aplicação.

### Log APRS-IS

- Monitor bruto do tráfego TNC2 recebido e transmitido.
- Direções **RX** e **TX** identificadas visualmente.
- Filtro de texto e filtro por direção.
- Auto-rolagem para acompanhar o tráfego em tempo real.
- Seleção de quantidade de linhas exibidas.
- Histórico persistido no SQLite com retenção dos 100.000 registros mais recentes.
- Passcode APRS-IS mascarado na linha de login antes de ser salvo/exibido.

### Configuração

- Indicativo, latitude, longitude e altitude são obrigatórios para concluir a configuração inicial.
- O campo Indicativo fica vazio em uma instalação nova; nenhum indicativo pessoal é preenchido automaticamente.
- Indicativo e SSID.
- Comentário, latitude, longitude e altitude.
- E-mail.
- Seletor de símbolo APRS.
- Beacon periódico.
- Servidor padrão `brazil.aprs2.net`.
- Porta padrão `14580`.
- Passcode APRS-IS.
- Filtro APRS-IS.
- `r/2000` é o filtro padrão para novas instalações e é expandido usando a posição configurada.
- Conectar ao iniciar.
- **Abrir também no navegador ao iniciar**, desligado por padrão; a janela integrada continua sendo aberta normalmente.
- Tipo de mapa, cor e espessura dos tracklogs.
- Cor RF, cor IGate e espessura da topologia observada, com restauração dos padrões.
- Tempo de exibição do aviso compacto de nova mensagem na aba Mensagens.
- Tema escuro como padrão e opção de tema claro.
- Fonte e tamanho independentes para Mensagens e Estações.
- Passcode APRS-IS visível junto ao indicativo, com cálculo automático.
- Importação/exportação JSON.


## Linux — v1.0

A v1.0 inicia a distribuição oficial para **Linux x86_64/amd64**.

Arquivos previstos na Release:

- `PT2VHF_APRS_Client_Linux_x86_64_v1.0.tar.gz` — pacote portátil genérico.
- `pt2vhf-aprs-client_1.0_amd64.deb` — Debian/Ubuntu e derivados.

Os dados do usuário ficam fora da pasta do programa:

```text
~/.local/share/PT2VHF-APRS-Client/data/pt2vhf_aprs.db
```

Se `XDG_DATA_HOME` estiver definido, ele será respeitado.

A execução normal tenta uma janela integrada. Se o ambiente Linux não oferecer um backend WebView compatível, a interface é aberta automaticamente no navegador em `http://127.0.0.1:8080`.

Instruções completas, atualização, desinstalação, autostart e diagnóstico:

- [Instalação no Linux](docs/INSTALL_LINUX.md)

## Build automático no GitHub

O workflow `.github/workflows/build-windows.yml` executa:

1. testes automatizados no Windows;
2. empacotamento PyInstaller `onedir` para gerar o instalador;
3. empacotamento PyInstaller `onefile` para o Portable EXE;
4. criação do instalador Inno Setup;
5. publicação dos artefatos Windows;
6. após sucesso do Windows, build Linux x86_64;
7. geração do pacote portátil `.tar.gz` e do pacote `.deb`;
8. geração de SBOM/inventário de licenças para os dois sistemas;
9. publicação automática de todos os arquivos na mesma Release.

## Build manual no Windows

Em PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\windows\build_windows.ps1
```

Os resultados são gravados em `dist-installer`.

## Desenvolvimento

Para executar o backend em modo de desenvolvimento no navegador:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Para testar a janela integrada no Windows:

```powershell
pip install -r requirements-windows.txt
python windows_app.py
```

O parâmetro `--browser` força o modo de diagnóstico pelo navegador.

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
- pywebview: https://pywebview.flowrl.com/
- Microsoft Edge WebView2: https://developer.microsoft.com/microsoft-edge/webview2/
- PyInstaller: https://pyinstaller.org/
- Inno Setup: https://jrsoftware.org/isinfo.php


## Licença

O código-fonte autoral do **PT2VHF APRS Client** é distribuído sob a [MIT License](LICENSE).

Os componentes de terceiros mantêm suas próprias licenças. Em particular, o build atual utiliza `aprslib` sob GNU GPL v2. Consulte [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) antes de redistribuir binários.

## Code signing policy

A política de assinatura está documentada em [CODE_SIGNING_POLICY.md](CODE_SIGNING_POLICY.md).

**Status atual:** as releases Windows ainda são não assinadas enquanto o projeto conclui o processo de onboarding para assinatura Open Source.

Após a aprovação e ativação do projeto, as releases assinadas usarão a atribuição exigida pelo programa:

> **Free code signing provided by SignPath.io, certificate by SignPath Foundation**

Papéis atuais do projeto:

- **Committer / reviewer:** [Alex Rodrigues (@alexpmr)](https://github.com/alexpmr)
- **Approver:** [Alex Rodrigues (@alexpmr)](https://github.com/alexpmr)

Política de privacidade: [PRIVACY.md](PRIVACY.md)

Consulte também o [plano de integração com SignPath](docs/SIGNPATH_SETUP.md).

## Privacidade e segurança

- [Política de privacidade](PRIVACY.md)
- [Política de segurança](SECURITY.md)
- [Avisos e licenças de terceiros](THIRD_PARTY_NOTICES.md)
