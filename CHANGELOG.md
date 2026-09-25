# Changelog

## v1.6.12 - 2026-09-25

- Release de diagnóstico somente **Windows x64 Portable**, sem instalador e sem manual.
- Adicionado rastreamento de requests do servidor HTTP local com endpoint, thread, duração e quantidade de requests simultâneos.
- Adicionado watchdog interno que consulta o backend e gera **thread dump** quando houver falhas consecutivas, request acima de 8 s ou saturação das threads do Waitress.
- Operações SQLite lentas (>= 750 ms) e erros de banco passam a ser registradas no arquivo de diagnóstico.
- O arquivo persistente `diagnostics.log` fica na pasta de dados e também pode ser obtido por `/api/diagnostics/log`.
- O aviso de timeout passa a mostrar o endpoint que deixou de responder.


## v1.6.10 - 2026-09-25

- Release completa multiplataforma com **Windows x64 Setup + Portable**, **Linux x86_64 TAR.GZ + AppImage + DEB**, **macOS ARM64 + Intel DMG** e **Manual PDF**.
- Consolidada a correção do envio de mensagens usando **fila assíncrona no backend**, evitando que a interface fique presa ao envio pelo socket APRS-IS.
- Adicionada proteção contra cliques repetidos/deduplicação para impedir múltiplos envios da mesma mensagem em sequência.
- Ao encerrar, a aplicação cancela filas pendentes, encerra os serviços e executa manutenção leve do SQLite.
- Corrigido o pipeline do ícone Windows para usar a identidade visual estável e válida durante o empacotamento.
- Os patches acumulados da série 1.6 passam a ser aplicados também aos builds macOS e à captura usada no manual.
- A nova logo APRS oficial permanece no backlog até ser reintegrada com arquivo de imagem validado.


## v1.6.2 - 2026-09-25

- Adicionado **Replay da Rede** na parte inferior do Mapa, com linha do tempo arrastável, densidade de tráfego, seek por horário, intervalo personalizado, modo Ao vivo e velocidades de 0,25x a 20x.
- A animação continua usando apenas caminhos APRS observados e pode movimentar o mesmo pacote por vários enlaces simultaneamente.
- Som e destaque de atividade passam a ocorrer somente para estações realmente visíveis no enquadramento/zoom atual; o marcador recebe ondas concêntricas animadas.
- Adicionado indicador **RX/TX** na barra superior para sinalizar atividade de tráfego recebido e transmitido.
- A legenda do Mapa passa a acompanhar imediatamente as cores e espessuras definidas em Configuração.
- Corrigida a aplicação da **espessura da topologia** no Mapa.
- Os controles de replay/animação foram removidos da aba Análise e concentrados no Mapa; o antigo botão **Animar período** foi removido.
- O botão do popup da estação passa a se chamar **Ver logs**, abrindo a aba Log já filtrada pelo indicativo/SSID.
- O fluxo de Configuração passa a ter um único botão **Salvar configuração** no rodapé, confirmação visual de salvamento e aviso ao sair com alterações pendentes.
- O **auto-update foi desativado**: o cliente apenas detecta e informa novas versões; download e instalação são manuais pela página oficial da Release.
- A checagem de versão ganhou timeout, recuperação após falhas e deixou de manter erro em cache.
- Após uma atualização, o aplicativo mostra uma única vez um popup local com as principais novidades da versão.
- Esta Release foi gerada somente para **Windows x64** (instalador e portátil), sem nova documentação PDF, Linux ou macOS.

## v1.6.1 - 2026-09-24

- As três opções de atualização OTA passam a vir **ativadas por padrão em novas instalações**: verificar, baixar e instalar ao fechar. Preferências já salvas continuam preservadas em instalações existentes.
- Mensagens APRS longas deixam de receber marcadores visíveis como `[1/2]` e `[2/2]`; a divisão passa a respeitar limites de palavra sempre que possível e só corta uma palavra quando ela, sozinha, excede o limite técnico da parte.
- Criada a nova aba superior **Análise**, que recebe a análise da topologia antes localizada em Configuração.
- A aba Análise inclui seleção de período, métricas agregadas, ranking de digipeaters, ranking de IGates, enlaces que deixaram de aparecer, comparação histórica, **Atualizar análise** e **Animar período**.
- Em **Configuração → Mapa**, permanecem apenas as preferências visuais e de comportamento do mapa/topologia.
- O popup das estações no mapa passa a oferecer **Mostrar log** ao lado de **Enviar mensagem**; a ação abre a aba Log com o indicativo completo da estação aplicado ao filtro.
- Removido o bloco introdutório **Página única de configuração**, fazendo a tela começar diretamente pela primeira seção.
- Mantidas as correções da v1.6 para popup **Ler mensagem**, layout vertical de Latitude/Longitude/Altitude, filtros brasileiros, mensagens agrupadas, retry, Log ordenável e atualizador integrado.
- O período **Completo** passa a ser o padrão da Topologia observada, mantendo as janelas de 1 h, 6 h, 24 h e 7 dias.
- Adicionada legenda dinâmica no Mapa para tracklog, enlace RF, IGate/APRS-IS, replay temporal e pacotes em movimento.
- Adicionada animação de tráfego APRS em modos **Histórico** e **Ao vivo**, com Play/Pausa, início, avanço/recuo, controle de velocidade, timestamp e contadores.
- Pacotes com múltiplos enlaces observados podem animar os vários segmentos simultaneamente.
- Adicionado aviso de atividade: som curto e pulso vermelho no marcador da estação transmissora, com controles independentes em Configuração.
- Estações favoritas passam a usar **estrela amarela**, persistem no banco, ficam fixadas no topo da lista de Estações e são priorizadas nas conversas/sugestões de mensagem.
- Adicionado botão **Não lidas** em Mensagens, com estado lida/não lida persistido e suporte à visualização agrupada.
- A consulta automática por novas versões passa a ocorrer a cada **5 minutos**, com proteção contra verificações sobrepostas e cache alinhado à mesma cadência.
- README, manual, ajuda interna e guia Linux atualizados para a série v1.6.1.

## v1.6 - 2026-09-24

- Consolidado o backlog funcional acumulado até 24/09/2026 e retomada a geração completa para Windows, Linux, macOS e manual PDF.
- A tela **Configuração** passa a ser uma página única, com seções compartimentalizadas para Estação APRS, APRS-IS, Mapa/Topologia, Mensagens/Aparência, Aplicativo, Atualizações e Backup/Dados.
- Ao tentar mudar de aba com alterações não salvas, o cliente oferece **Salvar e sair**, **Descartar alterações** ou **Cancelar**, preservando valores digitados quando o salvamento falha.
- Adicionado **Restaurar configuração padrão**, que redefine preferências sem apagar mensagens, estações, logs ou tracklogs.
- **Conectar ao iniciar** foi mantido junto aos parâmetros APRS-IS e passa a vir habilitado em novas instalações, sem sobrescrever a preferência já salva em instalações existentes.
- O filtro padrão de novas instalações passa a usar prefixos brasileiros: `p/PP/PQ/PR/PS/PT/PU/PV/PW/PX/PY/ZV/ZW/ZX/ZY/ZZ`; filtros personalizados existentes permanecem intactos.
- O editor gráfico APRS-IS passa a suportar filtro Brasil, raio com centro da estação ou coordenadas informadas, prefixos, indicativos exatos, área geográfica, tipos de pacote, interpretação dos componentes conhecidos, validação básica e cópia da string.
- A seleção de idioma mostra **🇧🇷 Português** como padrão e **🇺🇸 English**; os novos controles da v1.6 também receberam tradução.
- Adicionado botão rápido de tema no cabeçalho, sincronizado com a configuração persistida.
- Em Mensagens agrupadas, o título **Conversas** alterna a ordenação alfabética A–Z/Z–A e a conversa selecionada preenche automaticamente o campo **Destino**, incluindo SSID.
- Mensagens longas passam a registrar grupo/parte, mostrar status agregado e permitir retry individual. Timeout e número máximo de retries são configuráveis, e o retry automático usa novo ID APRS.
- Corrigida a aplicação do peso da fonte nas colunas **De**, **Para** e **Tipo**.
- Na aba Log, **data e hora permanecem em uma única linha**; clicar em **Hora** alterna a ordenação cronológica nos dois sentidos e o alinhamento das colunas foi padronizado.
- A topologia observada ganha ranking de digipeaters, ranking de IGates, identificação de enlaces que deixaram de aparecer, comparação com o período anterior, histórico de eventos e animação temporal no mapa.
- Linux passa a publicar **AppImage x86_64**, além de `.deb` e `.tar.gz`; o workflow também executa testes de núcleo em Ubuntu 22.04 e 24.04.
- Adicionadas notificações nativas best-effort para mensagens pessoais no Linux (`notify-send`) e macOS (`osascript`), mantendo o aviso sonoro existente no Windows.
- Implementado atualizador integrado com consulta da Release oficial, seleção do asset da plataforma, download, cálculo SHA-256 e conferência do digest SHA-256 quando fornecido pelo GitHub.
- Novas opções: **Verificar atualizações automaticamente** (padrão ligado), **Baixar atualização automaticamente** (padrão desligado) e **Instalar atualização automaticamente ao fechar** (padrão desligado), além do botão **Verificar atualização agora**.
- Windows Portable pode aplicar a atualização ao fechar e mantém uma cópia anterior para rollback; Windows Setup pode iniciar o instalador; macOS abre o DMG baixado; Linux AppImage pode iniciar o novo AppImage. Pacotes Linux `.deb`/`.tar.gz` continuam com instalação manual quando privilégios do sistema são necessários.
- O envio manual de beacon com altitude de contingência em **0 m** continua permitido e agora exibe uma recomendação não bloqueante para informar a altitude real.
- O pop-up de nova mensagem passa a oferecer **Ler mensagem** além de **Responder** e **OK**; a ação abre Mensagens e foca a conversa do remetente quando o agrupamento estiver ativo, ou a linha recebida na visualização normal.
- O bloco de Estação foi corrigido para manter **Latitude, Longitude e Altitude em linhas independentes**, evitando extrapolação horizontal em DMS e com fontes maiores.
- Atualizados README, guia Linux, notas de Release, screenshots do manual e gerador do PDF para refletir a v1.6.

## v1.5 - 2026-09-24

- Hotfix focado exclusivamente na versão **Windows portátil** para validação antes de gerar os demais instaladores.
- Corrigida a falha de JavaScript que interrompia a inicialização da interface antes de registrar os eventos das abas e dos botões do pop-up de configuração.
- A causa era o uso do seletor de elemento único `$()` em trechos que chamavam `.forEach()`; esses pontos foram corrigidos para o seletor de coleção `$()`.
- Corrigidos também os mesmos usos incorretos em linhas de estações, seções de configuração e tipos de filtro.
- Adicionado teste de regressão que falha caso o frontend volte a usar `$().forEach()`.
- Mantidas as correções da v1.4 para carregamento não bloqueante do mapa e conexão APRS-IS com diagnóstico melhorado.
- Esta release é publicada inicialmente apenas como **Portable x64**, conforme solicitado, para teste funcional antes da geração dos demais pacotes.

## v1.4 - 2026-09-24

- Hotfix para a regressão da v1.3 em que a interface podia ficar aparentemente travada quando o carregamento remoto do Leaflet demorava ou falhava.
- O carregamento do JavaScript do Leaflet passa a ser **assíncrono**, evitando que um CDN lento ou bloqueado impeça o funcionamento das abas, configurações e demais recursos locais.
- A inicialização do aplicativo passa a tolerar falhas parciais: mapa, versão, log ou outras rotinas não interrompem mais toda a interface.
- A geolocalização automática deixa de bloquear a sequência de inicialização e é executada de forma atrasada e independente.
- A conexão APRS-IS passa a usar **IPv4 explicitamente**, reduzindo esperas em redes Windows com IPv6 parcial ou sem rota funcional.
- Cada tentativa TCP utiliza timeout menor e o cliente testa, em sequência, o servidor configurado, **rotate.aprs2.net** e **soam.aprs2.net**, sem repetir endereços.
- Na conexão inicial, o cliente deixa de tentar indefinidamente: após três ciclos sem sucesso, encerra as tentativas e volta a exibir **Conectar**.
- O erro final de conexão APRS-IS passa a ser mostrado diretamente ao usuário, facilitando diagnóstico de DNS, firewall, porta bloqueada ou servidor indisponível.
- Reconexões após uma sessão que já esteve conectada continuam automáticas.

## v1.3 - 2026-09-24

- Corrigida a configuração inicial de conexão APRS-IS para novas instalações, usando **soam.aprs2.net:14580** como servidor padrão e tentativa alternativa por **rotate.aprs2.net**.
- Instalações v1.2 ainda usando o antigo padrão **brazil.aprs2.net:14580** são migradas automaticamente para o novo servidor padrão.
- O campo **Servidor APRS-IS** passa a oferecer sugestões regionais sem impedir o uso de um endereço manual.
- **Indicativo** permanece obrigatório e agora é validado explicitamente antes da conexão.
- O **Passcode APRS-IS** é calculado automaticamente a partir do indicativo-base e também é usado automaticamente na conexão quando o campo ainda não foi salvo.
- Ao clicar em **Conectar** com Indicativo, Latitude, Longitude ou Altitude ausentes, o cliente mostra um **pop-up** com a relação exata dos campos pendentes.
- O pop-up possui o botão **Ir para Configuração**, que abre **Configuração → APRS / Estação**, realça todos os campos obrigatórios ausentes e posiciona o foco no primeiro deles.
- Os destaques dos campos obrigatórios desaparecem conforme os valores são preenchidos.
- Na primeira execução, o cliente solicita a **localização atual** do usuário quando a plataforma oferece geolocalização.
- Com autorização, **Latitude e Longitude são pré-preenchidas automaticamente** e o mapa é inicialmente centralizado na posição atual.
- Depois da centralização inicial, o aplicativo respeita o centro e o zoom escolhidos manualmente e não recentraliza continuamente.
- Se a geolocalização não fornecer altitude, o cliente usa **0 m** para não impedir a conexão, exibe uma recomendação para informar a altitude real e identifica visualmente que o valor foi assumido.
- Uma altitude já informada manualmente não é sobrescrita por 0 m em execuções futuras.
- Mantido o botão **Usar minha localização atual** para atualização manual posterior.
- Manual PDF e ajuda interna atualizados para refletir o novo fluxo de conexão, localização automática, altitude de contingência e servidor APRS-IS padrão.

## v1.2 - 2026-09-24

- Configuração de texto ampliada para **Mensagens, Estações e Logs**, com fonte, tamanho, peso normal/negrito e espaçamento entre linhas independentes.
- As alterações tipográficas são pré-visualizadas imediatamente e persistidas no banco local após salvar.
- Adicionados botões **Restaurar padrão** separados para Mensagens, Estações e Logs.
- Manual PDF reformulado com **capa azul profissional** e a identidade visual oficial PT2VHF / APRS / CLIENT.
- A capa do manual passa a usar a logo oficial fornecida para o projeto.
- Corrigido o processamento de Markdown/changelog que podia gerar sequências inválidas como `\\1\\1\\1` no PDF.
- O manual passa a incorporar **screenshots reais da aplicação** capturados automaticamente no processo de release.
- Screenshots documentam mapa, mensagens, estações, log, configuração APRS, editor de filtro e configuração visual.
- Adicionada validação automática do manual: número mínimo de páginas, tamanho mínimo e presença de seções obrigatórias.
- O workflow de release falha antes da publicação do PDF se o manual estiver vazio, incompleto ou sem conteúdo legível.
- Mantidos builds Windows, Linux, macOS Apple Silicon e macOS Intel na mesma Release.

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
