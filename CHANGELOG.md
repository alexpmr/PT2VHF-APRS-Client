# Changelog

## 1.8.4 - 2026-10-02

- Adiciona monitoramento separado de **CPU e memória do PT2VHF APRS Client** e do **sistema operacional**.
- Define como padrão **90% para CPU** e **90% para memória**, com alerta somente após **30 segundos de condição crítica sustentada**.
- O alerta aparece em **popup não bloqueante**, indicando recurso, escopo, valor atual, limite, duração e horário.
- Implementa **histerese de 5 pontos percentuais** para recuperação e **cooldown padrão de 10 minutos**.
- Registra cada alerta no **log de diagnóstico**, incluindo versão, plataforma e métricas do aplicativo e do sistema.
- Adiciona em **Configuração → Saúde do aplicativo** opções para ativação, limites, persistência e cooldown.
- Na aba **Mapa**, a barra com **Histórico, período (Completo etc.), Ver, Velocidade, Tipo de mapa, Camadas e Exportar KML** passa a ficar **alinhada à esquerda**.
- Inclui traduções em **PT-BR, English, Español e Français** e testes de regressão.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.3 - 2026-10-01

- Em **Estatísticas → Software / dispositivos APRS**, separa as identificações em **Aplicativo APRS**, **Dispositivo / Hardware** e **Indeterminado**.
- Adiciona filtros persistentes **Mostrar aplicativos APRS**, **Mostrar dispositivos** e **Mostrar não identificados**.
- O ranking, posição e percentual passam a ser recalculados **somente sobre as categorias atualmente visíveis**.
- Isso permite comparar diretamente clientes como **PT2VHF APRS Client, UI-View, WinAPRS, APRSdroid e Dire Wolf** sem rádios D-STAR, rigs, HTs e trackers concorrendo no mesmo ranking.
- A classificação usa a base local **APRS Device Identification / TOCALL** e metadados conhecidos; identificações ambíguas permanecem **Indeterminadas**.
- Quando categorias diferentes estão misturadas, a tabela mostra discretamente a categoria de cada item.
- Em **Mapa → Ver**, substitui o botão **Tudo** pelas ações **Selecionar tudo** e **Remover tudo**.
- As ações globais atualizam imediatamente categorias, subcategorias, estados intermediários e preferências persistidas.
- Inclui **AIS**, **Balão/Radiosonda** e demais filtros dinâmicos no comportamento global de Mapa → Ver.
- Traduz os novos controles em **PT-BR, English, Español e Français**.
- Adiciona testes de regressão para classificação de aplicativos/hardware, recálculo de percentuais e ações globais do Mapa.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.2 - 2026-10-01

- O servidor web interno passa a usar **porta dinâmica**, começando em **8080** e avançando para **8081, 8082, 8083...** quando houver conflito.
- A escolha da porta é feita pelo **bind real do servidor**, sem janela de corrida entre “testar” e “abrir”.
- Windows, Linux e macOS usam a URL realmente alocada no WebView/navegador; a instância Windows também persiste temporariamente a porta para permitir localizar uma execução já aberta.
- A porta escolhida é exibida como **Interface local** e registrada no diagnóstico do Windows.
- A captura automática do Manual PDF deixa de assumir uma porta fixa e acompanha a porta publicada pela aplicação.
- Em **Mapa → Ver → Objetos**, objetos identificados de forma confiável como **AIS** passam a aparecer em categoria própria.
- **Balão/Radiosonda** permanece como categoria existente e independente.
- A identificação AIS é conservadora: AIS/MMSI e marcadores equivalentes classificam; o símbolo de barco isolado não força a categoria.
- O menu **Ver** mantém todas as categorias/subcategorias habilitadas por padrão em novas configurações e preserva escolhas já salvas.
- Remove a **bandeira grande** da aba Configuração; mantém seletor de idioma compacto e as pequenas bandeiras do seletor rápido no cabeçalho.
- Adiciona indicador da interface local em Configuração e traduções correspondentes em PT-BR/EN/ES/FR.
- Adiciona testes de regressão para fallback de portas, AIS, defaults do menu Ver, UI de idioma e integração dos launchers.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.1 - 2026-10-01

- Remove **Relevo sombreado** do menu Camadas e do código de carregamento; **Relevo com corte** permanece como a camada de elevação.
- Corrige **Claro** e **Escuro** para funcionar sem API key, usando tiles OpenStreetMap com filtros visuais locais.
- Adiciona mapas-base **CyclOSM**, **Humanitário / HOT**, **OSM.DE** e **ÖPNVKarte**, todos sem API key na configuração padrão.
- Mantém **OSM**, **OpenTopoMap** e **Satélite**.
- Adiciona fallback automático para **OSM** após falhas repetidas de um mapa alternativo, evitando mapa cinza/quebrado.
- Registra falhas de provedor no diagnóstico local.
- Traduz integralmente a nova aba **TNC / RF** para **PT-BR, English, Español e Français**, inclusive estados e textos dinâmicos.
- A troca de idioma passa a atualizar imediatamente o conteúdo TNC/RF já aberto.
- Atualiza traduções e ajuda dos novos mapas-base.
- Mantém todos os recursos da v1.8.0 e os defaults seguros de transmissão RF.
- Release completa de produção para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.0 - 2026-10-01

- Inicia a série **1.8** com integração RF/TNC no PT2VHF APRS Client.
- Adiciona nova aba **TNC / RF** com estado de conexão, monitor AX.25/APRS, configuração de papel RF, Digipeater, iGate e analisador adaptativo.
- Suporta **KISS TCP** e **KISS Serial**, incluindo detecção/listagem de portas seriais, baud rate, reconexão e contadores RX/TX.
- Implementa codec **KISS + AX.25 UI** com escaping FEND/FESC, CALL/SSID, path, bits de repetição e representação TNC2.
- Implementa **Digipeater** com perfis Fill-in (WIDE1-1), Wide/Regional (WIDEn-N) e aliases personalizados.
- O digi aplica supressão de duplicatas, bloqueio de loops, limite de hops, rate limit por origem e fila de TX priorizada.
- Implementa **iGate RF→APRS-IS** com qAR e **APRS-IS→RF** restritivo a mensagens destinadas a estações ouvidas diretamente por RF dentro da janela configurada.
- Adiciona tabela de estações ouvidas por RF, preservando timestamp próprio da última audição direta mesmo quando a estação depois chega via digi.
- Adiciona grafo **Quem fala com quem**, consolidando interações por RF/APRS-IS, ACK/REJ, contagem e última atividade.
- Adiciona otimizador em modos **Desligado**, **Observação/Recomendação** e **Automático conservador**; o modo automático reduz tráfego de baixa prioridade sob pressão local de TX sem reescrever arbitrariamente paths de terceiros.
- Adiciona auditoria detalhada das decisões: enviado, enfileirado, duplicado, bloqueado, ignorado ou suprimido, sempre com motivo.
- Adiciona retenção configurável para histórico TNC e persistência em SQLite.
- **Segurança operacional:** TX automático, Digipeater e iGate Internet→RF ficam desligados por padrão, exigem confirmação explícita e podem ser interrompidos imediatamente pelo botão **PARAR TX** sem desativar o monitor RX.
- Mensagens recebidas pelo TNC entram no histórico local sem gerar ACK pelo APRS-IS por engano.
- Adiciona testes de regressão para KISS, AX.25, WIDE1-1/WIDE2-2, loops, qAR, limpeza de path Internet, presença RF direta e defaults seguros de TX.
- Mantém todos os recursos da v1.7.23, incluindo Relevo com corte, Relevo sombreado, radar meteorológico e mapas-base Claro/Escuro.
- Release completa de produção para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.7.23 - 2026-09-30

- Adiciona **Mapa → Camadas → Relevo com corte**, baseado em DEM Terrarium real.
- O slider vertical no lado direito do mapa define a cota mínima em tempo real; somente terreno com altitude igual ou superior permanece destacado.
- Mantém **3.000 m** como máximo padrão do slider, configurável entre **100 e 9.000 m**, com ajuste automático da cota quando necessário.
- Adiciona opacidade independente do Relevo com corte e persistência de cota, máximo e transparência.
- Adiciona **Relevo sombreado** independente usando Esri World Hillshade.
- Adiciona mapas-base **Claro (CARTO Positron)** e **Escuro (CARTO Dark Matter)**, além de OSM, Topográfico e Satélite.
- Mantém Clima/RainViewer como overlay independente e **não inclui camada de raios**.
- Mantém estações, objetos APRS, tracklogs, enlaces, replay e animações acima das camadas de relevo.
- Adiciona proxy local para tiles DEM, evitando dependência de CORS no navegador/WebView.
- Release completa de produção para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## v1.7.22 - 2026-09-30

- **Pipeline:** corrigidos testes legados de links v1.7.20 e conflito de literal de cadência, permitindo a geração completa da produção v1.7.22.

- **Mapa / Camadas:** adiciona o menu **Camadas** junto ao tipo de mapa e a opção **Clima**.
- **Radar meteorológico:** sobrepõe o radar de precipitação mais recente disponível no RainViewer, independentemente do mapa-base.
- **Atualização do radar:** consulta periodicamente novos quadros enquanto a camada estiver ligada; em falha transitória, preserva a última camada válida.
- **Configuração:** adiciona controle de **opacidade da camada de clima**, com persistência e migração automática do banco.
- **Popup da estação:** limita altura, habilita rolagem interna e reforça auto-pan/keepInView para evitar que o topo fique escondido pela interface.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF, publicada como **latest**.

## v1.7.21 - 2026-09-30

- **Mapa / enlaces:** hover exibe painel fixo com origem, destino, RF × Internet/APRS-IS, sentido, pacotes e janela de observação.
- **Mapa / tracklogs:** hover exibe início/fim, duração, distância, velocidade média/máxima, quantidade de posições, pontos inicial/final e tempo desde a última posição.
- **Tracklogs enriquecidos:** novos pontos passam a guardar path, raw, RSSI e SNR quando disponíveis, permitindo identificar digipeaters, iGates e caminhos APRS observados.
- **Compatibilidade:** tracklogs históricos anteriores à v1.7.21 permanecem utilizáveis; campos não existentes no histórico são simplesmente omitidos.
- **Atualizador:** repetir um download reutiliza/sobrescreve o mesmo arquivo temporário e oficial, evitando cópias numeradas.
- **Limpeza automática:** após a versão atual iniciar corretamente, instaladores/pacotes antigos e downloads parciais são removidos da pasta temporária, preservando uma atualização mais nova ainda pendente.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## v1.7.20 - 2026-09-30

- **Estatísticas / Período:** corrige o filtro temporal; a consulta passa a usar o período selecionado na própria aba Estatísticas.
- **Mapa × Estatísticas:** os períodos agora são independentes e persistidos em chaves separadas.
- **RF × Internet:** `qAR`/`qAO` preservam evidência de entrada direta por RF; `qAr` e demais caminhos remotos continuam classificados como Internet/APRS-IS.
- **Primeira execução:** configuração incompleta abre automaticamente a aba **Configuração**, com foco no campo **Indicativo**.
- **GitHub:** remove a tabela de contadores de downloads do README e adiciona downloads diretos da Release `latest`.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## v1.7.19 - 2026-09-29

- **Mapa / Ver:** consolida a árvore hierárquica por famílias funcionais, com seleção parcial correta.
- **Objetos APRS:** deixam de herdar a classificação do TOCALL/software da estação publicadora; o tipo do objeto passa a ser determinado pela semântica do próprio objeto.
- **Categorias exclusivas:** estações, digipeaters, iGates e objetos permanecem em grupos principais distintos.
- **Estatísticas:** junta **Estações mais ativas** e **Estações que mais interagiram** em uma única tabela ordenável.
- **Ranking de estações:** exclui telemetria, digipeaters e iGates; mostra pacotes úteis, interações, mensagens enviadas/recebidas, contatos, última atividade e tipo/aplicação.
- **RF observado:** o popup da estação passa a listar as estações comprovadamente recebidas por RF, com contagem e última observação.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF, publicada como **latest** no GitHub.


## v1.7.15 - 2026-09-28

- **Interações APRS:** digipeaters, hotspots, gateways e repetidores identificados como infraestrutura ficam com mensagens e queries dirigidas desabilitadas quando não há evidência de suporte interativo.
- **Detecção por evidência:** mensagens recebidas, ACK/REJ, queries recebidas ou respostas efetivas a queries liberam automaticamente a interação com a estação.
- **Objetos/itens APRS:** continuam não interativos.
- **Popup:** ações passivas, como logs, favorito e histórico de queries, permanecem disponíveis mesmo quando a transmissão dirigida está desabilitada.
- **Atualizações:** mantém checagem inicial e a cada **30 minutos**, com **Versão atualizada** ou **Versão X.X.X disponível** em laranja e piscando.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF, publicada como **latest** no GitHub.


## v1.7.9 - 2026-09-28

- **Mapa:** novo seletor **Velocidade** entre **Topologia observada** e o período **Completo**, com opções **0,5x / 1x / 2x / 5x** e padrão **1x**.
- **Replay:** o seletor de velocidade do painel de replay foi reduzido às mesmas quatro opções e permanece sincronizado com o controle da barra contextual.
- **Persistência:** a velocidade escolhida é preservada localmente entre execuções.
- **Barra superior:** em português, **Build** passa a ser apresentado como **Versão**.
- **Build:** versão de validação somente **Windows x64 Portable**.


## v1.7.8 - 2026-09-28

- **Windows x64:** build de validação somente em formato **Portable**.
- **Animação APRS:** os segmentos observados passam a ser reproduzidos **hop a hop**, na ordem real do path APRS, em vez de todos simultaneamente.
- **Atividade por hop:** o nó de destino pulsa quando o pacote chega a cada etapa do percurso.
- **RF × Internet:** enlaces RF e trechos APRS-IS/Internet continuam visualmente separados; tráfego de Internet não é promovido a RF.
- **ACK/REJ e respostas:** o retorno segue o **path efetivamente observado**. Se a resposta utilizar os mesmos digipeaters, a animação percorre o mesmo caminho em sentido inverso.
- **Queries APRS:** respostas automáticas passam a ficar ativadas por padrão em novas configurações.


## v1.7.7 - 2026-09-28

- **Mapa:** removida definitivamente a recriação do botão global **Histórico** pelo patch legado de build; permanece apenas o controle da barra contextual do Mapa.
- **Mensagens:** **Apagar todas** passa a se chamar **Limpar**, mantendo estilo vermelho e confirmação antes de remover o histórico local.
- **Topologia:** novo padrão visual com linhas **amarelas (#ffff00)** e espessura mínima de **1 px**.
- **Tracklog:** permanece **azul (#3ba6ff)** por padrão.
- **Animação e som:** permanecem ativados por padrão para novas configurações.
- **Atualizações:** a checagem periódica de nova versão passa de 5 para **30 minutos**; o agendador só programa a próxima execução depois da conclusão da verificação atual.
- **Windows ARM64:** novos builds nativos **Setup ARM64** e **Portable ARM64**, com seleção de asset pelo updater conforme a arquitetura detectada.
- **Topologia RF × APRS-IS:** o parser passa a preservar a capitalização dos q-constructs; `qAR`/entrada direta e `qAr`/IGate remoto via APRS-IS deixam de ser confundidos, evitando enlaces de Internet desenhados como RF.
- Configurações visuais já personalizadas pelo usuário são preservadas; os novos valores são aplicados somente como padrão/reset.
- Adicionados testes de regressão para o Histórico contextual, botão Limpar, padrões do Mapa e cadência de atualização.
- Release completa: Windows x64 + Windows ARM64 (Setup + Portable), Linux x86_64 TAR.GZ + AppImage + DEB, macOS ARM64/Intel DMG e Manual PDF.

## v1.7.6 - 2026-09-28

- **Atualizador Windows:** o helper passa a usar **CMD nativo** como caminho principal para aplicar atualização automática, reduzindo falhas de inicialização do PowerShell.
- O fallback PowerShell passa a ser gravado com BOM UTF-8 e o tempo de confirmação do helper foi ampliado.
- **Exportação KML:** ao gerar o arquivo no aplicativo desktop, abre **Salvar como** para escolher pasta e nome do arquivo; o cancelamento é tratado normalmente.
- Em modo navegador, usa o File System Access API quando disponível e, como último fallback, informa claramente que o arquivo seguirá para a pasta de downloads do navegador.
- **Mapa:** os botões **Histórico** e **Exportar KML** passam a ficar na mesma barra contextual de **Estações, Tracklog e Topologia**.
- **Estatísticas:** novo bloco **Estações que mais interagiram**, calculado somente sobre conversas APRS manuais.
- O ranking ignora beacons, telemetria, ACK/REJ, queries, respostas automáticas, boletins e retries; mensagens multipartes do mesmo grupo não são infladas artificialmente.
- Adicionados testes de regressão para helper de atualização Windows, seletor de arquivo do KML, posição dos controles do Mapa e ranking de conversas manuais.
- Release completa: Windows x64 Setup + Portable, Linux x86_64 TAR.GZ + AppImage + DEB, macOS ARM64/Intel DMG e Manual PDF.

## v1.7.5 - 2026-09-28

- **Exportação KML:** novo botão na barra superior abre um seletor com **Estações, Posições, Tracklogs e Topologia/enlaces**, todos marcados por padrão, além do período a exportar.
- O KML é organizado em pastas separadas e preserva indicativo, timestamp, altitude e metadados relevantes, com saída compatível com Google Earth.
- **Qualidade de posição:** coordenadas **0,0**, fora dos limites geográficos, saltos com velocidade implícita extrema e posições incompatíveis com um iGate RF conhecido são rejeitadas.
- Dados geográficos rejeitados não entram no mapa, tracklogs, topologia, replay, distância nem exportações; a última posição válida é preservada quando disponível.
- **Estatísticas:** novo bloco **Estações com problemas** mostra anomalia, quantidade, recorrência e atalhos para Mapa/Logs.
- **Estatísticas:** novo bloco **Possíveis melhorias** sinaliza baixa redundância, concentração excessiva em um iGate e possíveis trechos de baixa cobertura, sempre identificados como inferências do tráfego observado.
- **Estatísticas:** indicativos em **Digipeaters mais utilizados** e **iGates mais ativos** passam a abrir a estação diretamente no mapa.
- **Mensagens:** conversas agrupadas podem ser ordenadas por **Remetente** ou **Data**, em ordem crescente ou decrescente.
- **Mensagens:** ação **Apagar todas** remove somente o histórico local após confirmação e atualiza imediatamente os indicadores de não lidas.
- Adicionados testes de regressão para KML, validação geográfica, anomalias, navegação das Estatísticas e controles de Mensagens.
- Release completa: Windows x64 Setup + Portable, Linux x86_64 TAR.GZ + AppImage + DEB, macOS ARM64/Intel DMG e Manual PDF.

## v1.7.4 - 2026-09-27

- **Atualizador:** mensagens temporárias agora ficam acima do modal de atualização e não são mais desfocadas pelo overlay.
- **Atualizador:** falhas de download/instalação aparecem também dentro do próprio modal, com destaque visual de erro e texto técnico preservado.
- **Atualizador:** estados **Preparando**, **Sucesso** e **Erro** ganharam apresentação própria; após falha, os botões de instalar, abrir a Release e fechar o modal voltam a ficar disponíveis.
- O aviso inline usa `aria-live="assertive"`, melhorando também a sinalização de erro por tecnologias assistivas.
- Adicionados testes de regressão para camada visual, mensagem inline e recuperação dos controles após erro.
- Release completa: Windows x64 Setup + Portable, Linux x86_64 TAR.GZ + AppImage + DEB, macOS ARM64/Intel DMG e Manual PDF.

## v1.7.3 - 2026-09-27

- **Atualizador:** corrigida a geração dos scripts auxiliares PowerShell/Bash. As quebras de linha estavam sendo gravadas como texto literal `\n`, impedindo o helper de executar corretamente.
- **Baixar e instalar:** o clique agora fornece feedback visual imediato, dispara diretamente o fluxo de instalação e não fica aparentemente inerte enquanto o backend trabalha.
- **Atualizações:** adicionados registros de diagnóstico para solicitação de instalação, asset selecionado, URL, caminho temporário, tamanho, SHA-256 e erros.
- **Estatísticas:** versões do mesmo cliente APRS passam a ser agrupadas por família canônica. Exemplo: **Dire Wolf 1.7**, **1.8** e **1.9** aparecem como uma única linha **Dire Wolf**.
- Aliases, nomes originais e TOCALLs permanecem preservados internamente para diagnóstico, embora a interface exiba apenas a família consolidada.
- Adicionados testes que geram os scripts auxiliares reais e validam que utilizam quebras de linha válidas, além de teste de regressão do agrupamento por família.
- Release completa: Windows x64 Setup + Portable, Linux x86_64 TAR.GZ + AppImage + DEB, macOS ARM64/Intel DMG e Manual PDF.

## v1.7.2 - 2026-09-27

- **Mapa:** os controles **Estações**, **Tracklog** e **Topologia observada** passam para a mesma barra contextual do botão **Histórico**, mantendo uma única linha compacta e liberando mais área vertical para o mapa.
- **Popup da estação:** **Última recepção** passa a mostrar também o tempo decorrido, como **há 2 min**, **há 3 h e 26 min** ou **há 4 dias**.
- O tempo relativo da última recepção é atualizado automaticamente enquanto o popup permanece aberto e acompanha o idioma corrente (**PT/EN/ES/FR**).
- **Estatísticas:** diferentes TOCALLs que resolvem para o mesmo nome amigável de software/dispositivo passam a ser consolidados em uma única linha, com quantidade e percentual recalculados.
- Os identificadores técnicos associados a cada software permanecem preservados internamente; versões com nomes amigáveis distintos, como **Dire Wolf 1.8** e **Dire Wolf 1.9**, continuam separadas.
- Mantido o destaque correto do **PT2VHF APRS Client** mesmo quando mais de um identificador técnico estiver associado ao mesmo nome amigável.
- Adicionados testes de regressão para consolidação de software, disposição dos controles do Mapa e atualização do tempo relativo.
- Release completa: Windows x64 Setup + Portable, Linux x86_64 TAR.GZ + AppImage + DEB, macOS ARM64/Intel DMG e Manual PDF.

## v1.7.1 - 2026-09-27

- Corrigido o atualizador integrado: a aplicação só é encerrada após o **helper externo confirmar que iniciou**; se o helper falhar, o programa permanece aberto e informa o erro.
- O modal **Nova versão disponível** deixa de iniciar a instalação apenas pelo clique no indicador e permanece aberto durante o fluxo; **Depois** só fecha antes do início da atualização.
- O indicador **Nova versão** passa a piscar/pulsar discretamente enquanto houver atualização pendente.
- Adicionado filtro contra **saltos irreais de coordenadas**: posições incompatíveis com deslocamento plausível são rejeitadas sem substituir a última posição válida; três posições coerentes na nova região confirmam uma relocação.
- O renderizador de tracklogs históricos também quebra o traçado em saltos extremos, evitando linhas falsas de centenas/milhares de quilômetros.
- Removido o controle **Atividade** do Mapa. **Estações**, **Tracklog** e **Topologia observada** passam a ter liga/desliga e período independentes: Completo, 1 h, 6 h, 24 h e 7 dias.
- O controle **Histórico** passa para uma barra contextual abaixo das abas e só aparece com a aba **Mapa** ativa.
- A aba **Mensagens** passa a pulsar quando chega uma nova mensagem direta enquanto o usuário está em outra aba.
- Em **Estatísticas → Estações mais ativas**, os indicativos passam a ser clicáveis e abrem Mensagens já com o destinatário preenchido.
- Nova aba **Sobre**, com apresentação de Alex/PT2VHF, contatos, link **tiny.cc/aprs** e divulgação manual do projeto por **Announcement APRS BLNA**.
- O Announcement usa o indicativo/SSID corrente como remetente, exibe prévia, permite edição, respeita 67 caracteres e exige confirmação explícita.
- Ampliada a cobertura das traduções **Português, English, Español e Français**, incluindo áreas recentes e atualização imediata de conteúdo dinâmico.
- Release completa: Windows x64 Setup + Portable, Linux x86_64 TAR.GZ + AppImage + DEB, macOS ARM64/Intel DMG e Manual PDF.

## v1.7 - 2026-09-27

- Inaugurada a linha **v1.7**; as próximas versões seguirão **v1.7.1, v1.7.2, v1.7.3...**.
- Na aba **Mapa**, os controles **Atividade** e **Topologia observada** ficam em uma barra superior fora do canvas, eliminando sobreposição.
- A animação de tráfego entre estações em modo **Ao vivo** passa a vir ativada por padrão em novas instalações, com preferência persistida em Configurações.
- Na aba **Mensagens**, os botões **Agrupado por remetente**, **Minhas mensagens** e **Não lidas** ficam mais baixos e com texto em uma única linha.
- A conversa em foco passa a ser sincronizada com o campo **Destinatário**; ao informar um indicativo diferente, o cliente muda o foco para a conversa correspondente ou deixa claro que é um novo destinatário, evitando envio acidental à estação errada.
- Adicionados **Español (ES)** e **Français (FR)** ao seletor de idioma, mantendo Português como padrão, persistência da escolha e fallback seguro para Português.
- Na aba **Estatísticas**, o ranking de software/aplicativos passa a mostrar somente o **nome amigável**, mantendo TOCALL/identificadores técnicos apenas internamente.
- A fonte padrão da aba **Estatísticas** fica ligeiramente maior e passa a ter controle próprio de tamanho em **Configurações**.
- Release completa: **Windows x64 Setup + Portable**, **Linux x86_64 TAR.GZ + AppImage + DEB**, **macOS ARM64/Intel DMG** e **Manual PDF**.

## v1.6.24 - 2026-09-27

- A **logo APRS fornecida pelo projeto** passa a ser a fonte visual única da aplicação.
- Cabeçalho e favicon passam a usar diretamente `app_logo.png`, derivado da imagem oficial enviada.
- Ícones de Windows, Linux e macOS, bandeja do Windows e capa do Manual PDF passam a ser gerados a partir da mesma logo.
- O gerador do ícone macOS deixa de desenhar uma identidade alternativa e passa a derivar o `.icns` diretamente da logo oficial.
- O pipeline deixa de converter uma logo SVG separada para o manual, evitando divergência visual entre builds.
- Adicionadas notas internas da v1.6.23 que estavam ausentes do histórico de novidades do aplicativo.
- Backlog consolidado: itens de queries APRS, estatísticas de clientes e gauges CPU/RAM já implementados são retirados das pendências; permanecem abertas as validações reais de estabilidade e compatibilidade de banco.
- Adicionados testes/validação de release para impedir regressão para logos antigas ou geradas separadamente.
- Release completa multiplataforma: Windows x64 Setup + Portable, Linux x86_64 TAR.GZ + AppImage + DEB, macOS ARM64/Intel DMG e Manual PDF.

## v1.6.23 - 2026-09-27

- A identidade visual do **PT2VHF APRS Client** é padronizada com a mesma logo vetorial/raster no cabeçalho e favicon da interface.
- Os ícones de **Windows, Linux e macOS** passam a usar a mesma identidade visual, evitando divergências entre plataformas.
- A bandeja do Windows e a capa do Manual PDF passam a usar a mesma identidade visual.
- Adicionada validação no pipeline para impedir a geração da Release caso os arquivos de logo estejam ausentes/inválidos.
- Na aba **Mapa**, adicionado filtro de atividade das estações pela última interação/recepção conhecida.
- O filtro oferece **Tudo** (padrão), **menos de 2 h**, **2 a 24 h** e **mais de 24 h**.
- Ao aplicar o filtro, marcadores e tracklogs de estações fora da faixa são ocultados; a topologia evita manter enlaces para estações conhecidas que foram filtradas.
- O mapa mostra a quantidade de estações visíveis em relação ao total quando um filtro estiver ativo.
- A legenda do Mapa ganha opção de **minimizar/expandir** com persistência local da preferência.
- Corrigido o rate-limit de respostas automáticas a queries APRS para não bloquear indevidamente a **primeira query** quando o sistema tiver menos de 30 segundos de uptime.
- Mantidos os recursos de atualização integrada e demais funções da v1.6.22.
- Release completa multiplataforma: Windows x64 Setup + Portable, Linux x86_64 TAR.GZ + AppImage + DEB, macOS ARM64/Intel DMG e Manual PDF.

## v1.6.22 - 2026-09-26

- O aviso de **nova versão** passa a iniciar diretamente o download e a instalação do pacote compatível com a plataforma/arquitetura em execução.
- Reativado e ampliado o atualizador integrado com seleção exata de asset para Windows Setup/Portable, Linux AppImage/DEB/TAR.GZ e macOS ARM64/Intel.
- O download é restrito à Release oficial, confere o tamanho do asset, calcula **SHA-256** e valida o digest publicado pelo GitHub quando disponível.
- A instalação é conduzida por um **updater auxiliar separado**, iniciado antes do encerramento da aplicação atual.
- A aplicação solicita encerramento limpo de APRS-IS, manutenção e componentes de fundo; após timeout, o helper pode encerrar somente o PID da instância anterior antes de substituir os binários.
- A nova versão é aberta automaticamente após instalação bem-sucedida.
- Windows Portable mantém backup para rollback; Windows Setup usa o instalador com elevação quando necessária.
- Linux AppImage/TAR.GZ são atualizados in-place; DEB usa dpkg/pkexec quando disponível. macOS monta o DMG, substitui o bundle ou usa ~/Applications como fallback.
- Adicionado lock de atualização com PID para impedir atualização concorrente entre instâncias e recuperar locks obsoletos.
- Dados do usuário permanecem fora dos binários e são preservados.
- Release completa: **Windows x64 Setup + Portable**, **Linux x86_64 TAR.GZ + AppImage + DEB**, **macOS ARM64 + Intel DMG** e **Manual PDF**.

## v1.6.21 - 2026-09-26

- A aba **Análise** passa a se chamar **Estatísticas** em toda a interface e documentação.
- Adicionada a seção **Estações mais ativas**, ordenada por quantidade de pacotes válidos no período selecionado.
- O ranking exclui pacotes de **telemetria** para evitar distorção causada por transmissões automáticas frequentes.
- **iGates e digipeaters** são excluídos do ranking principal e permanecem nas estatísticas dedicadas.
- Cada linha mostra posição, indicativo, quantidade de pacotes válidos e percentual sobre o total elegível.
- Adicionado teste automatizado para impedir regressões nos filtros do ranking.
- Release de teste somente **Windows x64 Portable**.

## v1.6.20 - 2026-09-26

- O bloco **Software / dispositivos APRS** passa a mostrar nomes amigáveis derivados da base oficial **APRS Device Identification (aprsorg/aprs-deviceid)**, mantendo o TOCALL em texto secundário.
- A base é embarcada localmente para funcionamento offline; o projeto inclui atribuição à fonte **CC BY-SA 2.0**.
- O ranking mostra os **Top 20** e acrescenta uma linha destacada do **PT2VHF APRS Client** caso ele esteja fora do corte, preservando sua posição real, quantidade de estações e percentual.
- O cliente passa a usar o TOCALL experimental **APZVHF** nas transmissões geradas pelo aplicativo, permitindo reconhecer instalações do PT2VHF APRS Client no tráfego observado.
- O seletor de idioma na barra superior passa a mostrar apenas o idioma corrente; ao clicar, abre um menu com **Brasil / Português** e **Inglaterra / English**.
- Corrigida a bandeira de English para usar especificamente a **bandeira da Inglaterra (Cruz de São Jorge)**.
- Corrigida a classificação dos enlaces de topologia em pacotes **qAR/qAO**: o salto recebido pelo IGate continua sendo classificado como **RF** e desenhado com linha contínua; o IGate fica registrado separadamente como ponto de entrada no APRS-IS.
- Bancos existentes migram automaticamente os antigos enlaces qAR/qAO gravados como `igate` para `rf`.
- Release completa multiplataforma com Windows x64, Linux x86_64, macOS ARM64/Intel e Manual PDF atualizado.


## v1.6.19 - 2026-09-26

- A aba **Análise** recebe um bloco de **clientes/versões APRS** baseado no TOCALL do último pacote de cada estação, contabilizando cada indicativo uma única vez e ordenando do mais usado para o menos usado.
- O ranking mostra quantidade de estações, percentual entre os clientes identificados e uma contagem separada de **Não identificado**, sem inferir software quando o pacote não oferece informação suficiente.
- O popup da estação no **Mapa** passa a mostrar uma área explícita de **Resultado da última query**, com tipo de query, estado, horário, RTT, resposta recebida e caminho textual do Trace.
- A última resposta fica disponível ao reabrir o popup e pode ser recuperada do histórico SQLite daquela estação.
- Adicionado botão **Ver histórico de queries** no popup, mostrando consultas anteriores, status e RTT.
- Respostas de posição agora registram latitude/longitude no texto do resultado.
- Restaurado o seletor rápido de idioma na barra superior, com **Brasil / Português** e **Inglaterra / English**, e persistência imediata da escolha.
- Release completa multiplataforma com Windows x64, Linux x86_64, macOS ARM64/Intel e Manual PDF atualizado.


## v1.6.18 - 2026-09-25

- Adicionadas **Directed Station Queries APRS** no popup das estações do Mapa: Posição (`?APRSP`), Status (`?APRSS`), Ouvidos (`?APRSD`) e Trace (`?APRST`).
- Adicionado **Ping/ACK** com mensagem APRS identificada, medição de RTT e indicação de timeout.
- Queries são enviadas no formato APRS de mensagem direcionada **sem message ID**, exceto o Ping/ACK que usa ID para medir a confirmação.
- Adicionado histórico SQLite próprio para queries, respostas, RTT e caminho de trace.
- Respostas de posição/status/objetos e mensagens de trace são correlacionadas automaticamente com a query pendente.
- O **Trace** recebido é interpretado e exibido no Mapa: hops com posição conhecida ganham marcadores e enlaces; hops sem posição permanecem identificados no resultado sem localização inventada.
- Adicionada opção **Responder automaticamente a queries APRS de posição, status e trace**, desativada por padrão, com rate-limit de 30 s por origem/tipo.
- O cliente passa a responder `?APRSP`, `?APRSS`, `?APRST` e `?PING?` quando a opção estiver habilitada e a sessão APRS-IS estiver verificada.
- Release completa multiplataforma com Windows x64, Linux x86_64, macOS ARM64/Intel e Manual PDF atualizado.


## v1.6.17 - 2026-09-25

- Release completa multiplataforma consolidando as correções de estabilidade testadas na série 1.6.13-1.6.16.
- Mantida a correção do gargalo em `/api/topology`: JOINs indexáveis, cache/coalescência, limite interno de tempo e carregamento single-flight.
- Mantida a redução de fan-out do Mapa e o bloqueio de atualizações completas concorrentes.
- Mantida a consolidação do processamento RX em uma única transação por pacote e o housekeeping SQLite em lotes.
- Mantidos os indicadores de **CPU** e **RAM** em tempo real na barra superior.
- Publicados artefatos para **Windows x64** (Setup + Portable), **Linux x86_64** (TAR.GZ, AppImage e DEB) e **macOS** (Apple Silicon ARM64 e Intel x86_64).
- Manual PDF versionado regenerado com screenshots da versão e validado automaticamente no workflow.


## v1.6.16 - 2026-09-25

- Release de teste somente **Windows x64 Portable**.
- Corrigido o gargalo confirmado no `diagnostics.log`: `GET /api/topology` ocupava workers do Waitress por vários minutos.
- Os JOINs de topologia deixam de aplicar `UPPER()` em `callsign/source/target`, permitindo o uso do índice/PRIMARY KEY de `stations.callsign`.
- Adicionado cache curto e coalescência: nunca mais várias threads executam simultaneamente a mesma consulta de topologia.
- Adicionado limite interno de **2,5 s** para abortar uma consulta patológica antes que monopolize um worker HTTP.
- `loadTopology()` no frontend passa a ser single-flight.
- Adicionados índices auxiliares para `topology_edges` e `topology_events`.


## v1.6.15 - 2026-09-25

- Release de teste somente **Windows x64 Portable**.
- Removido o fan-out de `loadMapData()` causado por eventos de estações ainda sem marcador/posição.
- O refresh completo do Mapa passa a ser **single-flight**: uma execução por vez.
- Atividade visual por pacote foi deduplicada por estação e animações ao vivo foram limitadas por ciclo.
- Adicionados medidores compactos de **CPU** e **RAM** na barra superior, atualizados a cada 2 segundos.
- As métricas agregam o processo principal e os processos filhos do WebView2, além de expor threads, requests ativos, fila TX e uptime no tooltip.


## v1.6.14 - 2026-09-25

- Release de teste somente **Windows x64 Portable**.
- O pipeline de recepção APRS foi consolidado em **uma única conexão/transação SQLite por pacote**.
- `aprs_log`, `packets`, `topology_edges/events` e `stations/tracks` deixam de abrir e confirmar transações independentes para o mesmo RX.
- Mantido o housekeeping periódico da v1.6.13, sem varreduras completas a cada pacote.
- Transações RX acima de 250 ms passam a ser registradas em `diagnostics.log`.
- Objetivo: reduzir amplificação de escrita, CPU e indisponibilidade do backend local.


## v1.6.13 - 2026-09-25

- Release de teste somente **Windows x64 Portable**.
- Removidas as consultas de retenção pesadas executadas a cada pacote recebido em `packets`, `aprs_log` e `topology_events`.
- Housekeeping passa a ocorrer em lotes de aproximadamente **1.000 novos registros** ou após **5 minutos**, usando corte por chave primária.
- Pollings pesados da interface foram desacelerados e passam a consultar mapa, mensagens, estações e log principalmente quando a aba correspondente está ativa.
- Mantida a instrumentação diagnóstica para registrar requests lentos, SQLite lento e thread dumps caso o backend ainda fique indisponível.


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
