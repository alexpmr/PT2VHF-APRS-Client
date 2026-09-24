# Changelog

## v1.1 - 2026-09-24

- Nova identidade visual **PT2VHF / APRS / CLIENT**, com logotipo vetorial mais nítido e maior no cabeçalho da aplicação.
- A tela **Configuração** passa a separar claramente **APRS / Estação** das preferências do **Aplicativo**.
- Ao tentar conectar sem Indicativo, Latitude, Longitude ou Altitude, o cliente abre a configuração APRS e destaca o primeiro campo obrigatório ausente.
- Coordenadas podem ser informadas em **decimal** ou **graus/minutos/segundos (DMS)**, com conversão automática entre os formatos.
- Novo botão **Usar minha localização atual**, usando a geolocalização disponibilizada pelo navegador/WebView/SO e mostrando a precisão quando disponível.
- A altitude só é preenchida automaticamente quando a plataforma fornece esse dado; caso contrário, permanece como preenchimento manual.
- Mantido o filtro APRS-IS em string para usuários avançados e adicionado **editor gráfico de filtro**, com composição assistida de filtro radial, prefixos, indicativos exatos e tipos de pacote.
- Ao salvar com o filtro APRS-IS vazio, o cliente exibe aviso explícito sobre o possível aumento de tráfego e exige confirmação para continuar.
- Tema **Escuro/Claro** com aplicação imediata.
- Novo chaveamento de idioma **Português/English**, com Português como padrão.
- Mantidas as preferências configuráveis de mapa, tracklogs, topologia observada, fontes e avisos de mensagem.
- Primeira distribuição para **macOS**, com builds separados para **Apple Silicon (arm64)** e **Intel (x86_64)** em imagens DMG.
- Dados no macOS passam a usar ~/Library/Application Support/PT2VHF APRS Client/data/pt2vhf_aprs.db.
- Adicionado guia de instalação específico para macOS, incluindo orientações sobre Gatekeeper para builds ainda não notarizados.
- Novo **manual PDF versionado**, gerado automaticamente a partir de VERSION, CHANGELOG.md e documentação do projeto e publicado em cada Release.
- Notas de Release passam a ser geradas automaticamente a partir do changelog da versão.
- Workflow de release passa a produzir artefatos Windows, Linux, macOS e o manual PDF na mesma versão.

## v1.0 — 2026-09-24

- Nova política de versionamento: a linha oficial passa de `0.3.x` para **v1.0**, seguindo depois v1.1, v1.2, v1.3 etc.
- Aba **Mensagens** passa ao fluxo de chat por padrão: mensagens antigas em cima e as mais novas na parte inferior.
- A atualização automática acompanha o fim da conversa somente quando o usuário já está próximo das mensagens mais recentes.
- Nova opção **Agrupar por remetente**, persistida localmente, com lista de conversas, última mensagem, horário e contagem de mensagens não lidas.
- Boletins e telemetria não são misturados nas conversas individuais agrupadas; permanecem acessíveis na lista cronológica conforme os filtros.
- Indicativos nas colunas **De** e **Para** passam a ser clicáveis e preenchem o destinatário para resposta.
- Ao clicar no próprio indicativo, o cliente tenta selecionar automaticamente o outro participante da mensagem.
- Quando uma mensagem chega com a aba **Mensagens** aberta, o alerta passa a ser compacto e não bloqueante.
- O alerta compacto pode ser fechado manualmente e fecha automaticamente após o período configurado, de 1 a 60 segundos.
- Em **Configuração → Mapa**, passam a ser configuráveis a cor dos enlaces RF, a cor dos enlaces via IGate e a espessura da topologia observada.
- Adicionado botão **Restaurar topologia padrão**.
- Nova opção **Abrir também no navegador ao iniciar**, desligada por padrão; a janela integrada continua sendo o comportamento principal no Windows.
- Primeira distribuição oficial **Linux x86_64/amd64**, com pacote portátil `.tar.gz` e pacote `.deb`.
- No Linux, o banco passa a seguir XDG e fica por padrão em `~/.local/share/PT2VHF-APRS-Client/data/pt2vhf_aprs.db`.
- O Linux tenta uma janela WebView compatível e utiliza o navegador local como fallback quando o backend gráfico não está disponível.
- Workflow unificado gera Windows e Linux, com testes, SBOM, inventário de licenças e publicação na mesma Release.
- Banco SQLite existente é migrado automaticamente com as novas preferências, preservando os dados anteriores.
- Build de release validado no GitHub Actions para Windows x64 e Linux x86_64/amd64.

## v0.3.2 — 2026-09-24

- Ao clicar no **X** da janela principal, o PT2VHF APRS Client passa a solicitar confirmação antes de sair.
- A confirmação usa a mensagem **“Deseja realmente sair do PT2VHF APRS Client?”**, com **Não** como opção padrão.
- Escolher **Não** cancela o fechamento e mantém o cliente funcionando.
- Escolher **Sim** desconecta do APRS-IS, encerra a janela WebView2, remove o ícone da bandeja e finaliza o processo.
- O cliente deixa de permanecer em segundo plano junto ao relógio após o fechamento confirmado da janela.
- A opção **Sair** na bandeja continua encerrando diretamente a aplicação.
- Banco SQLite e dados existentes permanecem compatíveis com a v0.3.1.
- Esta versão continua sem assinatura Authenticode enquanto o projeto aguarda a ativação do SignPath Foundation.

## v0.3.1 — 2026-09-24

- Removida completamente a barra flutuante superior do **Mapa**.
- O cabeçalho principal deixa de exibir “Cliente APRS-IS com banco local SQLite”.
- O cabeçalho passa a mostrar dinamicamente **Estações recebidas** e **Pacotes APRS-IS**.
- As abas **Mensagens** e **Estações** passam a exibir seus respectivos totais.
- **Limpar mensagens** permanece concentrado na aba Mensagens.
- **Limpar estações** e **Limpar tracklogs** ficam concentrados na aba Estações.
- Adicionada **Topologia observada APRS** no mapa, ativável por controle próprio.
- A topologia registra relações observadas entre estação, digipeater e IGate quando há evidência no path APRS e posição conhecida para os dois nós.
- São reconhecidos digipeaters efetivamente usados (marcados com `*`) e entradas de IGate observadas via `qAR`/`qAO`.
- Filtros de período da topologia: **1 h, 6 h, 24 h e 7 dias**.
- Clicar em um enlace mostra origem, destino, tipo, quantidade de pacotes, primeira e última observação.
- O campo de mensagem individual deixa de ter o limite curto de 63 caracteres.
- **Enter envia** a mensagem; **Shift+Enter** insere nova linha.
- Mensagens longas são divididas automaticamente em partes APRS numeradas, respeitando o limite de cada pacote.
- Cada parte enviada recebe ID APRS próprio e acompanha ACK/REJ individualmente.
- Quando uma parte recebe **ACK**, sua linha inteira fica verde na tela de Mensagens e o status aparece como **Lido**.
- O contador do campo informa o tamanho do texto e, quando necessário, a quantidade estimada de partes APRS.
- Instalador e Portable EXE passam a incluir a versão no próprio nome, por exemplo:
  - `PT2VHF_APRS_Client_Setup_x64_v0.3.1.exe`
  - `PT2VHF_APRS_Client_Portable_x64_v0.3.1.exe`
- Banco SQLite e dados existentes permanecem compatíveis com a v0.3.0.
- Esta versão continua sem assinatura Authenticode enquanto o projeto aguarda a ativação do SignPath Foundation.

## v0.3.0 — 2026-09-24

- A interface principal passa a abrir dentro de uma **janela própria do PT2VHF APRS Client**, sem depender de uma aba do navegador durante o uso normal.
- A janela integrada usa **Microsoft Edge WebView2** por meio do pywebview, preservando a interface HTML/CSS/JavaScript existente.
- O backend Flask/Waitress continua restrito a `127.0.0.1`, mantendo compatibilidade com o banco SQLite e as APIs locais já existentes.
- Janela inicial configurada para aproximadamente **1400 × 850**, com tamanho mínimo **1100 × 700**.
- Fechar a janela pelo **X** passa a ocultá-la na bandeja do Windows; a opção **Sair** na bandeja encerra efetivamente o aplicativo.
- Ao iniciar uma segunda instância, o cliente tenta restaurar e trazer a janela existente para frente em vez de abrir outra interface.
- Links externos, como GitHub, WhatsApp e e-mail, são encaminhados para o navegador padrão do Windows.
- Adicionado o modo de diagnóstico `--browser`, que força a interface a abrir no navegador.
- Se o WebView2 Runtime estiver indisponível ou falhar, o aplicativo informa o problema e utiliza o navegador como fallback.
- Instalador e Portable EXE passam a incluir as dependências necessárias do pywebview/WebView2.
- Banco local, configurações, mensagens, estações, tracklogs e Log APRS-IS permanecem compatíveis com a v0.2.9.
- Esta versão continua sem assinatura Authenticode enquanto o projeto aguarda a ativação do SignPath Foundation.

## v0.2.9 — 2026-09-24

- **Log, Mensagens e Estações** passam a seguir o mesmo padrão de navegação: registros mais recentes no topo e históricos mais antigos abaixo.
- No **Log**, os pacotes APRS-IS mais recentes agora aparecem no topo; rolar para baixo mostra os anteriores.
- Em **Estações**, a ordenação padrão continua pela última recepção em ordem decrescente, e a rolagem é preservada durante atualizações automáticas.
- Se o usuário estiver consultando registros antigos, as atualizações não forçam a tela de volta ao topo.
- Na aba **Mensagens**, adicionada a opção **Ocultar telemetria**, ligada por padrão.
- O filtro reconhece mensagens APRS de telemetria nos formatos `PARM.`, `UNIT.`, `EQNS.`, `BITS.` e relatórios `T#nnn`.
- A telemetria continua armazenada no histórico; o controle apenas esconde ou mostra esses registros.
- A preferência é mantida localmente para as próximas aberturas do aplicativo.
- No **Mapa**, os ícones APRS das estações passam a ser exibidos sem o quadrado de fundo: fundo, borda e sombra dos marcadores ficam transparentes, deixando visível apenas o símbolo APRS.
- Na tela **Mapa**, adicionados os botões **Apagar tracklogs** e **Apagar estações**.
- **Apagar tracklogs** remove somente os pontos de trilha armazenados e mantém as estações no mapa.
- **Apagar estações** remove as estações e seus tracklogs, reutilizando a mesma limpeza disponível na aba Estações.
- As duas ações exigem confirmação antes da exclusão.
- Em **Configuração → Aparência**, adicionada seleção entre **Tema escuro** e **Tema claro**.
- O tema escuro continua sendo o padrão para novas instalações.
- O novo **tema claro** adapta cabeçalho, abas, formulários, tabelas, mensagens, Ajuda, Log, modais e controles do mapa.
- A troca de tema é visualizada imediatamente e a escolha fica persistida no banco local após salvar a configuração.
- Na aba **Mensagens**, por padrão as mensagens mais novas aparecem no topo; as mais antigas ficam abaixo e são consultadas rolando a lista para baixo.
- Ao abrir a aba Mensagens, a visualização começa no topo. Durante atualizações automáticas, se o usuário estiver consultando mensagens antigas, a posição da rolagem é preservada.
- Em novas instalações, o campo **Indicativo** passa a iniciar vazio; nenhum indicativo pessoal é preenchido automaticamente.
- **Indicativo, latitude, longitude e altitude** passam a ser campos obrigatórios na configuração da estação.
- A interface destaca visualmente os campos obrigatórios e impede salvar enquanto estiverem vazios.
- O backend também valida os campos obrigatórios, evitando conexão APRS-IS com configuração incompleta.
- Se **Conectar ao iniciar** estiver habilitado e a configuração estiver incompleta, o aplicativo abre normalmente e permanece desconectado, informando o motivo.
- O filtro APRS-IS padrão para novas instalações passa a ser **`r/2000`**, usando a latitude/longitude configuradas como centro.
- Configurações já existentes são preservadas durante a atualização; a aplicação não substitui automaticamente indicativo, posição ou filtro previamente salvos.

## v0.2.8 — 2026-09-23

- Release de manutenção baseada na v0.2.7, sem alterações no formato do banco local.
- Mantidos os ajustes da tela de Mensagens, incluindo **Lido** em verde, lista com rolagem própria e área de envio adaptada à altura da janela.
- Distribuição mantida apenas em **Instalador EXE** e **Portable EXE**.
- As descrições dos downloads permanecem em português na página da Release.
- Esta versão continua **sem assinatura Authenticode** enquanto o projeto aguarda a ativação do SignPath Foundation; portanto, o Smart App Control do Windows ainda pode bloquear os executáveis.

## v0.2.7 — 2026-09-23

- Política de privacidade atualizada para documentar a consulta automática ao GitHub usada pelo verificador de novas versões; nenhum indicativo, posição, mensagem ou passcode é enviado nessa consulta.
- Na aba **Mensagens**, o status `ACK` passa a ser exibido como **Lido** em verde, mantendo `ACK` apenas internamente no protocolo APRS.
- Ajustada a aba **Mensagens** para caber integralmente na altura disponível da janela.
- A lista de mensagens passa a usar automaticamente o espaço restante e possui **barra de rolagem própria**.
- A área de composição fica presa ao rodapé da aba e se adapta à altura disponível.
- O botão **Enviar** foi reposicionado para permanecer sempre visível em telas largas.
- Em janelas de menor altura, o compositor reduz automaticamente sua altura sem empurrar controles para fora da tela.
- O arquivo **Portable ZIP** deixa de ser gerado e publicado.
- As próximas versões passam a oferecer apenas **Instalador EXE** e **Portable EXE** como opções para usuários Windows.
- A página de cada Release passa a apresentar em **português** a descrição dos arquivos disponíveis.
- O instalador é identificado como a opção recomendada para a maioria dos usuários.
- O Portable EXE é descrito como versão em arquivo único, sem necessidade de instalação.
- SBOM e inventário de licenças continuam disponíveis como arquivos técnicos da Release.

## v0.2.6 — 2026-09-23

- Botão **Limpar mensagens** na aba Mensagens, com confirmação antes de apagar todo o histórico local de mensagens e boletins.
- Botão **Limpar estações** na aba Estações, removendo estações e tracklogs locais com confirmação.
- A limpeza de mensagens não afeta estações; a limpeza de estações não afeta mensagens, configurações ou Log APRS-IS.
- O mapa remove imediatamente marcadores e tracklogs apagados, sem exigir reinício.
- Área de composição de mensagem aumentada para aproximadamente três vezes a altura anterior.
- Campo de mensagem alterado para editor multilinha com contador de caracteres.
- **Enter** cria nova linha durante a edição e **Ctrl+Enter** envia a mensagem.
- Mantidos todos os recursos da v0.2.5, incluindo Ajuda integrada, Portable EXE, brilho do mapa, aviso sonoro, atualização automática de versão e envio de mensagens a partir do mapa.
- Telemetria/estatísticas anônimas **não fazem parte desta versão** e permanecem para desenvolvimento posterior.
- Esta release permanece **não assinada** enquanto o projeto aguarda aprovação do SignPath Foundation.

## v0.2.5 — 2026-09-23

- Nova aba **Ajuda** com guia de primeiros passos, configuração da estação, APRS-IS, mapa, mensagens, boletins, estações, Log, atualizações, banco/backup e diagnóstico rápido.
- A Ajuda inclui contato para dúvidas, dificuldades e sugestões: Alex — WhatsApp 61 98402-3634 — alexpmr@gmail.com.
- Novo artefato `PT2VHF_APRS_Client_Portable_x64.exe`: versão portátil em executável único, sem necessidade de descompactar o ZIP.
- O Portable EXE continua usando o banco SQLite em `%LOCALAPPDATA%\PT2VHF APRS Client\data`, compartilhando configurações e histórico com a instalação normal.
- O instalador agora encerra automaticamente a versão anterior do PT2VHF APRS Client antes de substituir os arquivos, evitando falhas de atualização por arquivos em uso.
- O instalador também tenta interromper um eventual serviço Windows `PT2VHF_APRS_Client`, preparando o mecanismo para uma futura execução como serviço.
- Controle de **Brilho do mapa** em Configuração → Mapa, de 30% a 150%, com pré-visualização imediata.
- Opção de **sinal sonoro** ao receber nova mensagem individual destinada ao `CALL-SSID` configurado.
- O sinal sonoro é gerado nativamente pelo Windows quando chega uma mensagem individual para a estação configurada, funcionando mesmo com a interface no navegador minimizada.
- Botão **Enviar mensagem** no popup das estações do mapa; abre a aba Mensagens com o indicativo de destino já preenchido e o cursor no campo de texto.
- Indicador de versão no cabeçalho da aplicação.
- Mostra **Última versão** quando a instalação corresponde à release mais recente publicada.
- Mostra **Nova versão vX.Y.Z** quando houver uma release mais nova no GitHub.
- O aviso de nova versão abre diretamente a página da Release.
- Builds de desenvolvimento mais novos que a última release são identificados como **Build vX.Y.Z**.
- Falhas de consulta não afetam o APRS e são mostradas como **Versão não verificada**.
- Consulta feita pelo backend local com cache de 15 minutos; a interface revalida periodicamente.

## v0.2.4 — 2026-09-23

- Nova seção **Aparência** em Configuração.
- Ajuste independente da **família da fonte** da aba Mensagens.
- Ajuste independente do **tamanho da fonte** da aba Mensagens, de 10 a 20 px.
- Ajuste independente da **família da fonte** da aba Estações.
- Ajuste independente do **tamanho da fonte** da aba Estações, de 10 a 20 px.
- Fontes disponíveis: Sistema, Segoe UI, Arial, Verdana, Tahoma e Consolas.
- Alterações de aparência são visualizadas imediatamente e persistidas no SQLite após salvar.
- Configuração incluída na exportação/importação JSON.
- Mantidas todas as melhorias da v0.2.3, incluindo boletins APRS, Minhas mensagens, popup de mensagens, mapas alternativos, tracklogs configuráveis, passcode automático e nova identidade visual.
- Esta release permanece **não assinada** enquanto o projeto aguarda aprovação do SignPath Foundation.


## v0.2.3 — 2026-09-23

- Suporte nativo a **boletim APRS geral** (`BLN0`–`BLN9`) sem ACK.
- Suporte a **boletim APRS de grupo**, com identificador e grupo de até 5 caracteres.
- Histórico de mensagens distingue mensagem individual, boletim e boletim de grupo.
- Botão **Minhas mensagens** mostra apenas mensagens individuais de ou para o `CALL-SSID` configurado.
- Popup para nova mensagem individual destinada à estação configurada, com remetente, horário, texto e botão **Responder**.
- Aba **Estações** sem a coluna Nome; Indicativo passa a ser a identificação principal.
- Clique em uma estação abre a aba MAPA, centraliza a posição e abre o popup correspondente.
- **Última recepção** permanece em uma única linha com data e hora.
- **Distância** mantém valor e `km` na mesma linha.
- Nova seção **Mapa** nas configurações.
- Seleção de mapa: OpenStreetMap, OpenTopoMap e Esri World Imagery.
- Configuração de cor e espessura dos tracklogs, persistida no SQLite.
- Passcode APRS-IS movido para junto do Indicativo e exibido em texto normal.
- Cálculo automático do passcode APRS-IS enquanto o indicativo é digitado.
- Nova identidade visual quadrada do PT2VHF APRS Client no cabeçalho, favicon, bandeja, executável e instalador.
- Geração automática do ícone Windows durante o build.
- Logo validada novamente no pipeline após correção do ativo PNG usado para gerar o ícone Windows.
- Mantidos SBOM CycloneDX, inventário de licenças e preparação para futura assinatura SignPath.
- Esta release ainda é **não assinada** enquanto o projeto aguarda aprovação do SignPath Foundation.


## v0.2.2 — 2026-09-23

Build Windows de teste enquanto o projeto aguarda aprovação do SignPath Foundation.

- Código autoral formalizado sob licença MIT.
- Política de assinatura de código publicada.
- Política de privacidade e política de segurança adicionadas.
- Avisos e licenças de componentes de terceiros documentados.
- `CODEOWNERS` configurado para o mantenedor do projeto.
- Instalador passa a exibir a licença MIT e o aviso de privacidade.
- Geração automática de SBOM CycloneDX no build Windows.
- Inventário automático das licenças das dependências.
- SBOM e inventário de licenças incluídos nos artefatos do GitHub Actions.
- Página de Release passa a informar explicitamente o status de assinatura.
- Documentação de onboarding e candidatura ao SignPath Foundation adicionada.
- Esta versão permanece **não assinada** enquanto a aprovação do SignPath estiver pendente.


## v0.2.1 — 2026-09-23

- Correção dos tiles do mapa exibidos fora de posição/“embaralhados”.
- CSS do Leaflet empacotado localmente com a aplicação para evitar falhas do CDN.
- Proteção CSS adicional para o posicionamento absoluto dos tiles.
- Botão **Minha localização** no mapa, usando a geolocalização do navegador.
- Exibição de marcador e raio de precisão da localização do navegador.
- Versão exibida no título da aplicação e na aba do navegador.
- Aba **Log** com todo o tráfego APRS-IS bruto em RX/TX.
- Filtro textual, filtro por direção, quantidade de linhas e auto-rolagem no Log.
- Histórico do Log persistido no SQLite, com retenção dos 100.000 registros mais recentes.
- Passcode APRS-IS mascarado antes de registrar a linha de login no Log.
- Reconexão automática ao alterar parâmetros de conexão/filtro enquanto conectado.
- Contadores de pacotes recebidos e filtro APRS-IS ativo exibidos no mapa para diagnóstico.

## v0.2.0 — 2026-09-23

Versão Windows-first.

- Aplicativo Windows sem console, com servidor local Waitress.
- Ícone na bandeja com abrir, conectar, desconectar, abrir pasta de dados e sair.
- Banco SQLite movido para `%LOCALAPPDATA%\PT2VHF APRS Client\data` no Windows.
- Empacotamento PyInstaller em modo onedir.
- Instalador Inno Setup x64 e ZIP portátil.
- Workflow GitHub Actions para gerar artefatos e anexá-los automaticamente às Releases criadas por tags `v*`.
- Dados locais preservados durante atualização/desinstalação.

## v0.1.0 — 2026-09-23

Primeira versão funcional do PT2VHF APRS Client.

- Cliente TCP APRS-IS com conexão, desconexão e reconexão automática.
- SQLite local para configuração, mapa, estações, trilhas, mensagens e pacotes brutos.
- Mapa Leaflet/OpenStreetMap com símbolos APRS e tracklog.
- Mensagens APRS com autocomplete, filtro, ordenação, ACK/REJ e envio.
- Lista de estações com distância, velocidade, curso, altitude e informação.
- Configuração completa, seletor de símbolo, beacon e importação/exportação JSON.
