# Backlog

## Concluído na v1.6.1

- atualização OTA com preferências configuráveis;
- verificação automática da Release a cada 5 minutos;
- mensagens longas sem marcadores visíveis de parte;
- aba **Análise** com métricas e rankings;
- período **Completo** da topologia;
- favoritos com estrela amarela;
- filtro **Não lidas** em Mensagens;
- botão **Mostrar log** no popup da estação;
- legenda de linhas no Mapa;
- animação inicial de tráfego APRS;
- som/destaque visual de atividade.

## Concluído na v1.6.2

- **Replay da Rede** com timeline arrastável, histograma/densidade de tráfego, seek, intervalo personalizado e velocidades de 0,25x a 20x.
- Controles de replay/animação movidos para a **parte inferior do Mapa**.
- Removido **Animar período** da aba Análise.
- Pacotes multi-hop podem percorrer múltiplos enlaces simultaneamente.
- Som, notificação e destaque visual limitados às estações visíveis no enquadramento/zoom atual.
- Ondas/círculos concêntricos animados ao redor do marcador da estação que transmite.
- Indicador **RX/TX** de atividade de tráfego na barra superior.
- Legenda do Mapa sincronizada com as **cores e espessuras** configuradas.
- Correção da **espessura da topologia** refletindo no Mapa.
- Botão **Ver logs** no popup da estação, abrindo o Log filtrado pelo indicativo/SSID.
- Um único botão **Salvar configuração** no rodapé da aba Configuração.
- Confirmação visual após salvar e proteção ao trocar de aba com alterações pendentes.
- **Auto-update desativado**; o cliente somente informa quando existe uma versão nova.
- Verificação de versão com timeout, recuperação automática e sem manter falhas presas em cache.
- Popup de **novidades da versão** exibido uma única vez após atualização.
- Release gerada somente para **Windows x64**: Setup + Portable, sem nova documentação PDF, Linux ou macOS.

## Concluído na v1.6.4

- Corrigido o envio na aba **Mensagens** pelo botão **Enviar** e pela tecla **Enter**.
- Corrigido o **filtro por origem** na aba Mensagens.
- Corrigido o **Replay da Rede** para voltar a mostrar os pacotes trafegando entre os nós, além do realce das estações.
- Adicionado rastro visual ao pacote animado para destacar o enlace em uso.
- Mantida a animação das estações móveis com tracklog progressivo.
- Incluído teste de regressão para impedir que o replay volte a exibir apenas o *highlight* das estações.
- Release somente **Windows x64 Portable**, sem instalador e sem PDF.

## Concluído na v1.6.7

- Gerada versão **Linux x86_64** nos formatos **TAR.GZ, AppImage e DEB**.
- Aplicadas ao build Linux as correções acumuladas das versões 1.6.4 a 1.6.6.
- Corrigida a aplicação da **logo APRS oficial** na interface e no ícone Linux.
- Adicionados smoke tests em **Ubuntu 22.04** e **Ubuntu 24.04**.
- Release somente Linux, sem Windows, macOS ou PDF.

## Concluído na v1.6.8

- Corrigido o travamento no envio de mensagens com **fila assíncrona de transmissão APRS**.
- Adicionada **deduplicação** para impedir múltiplos envios após cliques repetidos.
- Botão **Enviar** é temporariamente bloqueado enquanto a mensagem entra na fila.
- Ao fechar a aplicação, filas pendentes são canceladas e não são reenviadas na próxima abertura.
- Adicionada manutenção leve de encerramento com **PRAGMA optimize** e checkpoint do WAL do SQLite.
- Serviços, conexão APRS-IS e worker de transmissão são encerrados de forma controlada.
- Release para **Windows x64 e Linux x86_64**, sem macOS e sem PDF.

## Consolidado na v1.6.9

- Consolidada a correção do travamento de mensagens com **fila assíncrona e deduplicação**.
- Corrigido o teste legado que ainda exigia a logo APRS oficial e bloqueava os builds.
- Mantida a logo estável anterior no empacotamento até a imagem oficial ser reintegrada com validação.
- Release para **Windows x64 e Linux x86_64**, sem macOS e sem PDF.

## Preparado para a v1.6.10

- Release completa com **Windows x64 Setup + Portable**.
- Release Linux x86_64 em **TAR.GZ, AppImage e DEB**.
- Release macOS em **ARM64 e Intel x86_64 (DMG)**.
- **Manual PDF versionado** gerado e validado no workflow.
- Aplicação dos patches acumulados também aos builds macOS e ao ambiente de captura do manual.
- Correção do pipeline do ícone Windows para não depender do JPEG oficial inválido.

## Pendências para próximas versões

- **Mapa — botões de queries no popup da estação**
  - Ao clicar em uma estação no Mapa, incluir no popup uma área **Diagnóstico / Queries APRS**.
  - Adicionar botões de ação rápida para, no mínimo: **Posição**, **Status**, **Ouvidos**, **Ping/ACK** e **Trace**.
  - As ações devem usar automaticamente o indicativo/SSID da estação selecionada como destino.
  - Mostrar no próprio popup ou em painel associado o andamento da consulta e a última resposta recebida.
  - O botão **Trace** deverá integrar o resultado à visualização do Mapa, destacando os hops/digipeaters identificados quando houver dados suficientes.
  - O botão **Ping/ACK** deverá mostrar RTT e timeout/perda sem confundir esse recurso com a query `PING?`/trace definida pelo APRS.
  - Se uma query não for suportada ou não houver resposta, indicar isso de forma explícita sem bloquear o restante da interface.


- **Uso de queries APRS em outras estações**
  - Permitir enviar queries APRS para qualquer estação selecionada, sem exigir que o usuário escreva manualmente o pacote TNC2.
  - Oferecer ações prontas para **Consultar posição**, **Consultar status**, **Ouvidos diretamente**, **Verificar se ouviu outra estação**, **Objetos**, **Trace** e demais queries suportadas.
  - Exibir o estado da operação como **Query enviada**, **Resposta recebida**, **Sem resposta/timeout** ou **Não suportada**, quando isso puder ser determinado.
  - Medir e exibir o tempo entre envio e resposta quando aplicável.
  - Manter histórico por indicativo com data/hora, query enviada, resposta recebida e tempo de resposta.
  - Para **Ping**, diferenciar claramente o trace/query APRS de um **Ping por mensagem com ACK**, permitindo medir RTT e perda de confirmações.
  - Ao consultar uma estação via APRS-IS, informar que a entrega até RF depende de IGate/roteamento e que nem toda estação implementa todas as queries.


- **Diagnóstico APRS — queries, Ping/Trace e respostas automáticas**
  - Adicionar ferramentas para enviar **queries APRS padronizadas** a uma estação a partir do mapa/Estações/Análise, incluindo consulta de **posição**, **status**, **estações ouvidas diretamente** e recursos equivalentes a **trace/ping** quando suportados pelo equipamento remoto.
  - Implementar um **Ping por mensagem APRS com ACK**, medindo o tempo entre envio e confirmação e exibindo RTT, timeout/perda e histórico recente por indicativo.
  - Implementar visualização de **APRS Trace** no mapa quando a resposta/caminho permitir identificar os digipeaters/IGates observados, mostrando origem, intermediários e destino sem inventar hops não presentes no pacote.
  - Adicionar ação **“Diagnosticar estação”** no popup/menu contextual, reunindo Ping/ACK, consultas APRS e trace em uma interface única.
  - Registrar as queries e respostas no Log/Análise para permitir histórico de diagnóstico e estatísticas de tempo de resposta.
  - **Responder queries recebidas:** preparar o cliente para reconhecer queries APRS endereçadas ao próprio indicativo e despachá-las por um handler dedicado, separado do fluxo de mensagens/ACK.
  - Criar uma camada de **query dispatcher** extensível, mapeando cada comando suportado para sua função de resposta, de forma que novas queries possam ser adicionadas sem alterar o parser principal.
  - Incluir inicialmente suporte de resposta para **posição** e **status**, usando os dados já configurados da estação; preparar interfaces para **direct heard/últimos ouvidos**, trace e outras queries padronizadas.
  - Validar destino pelo **indicativo completo com SSID** e aceitar apenas queries destinadas à própria estação, evitando responder a tráfego genérico ou de terceiros.
  - Gerar respostas APRS no formato correto para cada query e transmitir pelo mesmo pipeline TX controlado do cliente, com registro no Log como resposta automática.
  - Adicionar **rate-limit por origem e por tipo de query**, deduplicação de requests repetidos e proteção contra loops/flood.
  - Adicionar opção em Configurações para **habilitar/desabilitar respostas automáticas a queries**, com padrão conservador, além de opção futura para habilitar individualmente cada tipo de resposta.
  - Registrar no diagnóstico: query recebida, origem, tipo reconhecido, resposta enviada, ignorada ou rejeitada e motivo.
  - Adicionar testes automatizados cobrindo parsing da query, validação do destinatário, resposta correta, rate-limit, query desconhecida e ausência de transmissão quando desconectado/não verificado.
  - Não confundir **ACK de mensagem** com query APRS: manter o ACK existente e tratar queries em um caminho próprio do parser/serviço.


- **Atualização/instalação — fechar versão anterior antes de instalar**
  - Ao iniciar a instalação de uma nova versão, detectar se o **PT2VHF APRS Client** anterior ainda está em execução.
  - Se estiver aberto, solicitar/forçar o encerramento controlado da aplicação antes de substituir arquivos, evitando falha de instalação por arquivo em uso.
  - Preferir encerramento gracioso primeiro, permitindo fechar conexão APRS-IS, workers, filas e banco SQLite corretamente; se não encerrar dentro de um timeout curto, oferecer/usar encerramento forçado.
  - Após a instalação concluir com sucesso, **abrir automaticamente a nova versão**.
  - No Windows Setup, integrar esse comportamento ao instalador; aplicar equivalente nas plataformas em que o empacotador permitir comportamento semelhante.
  - Não encerrar processos que não pertençam ao PT2VHF APRS Client; identificar a instância com segurança por executável/processo.


- **Atualizações — download direto da versão correta pela caixa de versão**
  - Quando houver uma versão nova disponível, tornar a **caixa/indicador de versão na barra superior clicável** para iniciar o download diretamente da Release oficial no GitHub.
  - Detectar automaticamente a **plataforma e arquitetura em uso** e escolher o artefato correspondente: **Windows x64**, **Linux x86_64** ou **macOS ARM64/Intel x86_64**.
  - No Windows, preservar também o tipo de distribuição quando possível: **Portable baixa Portable** e **instalação via Setup baixa o Setup**.
  - No Linux, selecionar o formato apropriado da instalação atual quando identificável (**AppImage, DEB ou TAR.GZ**); se não for possível determinar com segurança, apresentar as opções Linux disponíveis sem escolher arbitrariamente.
  - No macOS, selecionar automaticamente o DMG compatível com a arquitetura (**Apple Silicon ARM64** ou **Intel x86_64**).
  - O download deve apontar diretamente para o **asset da versão mais recente publicada no GitHub Releases**, sem exigir que o usuário navegue manualmente pela página da Release.
  - Manter o comportamento de **somente baixar/avisar**, sem instalação automática silenciosa; a instalação continua sob controle do usuário.
  - Exibir estado de download/progresso e mensagem clara em caso de falha, asset ausente ou incompatibilidade detectada.


- **Aba Análise — ranking das estações que mais conversaram**
  - Adicionar um painel com o ranking das **estações com maior volume de conversas/mensagens** registradas pelo cliente.
  - Ordenar em ordem decrescente, da estação com mais interações para a com menos.
  - Exibir pelo menos **Indicativo**, **quantidade de mensagens/interações** e **percentual sobre o total de conversas registradas**.
  - Contabilizar as interações por estação usando as mensagens armazenadas no banco local.
  - Permitir diferenciar, quando útil, **mensagens enviadas**, **recebidas** e **total de interações**.


- **Aba Análise — ranking de versões dos clientes APRS**
  - Adicionar um painel mostrando as **versões dos clientes/aplicativos APRS detectados nas estações recebidas**.
  - Agrupar por **cliente + versão** e exibir a quantidade de estações únicas usando cada versão.
  - Ordenar da **versão/cliente mais usada para a menos usada**.
  - Exibir também o **percentual** sobre o total de estações em que foi possível identificar o software/versão.
  - Manter uma categoria **Não identificado** para estações sem informação suficiente, separada do ranking principal.
  - Evitar contar repetidamente a mesma estação; considerar a versão mais recente observada por indicativo.


- **Barra superior — indicadores de CPU e memória em tempo real**
  - Adicionar na barra superior indicadores compactos do consumo do processo do **PT2VHF APRS Client**.
  - Exibir **CPU (%)** em tempo real.
  - Exibir **memória RAM** usada pelo processo, em **MB** e, quando possível, também em **%**.
  - Atualização sugerida a cada **2 segundos**, com baixo overhead.
  - Usar apresentação compacta estilo gauge/medidor, com faixas visuais de normal, atenção e crítico.
  - Tooltip opcional com detalhes adicionais: quantidade de threads, requests HTTP ativos, tamanho da fila TX e uptime.
  - O indicador deve servir também como recurso permanente de diagnóstico de estabilidade e desempenho.
  - **Implementado para teste na v1.6.15:** gauges compactos de CPU e RAM na barra superior, com atualização a cada 2 segundos.
  - Para refletir corretamente o consumo real do Portable, calcular CPU/RAM do **processo principal + processos filhos do WebView2**, e não apenas do executável Python, para evitar leitura enganosa.


- **Portátil — aplicação deixa de responder após alguns minutos (prioridade alta)**
  - **Teste v1.6.16 topologia indexada:** corrigida a causa confirmada no diagnóstico: JOINs de `/api/topology` deixam de usar `UPPER()`, consultas concorrentes são coalescidas/cacheadas, há limite interno de 2,5 s e o frontend não inicia mais múltiplos `loadTopology()` simultâneos. Validar CPU, envio de mensagens, salvamento de Configuração e estabilidade prolongada.
  - **Resultado inicial da v1.6.16:** consumo de CPU observado em aproximadamente **1%** nos testes iniciais, contra ~55% na v1.6.15. É um forte indício de que a consulta de topologia era o principal gargalo de CPU. Manter validação prolongada antes de encerrar o incidente.
  - **Teste v1.6.15 Mapa/single-flight:** removido o `loadMapData()` disparado por `stationActivity()`, adicionada trava para impedir refreshes completos concorrentes e limitado o processamento visual de rajadas. Esta versão também implementa os gauges de CPU/RAM para observar o comportamento em tempo real.
  - **Resultado da v1.6.15:** a CPU deixou de crescer indefinidamente, mas estabilizou em aproximadamente **55%** e a aplicação ainda **congelou**. Isso indica que o fan-out do Mapa era parte do problema, porém permanece uma carga sustentada anormal ou um bloqueio subsequente.
  - **Mensagens na v1.6.15:** a aplicação trava menos, porém `POST /api/messages/send` ainda excede 10 s e a mensagem não entra na fila. O caminho de envio ainda faz `db.get_config()` e `db.add_outgoing_message_parts()` de forma síncrona antes de responder ao HTTP; portanto, qualquer contenção do writer SQLite bloqueia diretamente o botão Enviar.
  - **Diagnóstico confirmado pelo `diagnostics.log` da v1.6.15:** a causa imediata do congelamento é `GET /api/topology`. Várias threads do Waitress ficam simultaneamente presas em `database.list_topology_edges()` por períodos de aproximadamente **10 a 19 minutos**. Foram observadas execuções de ~601 s, ~1.044 s, ~1.066 s e ~1.122 s. Com 7–8 workers ocupados por essa mesma consulta, requests normais ficam aguardando na fila do servidor e o frontend estoura o timeout de 10 s.
  - O próprio `POST /api/messages/send` não é lento quando finalmente chega a um worker: no log ele conclui em cerca de **15–32 ms**. Portanto, o timeout visto na interface é principalmente **espera na fila do Waitress por falta de worker livre**, e não lentidão da rotina de envio.
  - **Causa provável dentro de `list_topology_edges()`:** os JOINs usam `UPPER(s1.callsign)=UPPER(e.source)` e `UPPER(s2.callsign)=UPPER(e.target)`, impedindo o uso direto do índice/PRIMARY KEY de `stations.callsign` e provocando varreduras muito caras. Como indicativos e arestas já são normalizados em maiúsculas na gravação, trocar por igualdade direta permite lookup indexado. Adicionar também proteção single-flight para `loadTopology()`/rota de topologia e índices auxiliares se necessários.
  - Esta evidência desloca a prioridade para o backend/SQLite: implementar **writer RX dedicado com fila e commits em lote**, deixando operações interativas (Configuração/Mensagens) fora da disputa contínua com o fluxo de recepção. Considerar fila de prioridade ou flush curto (ex.: 50 pacotes ou 100–250 ms) e métricas de profundidade/latência da fila.
  - Próximo diagnóstico deve separar **backend Python/SQLite** de **WebView2/Leaflet**. Testar modo navegador externo (`--browser`) e/ou uma build de diagnóstico com renderização/polling do Mapa desativados para comparar CPU e estabilidade.
  - Se o congelamento ocorrer mesmo sem WebView/Mapa, priorizar fila RX + writer SQLite em lotes; se desaparecer, priorizar redução de trabalho do Leaflet/WebView2 e do replay/atividade visual.
  - **Teste v1.6.14 transação única RX:** o pipeline normal de recepção foi consolidado em uma única transação SQLite por pacote, agrupando log RX, histórico de pacotes, topologia e atualização de estação/track. Objetivo: reduzir a amplificação de escrita e impedir que o tráfego APRS monopolize CPU/banco e faça as rotas HTTP deixarem de responder. Manter o item aberto até teste prolongado em uso real.
  - **Resultado da v1.6.14:** o travamento persiste, com **CPU ainda alta**, e o salvamento de Configurações voltou a falhar com timeout em **`/api/config`**. A transação única por pacote não resolveu a causa raiz.
  - Próxima hipótese prioritária: mesmo com uma transação por pacote, o RX continua fazendo **um commit SQLite por pacote recebido**. Sob tráfego alto isso pode manter o writer quase continuamente ocupado e provocar starvation das escritas HTTP. Avaliar writer dedicado com **fila e commits em pequenos lotes** (por quantidade e/ou janela de tempo), com backpressure e métricas de profundidade da fila.
  - Verificar também o custo do WebView/Leaflet e das animações de tráfego; quando o replay/live não estiver ativo, nenhum loop de animação deve consumir CPU continuamente.
  - **Nova evidência crítica:** a CPU começa a subir **imediatamente após iniciar o app** e continua aumentando a cada segundo.
  - **Hipótese prioritária de fan-out no Mapa:** `pollTrafficEvents()` percorre cada evento recebido e chama `stationActivity()`; quando a estação ainda não tem marcador, `stationActivity()` dispara `loadMapData()` sem trava de concorrência. Um lote de até 500 eventos pode, portanto, abrir dezenas/centenas de recargas completas simultâneas do mapa. Estações sem posição nunca ganham marcador e podem repetir esse ciclo indefinidamente.
  - Corrigir removendo completamente o `loadMapData()` de `stationActivity()`, adicionando `mapLoadBusy`/single-flight ao refresh do mapa, limitando o processamento visual por ciclo e cancelando/ignorando trabalho de mapa quando a aba Mapa não estiver ativa.
  - **Teste v1.6.13 CPU/SQLite:** removido o housekeeping pesado executado em cada pacote APRS. A retenção de `packets`, `aprs_log` e `topology_events` agora roda em lotes e usa corte pela chave primária. Pollings pesados também foram reduzidos/condicionados à aba ativa. Validar consumo de CPU e estabilidade prolongada antes de considerar o problema encerrado.
  - **Resultado parcial da v1.6.13:** durante teste de envio de mensagem, a interface exibiu **“O backend local não respondeu em 10 segundos (/api/messages/send)”**. Portanto, a otimização de CPU/housekeeping não eliminou o travamento do envio. Preservar e analisar o `diagnostics.log` desta execução para identificar a thread/request bloqueado no momento do timeout.
  - **Configuração também continua afetada na v1.6.13:** o usuário não consegue concluir **Salvar configuração**. Tratar como evidência de indisponibilidade geral do backend, não apenas falha da rota de mensagens; verificar no diagnóstico se `POST /api/config` também permanece ativo/bloqueado durante o travamento.
  - **Travamento com CPU quase saturada na v1.6.13:** confirmado novo congelamento acompanhado de uso de CPU próximo do máximo. A v1.6.13 reduziu o housekeeping, mas o pipeline RX ainda abre/fecha e confirma múltiplas transações SQLite por pacote (`aprs_log`, `packets`, `topology`, `stations/tracks`). Investigar forte amplificação de escrita e possível starvation das rotas HTTP que também precisam escrever no banco. Próxima correção candidata: processar cada pacote recebido em uma única transação SQLite ou por writer dedicado/fila, em vez de várias conexões/commits independentes.
  - **Teste v1.6.12 diagnóstico:** instrumentação adicionada para registrar requests ativos, duração/endpoint/thread, operações SQLite lentas, health-check interno e dump automático de threads quando o servidor local parar de responder. O log fica em `diagnostics.log` na pasta de dados.
  - **Teste v1.6.11:** preparada correção experimental para reduzir contenção SQLite, impedir pollings sobrepostos, limitar chamadas HTTP a 10 s e gravar mensagens multipartes em uma única transação. Manter este item aberto até validação em uso real.
  - **Resultado do teste v1.6.11:** ocorreu a mensagem **“O backend local não respondeu em 10 segundos.”**. Portanto, o timeout do frontend funcionou, mas a causa raiz permanece: o servidor HTTP local fica indisponível por mais de 10 s.
  - **Configuração também afetada na v1.6.11:** o botão **Salvar configuração** não conclui a gravação quando o backend entra nesse estado. Isso confirma que a falha não está restrita a Mensagens; a rota `POST /api/config` também fica sem atendimento.
  - Tratar a v1.6.11 como **não resolvida**. O próximo diagnóstico deve identificar qual rota/request ocupa as threads do Waitress no momento do travamento e se há esgotamento do pool de workers.
  - Instrumentar cada request com início/fim/duração, endpoint, thread e status; incluir contador de requests ativos e dump das threads quando o health-check detectar atraso.
  - Quando o backend entrar em timeout, suspender temporariamente os pollings automáticos para evitar que novos requests agravem o esgotamento das threads.
  - Na versão **Portable**, após alguns minutos aberta, a interface aparenta continuar visível, mas as operações que dependem do backend deixam de responder.
  - **Reprodutibilidade confirmada:** ao fechar e abrir novamente, a aplicação volta a funcionar normalmente por algum tempo e depois trava de novo.
  - **Confirmação pelo navegador:** quando ocorre o travamento, abrir a interface pelo navegador ou tentar atualizar/recarregar a página também não responde. Isso indica indisponibilidade do **servidor HTTP local/backend**, e não apenas travamento do WebView ou da janela portátil.
  - Sintomas observados: **não conecta ao APRS-IS**, **não verifica nova versão**, **não salva Configurações** e outras chamadas da interface ficam sem conclusão.
  - O padrão temporal sugere acúmulo progressivo de requests/threads/conexões, lock persistente, polling sobreposto ou recurso não liberado, e não apenas erro pontual de uma tela.
  - Priorizar investigação de **esgotamento das 8 threads do Waitress** por requests bloqueados e de contenção SQLite. O uso atual de `PRAGMA journal_mode=WAL` a cada nova conexão deve ser removido do caminho normal das requisições e executado somente na inicialização/migração do banco.
  - Investigar travamento/indisponibilidade do servidor HTTP local, esgotamento ou bloqueio das threads do Waitress, chamadas `fetch` sem timeout, pollings concorrentes, contenção/lock do SQLite e interação com o WebView.
  - Instrumentar watchdog/health-check interno do backend e registrar último request iniciado/concluído, threads ativas, fila de requests, conexões SQLite abertas/tempo de espera e exceções não tratadas.
  - Evitar que uma operação lenta bloqueie as demais rotas da aplicação.
  - Adicionar timeout e cancelamento às chamadas HTTP do frontend, com feedback explícito quando o backend local não responder.
  - Criar teste de estabilidade prolongada da versão portátil, mantendo a aplicação aberta com recepção APRS, atualização de mapa/mensagens e ações de Configuração por vários minutos.


- **Configurações — falha de salvamento com banco antigo/inconsistente**
  - O problema desapareceu após apagar o banco local e iniciar com um banco novo.
  - Isso indica possível incompatibilidade de migração, esquema antigo, registro de configuração inconsistente ou dado legado inválido, e não necessariamente falha do botão de salvar em uma instalação limpa.
  - Investigar a abertura de bancos existentes após upgrade e validar/migrar automaticamente a tabela de configuração.
  - Se houver dado inválido ou coluna ausente, corrigir/migrar sem exigir que o usuário apague todo o banco.
  - Revisar também o fluxo do `saveConfigFooterButton` e do modal **Salvar e sair** para sempre exibir erro explícito caso a persistência falhe.
  - Adicionar teste de regressão cobrindo upgrade com banco de versão anterior → alterar configuração → salvar → persistir e navegar.


- **Logo APRS oficial ainda não aplicada corretamente**
  - A imagem enviada pelo usuário ainda precisa ser incorporada com um arquivo de imagem válido no repositório.
  - Atualizar cabeçalho/interface, favicon, ícones Windows/Linux e demais pontos visuais sem quebrar o build.
  - Adicionar validação de integridade da imagem no pipeline para evitar novos empacotamentos com arquivo corrompido.

Novas demandas devem continuar na série **1.6.x** até indicação explícita para avançar para **1.7**.


## Consolidado na v1.6.17

- Release completa multiplataforma baseada nas correções testadas até a v1.6.16.
- CPU inicial observada em torno de 1% após a correção da consulta de topologia, contra aproximadamente 55% na v1.6.15.
- Mantida a instrumentação diagnóstica e os gauges de CPU/RAM para acompanhar estabilidade em uso real.
- Publicação prevista para Windows, Linux, macOS e Manual PDF.


## Concluído na v1.6.18

- Queries APRS direcionadas pelo popup da estação: posição, status, ouvidos e trace.
- Ping/ACK com RTT e timeout.
- Trace visual no mapa com hops conhecidos, sem inventar posição para hops desconhecidos.
- Histórico local das queries e respostas.
- Estrutura de resposta automática a APRSP/APRSS/APRST/PING com configuração e rate-limit.
## Próximas melhorias — Análise e idioma

- **Aba Análise — estatísticas de versões de clientes APRS:** adicionar um bloco com a distribuição das versões/clientes observados, ordenado do **mais usado para o menos usado**. Exibir pelo menos nome do cliente/versão e quantidade de ocorrências; quando houver base suficiente, mostrar também percentual sobre o total identificado. Manter uma categoria separada para tráfego em que o cliente/versão não puder ser determinado, sem inferir dados ausentes.
- **Seletor de idioma no topo:** corrigir a regressão em que a opção de troca de idioma deixou de aparecer na barra superior. Restaurar o seletor **PT/EN com bandeiras**, mantendo **PT-BR como padrão** e preservando a seleção do usuário.

