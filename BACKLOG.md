# Backlog

## Política de versões a partir da próxima geração

- A próxima versão completa será **v1.7**.
- As versões seguintes desta linha usarão numeração incremental **v1.7.1, v1.7.2, v1.7.3...**.
- Não publicar a versão intermediária **v1.6.25**.

## Concluído na v1.7.22

- **Mapa → Camadas → Clima:** radar meteorológico como sobreposição independente do mapa-base.
- **Radar de precipitação:** atualização periódica a partir do quadro mais recente disponível no RainViewer.
- **Configuração:** controle persistente de opacidade da camada de clima.
- **Popup da estação:** altura limitada, rolagem interna e proteção adicional de auto-pan/keepInView para evitar corte no topo.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.7.21

- **Hover de enlaces:** painel contextual fixo com origem/destino, tipo RF ou Internet/APRS-IS, direção, pacotes e período observado.
- **Hover de tracklog:** painel com início/fim, duração, distância, velocidade média/máxima, posições, pontos inicial/final, caminhos APRS, digipeaters/iGates e métricas RF quando disponíveis.
- **Histórico enriquecido:** novos pontos de tracklog armazenam path, pacote bruto, RSSI e SNR quando fornecidos.
- **Download de atualização:** o mesmo pacote é sobrescrito ao baixar novamente, sem criar duplicatas numeradas.
- **Housekeeping do updater:** após inicialização bem-sucedida da versão instalada, remove versões/pacotes antigos e downloads incompletos da pasta temporária.

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

- **Builds — Linux ARM64**
  - **Windows ARM64 foi incorporado na v1.7.7** com Setup e Portable nativos; manter apenas acompanhamento de compatibilidade/estabilidade.
  - Adicionar geração oficial de artefatos **Linux ARM64**, priorizando **TAR.GZ** e, quando suportado pelo pipeline, também **AppImage** e **DEB arm64**.
  - Manter o build nativo **macOS ARM64** já existente e garantir paridade funcional com Intel x86_64.
  - Atualizar o mecanismo de atualização automática para Linux ARM64 quando os artefatos correspondentes estiverem disponíveis.
  - Não permitir atualização cruzada entre arquiteturas.
  - Validar banco SQLite, WebView/interface, mapa, APRS-IS, updater e empacotamento antes de considerar Linux ARM64 estável.
  - Documentar claramente no README/Release qual pacote deve ser usado em cada arquitetura.
- **Portátil — validação prolongada de estabilidade**
  - Manter acompanhamento em uso real do Windows Portable após as correções de CPU/topologia/SQLite já incorporadas.
  - Registrar qualquer novo congelamento com diagnostics.log e verificar se há regressão no backend, WebView2, mapa ou contenção SQLite.
  - Considerar encerrado somente após teste prolongado sem aumento anormal de CPU e sem timeout nas rotas interativas.

- **Configurações — compatibilidade com banco antigo/inconsistente**
  - Validar upgrade com banco de versão anterior, alterar configuração, salvar, reiniciar e confirmar persistência.
  - Garantir migração automática de schema/defaults sem apagar mensagens, estações, logs ou tracklogs.
  - Adicionar/confirmar teste de regressão para banco antigo ou parcialmente migrado.

- **TNC / RF — interface de conexão, Digipeater e iGate inteligente**
  - Criar uma área própria de **TNC / Rádio** na Configuração e um indicador de estado na interface principal.
  - Suportar inicialmente **KISS TNC** por **porta serial** e **KISS TCP**, permitindo uso com TNCs físicos e softwares como Dire Wolf; manter arquitetura extensível para outros protocolos, como AGWPE, sem acoplar o núcleo APRS a um único fabricante.
  - Na conexão serial, permitir selecionar porta COM/tty, baud rate, reconexão automática e identificação amigável do TNC; no modo TCP, configurar host, porta, timeout e reconexão.
  - Implementar **detecção/listagem de portas seriais**, teste de conexão, status Conectado/Desconectado/Reconectando, contadores RX/TX, último frame e diagnóstico de erro.
  - Disponibilizar **monitor TNC** com frames AX.25/APRS recebidos e transmitidos, timestamp, origem, destino, path, PID/tipo quando disponível e representação TNC2 decodificada.
  - Manter **APRS-IS e TNC independentes**: o cliente pode operar somente Internet, somente RF ou em modo híbrido.
  - Permitir selecionar o papel RF: **Somente monitor**, **Estação local**, **Digipeater**, **iGate RX**, **iGate bidirecional** ou **Digi + iGate**.
  - Separar claramente **recepção RF**, **transmissão RF**, **digipeating** e **gating Internet↔RF**, com chaves independentes e indicação visual explícita quando houver capacidade de transmissão.
  - Antes de habilitar qualquer retransmissão automática, validar indicativo/SSID, configuração de path e parâmetros mínimos; impedir loops e transmissões acidentais causadas por configuração incompleta.

  - **Digipeater APRS**
    - Implementar digipeating compatível com os aliases e regras APRS usuais, incluindo tratamento de **WIDE1-1 / WIDEn-N** conforme perfil configurado.
    - Permitir perfis como **Fill-in**, **Wide/Regional** e **Personalizado**, evitando que um nó fill-in se comporte como digi regional por engano.
    - Implementar **duplicate suppression** por hash/assinatura do frame e janela temporal configurável, evitando repetir o mesmo pacote recebido por caminhos diferentes.
    - Detectar e bloquear **loops**, paths já consumidos, chamadas repetidas indevidamente e frames que excedam limites configurados de hops.
    - Respeitar o path APRS original e registrar no banco a decisão tomada: retransmitido, duplicado, bloqueado por loop, fora de política, TTL expirado ou outro motivo.
    - Aplicar fila de TX com prioridade para **mensagens/ACK/REJ e tráfego útil**, evitando que beacons, telemetria repetitiva ou duplicatas dominem o canal.
    - Permitir limites por origem/tipo de pacote e **rate limit** por estação para conter equipamentos mal configurados sem bloquear toda a rede.
    - Expor métricas de airtime/ocupação quando o TNC ou modem fornecer essa informação; quando não houver métrica real, não inventar utilização de canal.

  - **iGate APRS inteligente**
    - Implementar **RF → APRS-IS** com deduplicação, preservação do pacote original e q-construct adequado ao papel de iGate.
    - Implementar **APRS-IS → RF** de forma restritiva e compatível com a lógica de iGate: transmitir para RF somente quando houver justificativa local, evitando transformar o iGate em retransmissor indiscriminado da Internet.
    - Manter uma tabela de **estações ouvidas por RF**, com última recepção, se foi direta ou via digi, path observado, frequência de atividade e qualidade RF quando disponível.
    - Para mensagens vindas da Internet, considerar elegível para RF principalmente o destinatário **recentemente ouvido na área RF**; manter janela temporal configurável.
    - Evitar retransmitir para RF pacotes que já tenham sido observados localmente, mensagens duplicadas ou tráfego cujo destino não possua presença RF recente.
    - Registrar toda decisão de gating com motivo: gated RF→IS, gated IS→RF, destino não ouvido, duplicado, bloqueado por política, limite excedido ou sem capacidade TX.
    - Permitir modo **RX-only iGate** como opção simples e segura.

  - **Otimização adaptativa baseada em quem fala com quem**
    - Construir um **grafo de interação RF/APRS** usando dados observados: estação de origem, destino das mensagens, digipeaters utilizados, iGate de entrada/saída, paths, ACK/REJ, frequência de contatos e última atividade.
    - Diferenciar claramente **relação observada** de rota física inferida; não assumir enlace RF direto apenas porque duas estações trocaram mensagens via APRS-IS.
    - Manter uma **tabela de vizinhança RF** com estações diretamente ouvidas, estações ouvidas via digi e digis realmente utilizados.
    - Calcular, por período, pares que mais se comunicam, paths efetivamente úteis, redundância, duplicatas, taxa de ACK e tempo de resposta quando mensurável.
    - Usar essa análise para ajustar somente decisões permitidas pelo protocolo: prioridade de fila, supressão de duplicatas, necessidade de gating IS→RF, rate limits e preferência por não repetir tráfego desnecessário.
    - **Não reescrever arbitrariamente paths APRS de terceiros** nem criar roteamento proprietário incompatível com outros digipeaters; a inteligência deve otimizar dentro das regras APRS.
    - Implementar primeiro um modo **Recomendação/Observação**, mostrando o que o sistema faria e por quê; somente depois permitir **Otimização automática**, ativada explicitamente pelo usuário.
    - No modo automático, usar limites conservadores, permitir rollback para perfil fixo e registrar cada decisão no log para auditoria.
    - Se a ocupação de RF aumentar, reduzir automaticamente repetições de baixa prioridade e preservar mensagens, ACK/REJ e tráfego operacional importante.
    - Quando houver múltiplos iGates/digis observados, detectar **redundância saudável** versus repetição excessiva, sem desligar tráfego com base apenas em uma amostra curta.
    - Criar indicadores como **pacotes evitados**, duplicatas suprimidas, mensagens entregues, ACKs observados, tráfego RF economizado e principais pares de comunicação.

  - **Mapa, Estatísticas e diagnóstico**
    - Identificar no Mapa pacotes recebidos diretamente pelo TNC, repetidos pelo digi local, enviados ao APRS-IS e gated da Internet para RF.
    - Exibir no popup/painel da estação se ela foi ouvida **diretamente por RF**, **via digi**, **via APRS-IS** ou por mais de um meio.
    - Adicionar em Estatísticas uma seção **RF / TNC / Digi / iGate** com RX/TX, frames repetidos, duplicatas suprimidas, mensagens gated, principais paths e estações mais ouvidas.
    - Criar uma visualização opcional do **grafo de comunicação**, permitindo ver quem fala com quem e quais digis/iGates participam dos caminhos observados.
    - Integrar o módulo ao diagnóstico existente, incluindo estado do TNC, porta/host (sem dados sensíveis), filas, erros de serial/TCP e últimos eventos de RF.
    - Persistir histórico necessário no SQLite com retenção configurável, evitando crescimento ilimitado do banco.

  - **Segurança operacional e testes**
    - Deixar **TX automático, Digipeater e iGate bidirecional desativados por padrão** em novas instalações; monitor e iGate RX-only podem ser habilitados separadamente.
    - Exigir confirmação explícita ao ativar pela primeira vez qualquer função que transmita automaticamente em RF.
    - Adicionar botão de **parada imediata de TX automático**, sem derrubar a recepção/monitoramento.
    - Validar comportamento com frames gravados/replay antes de testar em RF real.
    - Criar testes de regressão para KISS escaping, AX.25 encode/decode, SSID, paths WIDE, duplicate suppression, loops, filas, ACK/REJ, gating RF→IS e IS→RF.
    - Incluir um **simulador TNC** nos testes para validar cenários de múltiplas estações/digis/iGates sem precisar de rádio físico.
    - Documentar claramente que a operação em RF depende da configuração correta da estação, do equipamento e das regras aplicáveis ao serviço de radioamador.

- **Mapa — painel lateral de estação**
  - Substituir progressivamente o popup grande da estação por um painel lateral fixo, preservando o mapa visível durante a consulta.
  - Exibir Indicativo, última recepção, distância, software/dispositivo, posição, status, favorito, mensagens, Ping, Trace e estações ouvidas.
  - Incluir atalhos para **Mostrar log**, **Enviar mensagem**, **Ping/ACK**, **Trace**, **Posição**, **Status** e histórico de queries.
  - Em telas pequenas, transformar o painel lateral em painel inferior responsivo.
  - Ao trocar de estação, atualizar o mesmo painel sem criar sobreposição adicional no mapa.

- **Mapa — camada Elevação mínima com corte por altitude**
  - Replicar no **PT2VHF APRS Client** o comportamento final validado no **Traffic Analyzer**.
  - Adicionar em **Camadas** uma sobreposição analítica chamada **Elevação mínima**, baseada em dados reais de DEM.
  - Quando ativada, exibir somente o terreno cuja altitude seja **maior ou igual à cota mínima selecionada**; todo o terreno abaixo do limite fica transparente.
  - O controle vertical deve aparecer **somente enquanto a camada Elevação mínima estiver ligada**.
  - Posicionar o controle na **lateral direita do mapa**, centralizado verticalmente, sem depender da camada Relevo sombreado.
  - O slider deve representar altitude: mover para cima aumenta a cota mínima; mover para baixo reduz a cota.
  - Exibir acima do slider o valor atual da cota em metros, por exemplo **1.000 m**.
  - Atualizar imediatamente a área destacada durante o movimento do slider.
  - Usar **3.000 m como limite máximo padrão** do slider.
  - O **campo numérico inferior do próprio controle** deve informar e alterar o **limite máximo do range do slider**, e não a cota mínima atual.
  - Permitir no campo inferior limite configurável de **100 a 9.000 m**; ao mudar o valor, atualizar imediatamente o máximo do slider e a indicação superior da escala.
  - Se o novo limite máximo ficar abaixo da cota mínima atual, ajustar automaticamente a cota ao novo máximo.
  - A altura normal do slider deverá ser de aproximadamente **390 px**; em janelas de menor altura, usar aproximadamente **255 px**, mantendo adaptação responsiva.
  - Manter controle separado de **opacidade** da camada.
  - Persistir a última cota mínima, o limite máximo configurado e a opacidade escolhida.
  - Estações APRS, objetos, tracklogs, enlaces, animações e radar devem permanecer acima da camada de elevação.
  - **Relevo sombreado** deve permanecer independente da camada Elevação mínima; ligar somente o relevo sombreado não deve exibir o slider.
  - A implementação deve usar dados reais de elevação/DEM; não inferir altitude a partir do mapa topográfico visual.

- **Mapa — paridade de mapas/camadas com o Traffic Analyzer**
  - Espelhar no PT2VHF APRS Client a organização usada no Traffic Analyzer: **mapa-base** separado de **Camadas**.
  - Mapas-base disponíveis: **Ruas / OpenStreetMap (OSM)**, **Topográfico**, **Claro**, **Escuro** e **Satélite**.
  - Manter **Radar meteorológico (RainViewer)** dentro do menu **Camadas**, independente do mapa-base, com ativação/desativação própria e atualização periódica.
  - **Não incluir camada de raios/lightning**, pois a integração considerada não oferece cobertura útil para o Brasil e é voltada aos EUA.
  - Preservar o controle de **opacidade do radar** em Configuração.
  - Adicionar inicialmente ao APRS Client os mapas-base **Claro** e **Escuro**, que ainda não existem nele, mantendo OSM, Topográfico e Satélite.
  - Não misturar mapas-base com sobreposições: **Claro/Escuro/Satélite** são mapas-base; **Radar** é camada.
  - Manter a estrutura de Camadas preparada para receber novas sobreposições posteriormente, sem alterar novamente a barra principal.

- **Mapa — consolidar controles na barra superior**
  - Aproveitar a nova barra acima do mapa para reunir os controles usados com maior frequência.
  - Avaliar incluir seletor de mapa/base cartográfica, mostrar/ocultar tracklogs, mostrar/ocultar enlaces, animações, som e outros controles rápidos.
  - Manter os controles menos usados em um menu **Mais ▾**, evitando poluir a barra.
  - Garantir que nenhum controle volte a ficar sobreposto ao canvas do mapa ou à legenda.

- **Busca rápida — localizar estação por indicativo**
  - Adicionar campo de busca rápida por indicativo, com filtragem caractere por caractere.
  - Aceitar indicativo completo ou parcial, incluindo SSID.
  - Ao selecionar uma estação, abrir a aba **Mapa**, centralizar o marcador e aplicar um nível de zoom adequado.
  - Integrar a seleção ao futuro painel lateral da estação.
  - Priorizar favoritos e correspondências exatas nas sugestões.

- **Estatísticas — qualidade da rede APRS**
  - Adicionar painel específico de qualidade/saúde da rede observada.
  - Exibir taxa de pacotes duplicados, tráfego **RF × APRS-IS**, estações únicas por hora/dia e distribuição por tipo de pacote.
  - Incluir mensagens com ACK/sem ACK, RTT médio/mediano do Ping, estações novas no período e estações que deixaram de aparecer.
  - Respeitar o período selecionado em Estatísticas e permitir análise **Completo, 1 h, 6 h, 24 h e 7 dias**.
  - Evitar que telemetria de alta frequência distorça indicadores de atividade humana.

- **Exportação — CSV e GeoJSON**
  - Manter como próxima etapa a exportação tabular em **CSV** e geográfica em **GeoJSON**.
  - Respeitar período e filtros ativos, preservando timestamp, indicativo, origem e atributos úteis.
  - Garantir compatibilidade com Excel, QGIS e outras ferramentas de análise.

- **Estatísticas — comparação entre períodos**
  - Permitir comparar o período atual com o período imediatamente anterior de mesma duração.
  - Exemplos: **últimas 24 h × 24 h anteriores** e **últimos 7 dias × semana anterior**.
  - Mostrar variação absoluta e percentual de estações ativas, mensagens, tráfego, enlaces, digipeaters e iGates.
  - Destacar novos enlaces, estações novas e estações que desapareceram.
  - Evitar apresentar variação percentual quando a base anterior for zero; nesse caso, indicar **novo** ou equivalente.

- **Diagnóstico — saúde da aplicação e pacote de suporte**
  - Criar uma área de diagnóstico em **Ajuda** ou seção própria.
  - Exibir integridade do banco SQLite, tamanho do banco, estado da conexão APRS-IS, WebView, CPU, RAM, filas de mensagens, serviços/threads principais e espaço em disco.
  - Adicionar botão **Gerar pacote de diagnóstico**.
  - O pacote deve incluir logs e informações técnicas úteis, removendo ou mascarando dados sensíveis antes da geração.
  - Incluir versão da aplicação, plataforma, arquitetura, caminho do banco, status das migrações e erros recentes.
  - Facilitar o envio desse ZIP em casos de travamento ou comportamento anormal.

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
## Concluído na v1.6.19

- **Aba Estatísticas:** bloco de clientes/versões APRS por TOCALL mais recente de cada estação, ordenado do mais usado para o menos usado, com quantidade, percentual e Não identificado.
- **Mapa / queries:** resultado da última query passa a ficar claramente visível no popup, com status, RTT, resposta, Trace textual e indicação de hops localizados.
- **Mapa / histórico:** botão para visualizar o histórico de queries daquela estação e restauração da última resposta ao reabrir o popup.
- **Idiomas:** restaurado o controle de idioma na barra superior, com Português/Brasil e English/Inglaterra, persistindo a escolha.
- **Queries de posição:** resposta exibida passa a incluir latitude e longitude recebidas.

## Concluído na v1.6.20

- **Estatísticas / clientes:** nomes amigáveis de software/dispositivo pelo snapshot local da base APRS Device Identification, mantendo o TOCALL como referência.
- **Estatísticas / adoção:** Top 20 + linha adicional destacada com a posição real do PT2VHF APRS Client quando estiver fora do corte.
- **Identificação do cliente:** transmissões do aplicativo passam a usar o TOCALL experimental **APZVHF**, permitindo contabilizar instalações observadas.
- **Idioma no topo:** controle compacto mostra somente o idioma atual e abre as duas opções ao clicar; English usa a bandeira da Inglaterra.
- **Mapa / topologia:** qAR/qAO até o IGate passa a ser classificado como RF e desenhado em linha contínua; bancos existentes são migrados automaticamente.

## Concluído na v1.6.21

- **Estatísticas / estações mais ativas:** aba renomeada de Análise para Estatísticas e novo ranking por tráfego útil no período selecionado.
- O ranking exclui telemetria, iGates e digipeaters; essas infraestruturas continuam nas seções dedicadas.
- Exibe posição, indicativo, pacotes válidos e percentual sobre o total elegível.
- Incluído teste automatizado cobrindo ordenação e exclusões.

## Concluído na v1.6.22

- **Atualização integrada por plataforma:** clicar no aviso de nova versão baixa o asset correspondente ao ambiente em execução e inicia a instalação.
- Download restrito à Release oficial, com conferência de tamanho, SHA-256 calculado localmente e validação do digest do GitHub quando disponível.
- Updater auxiliar separado do processo principal, encerramento limpo primeiro e encerramento forçado por PID após timeout somente se necessário.
- Nova versão relançada automaticamente após instalação bem-sucedida.
- Windows Portable com backup/rollback; Windows Setup com instalador; Linux AppImage/DEB/TAR.GZ e macOS DMG com fluxos próprios.
- Lock em arquivo com PID para impedir duas atualizações concorrentes e recuperar locks obsoletos.
- Configuração, banco SQLite, mensagens, estações, logs e demais dados permanecem preservados fora dos binários.

## Concluído na v1.6.23

- **Identidade visual:** a mesma logo vetorial/raster é aplicada ao cabeçalho, favicon, ícones Windows/Linux/macOS, bandeja do Windows e Manual PDF.
- **Mapa — filtro por última interação:** adicionadas as opções **Tudo** (padrão), **menos de 2 h**, **2 a 24 h** e **mais de 24 h**.
- O filtro atua sobre os marcadores e tracklogs; enlaces de topologia associados a estações conhecidas filtradas também deixam de ser exibidos.
- O Mapa informa quantas estações permanecem visíveis em relação ao total.
- A opção **Tudo** permanece selecionada por padrão em cada abertura da aplicação.
- **Mapa — legenda:** adicionada opção para minimizar/expandir a legenda; o estado escolhido é preservado localmente.

## Concluído na v1.6.24

- **Logo oficial única:** a imagem APRS fornecida para o projeto passa a ser a fonte visual única para interface, favicon, bandeja, ícones de plataforma e Manual PDF.
- **macOS:** removido o desenho alternativo do ícone; o ICNS passa a ser derivado da mesma logo PNG usada pelas demais plataformas.
- **Histórico de versões:** adicionadas as notas internas ausentes da v1.6.23 e as notas da v1.6.24.
- **Backlog consolidado:** removidas pendências já concluídas em queries APRS, estatísticas de clientes, idioma, topologia e gauges CPU/RAM.
- Permanecem abertas apenas melhorias/validações ainda não concluídas, incluindo ranking de conversas, estabilidade prolongada do Portable e compatibilidade de configuração com banco antigo.

## Concluído na v1.7

- **Mapa:** controles de Atividade e Topologia observada ficam fora do canvas, na barra superior.
- **Mapa:** animação de tráfego ao vivo ativada por padrão em novas instalações, com opção persistente para desativar.
- **Mensagens:** filtros compactos, com rótulos em uma linha.
- **Mensagens:** conversa em foco e campo Destinatário sincronizados, incluindo tratamento claro para destinatário novo sem histórico.
- **Idiomas:** suporte a Português, English, Español e Français, com seletor rápido, persistência e fallback seguro.
- **Estatísticas:** somente nome amigável do aplicativo/software na apresentação principal; identificadores técnicos permanecem internos.
- **Estatísticas:** fonte padrão maior e controle próprio de tamanho na Configuração.
- **Versionamento:** nova linha iniciada em v1.7; próximas releases serão v1.7.1, v1.7.2, v1.7.3...

## Concluído na v1.7.7

- **Mapa:** removida a recriação do botão global **Histórico** pelo patch legado; permanece somente o controle contextual do Mapa.
- **Mensagens:** **Apagar todas** foi renomeado para **Limpar**, preservando o estilo vermelho e a confirmação antes da exclusão.
- **Topologia:** novo padrão amarelo (`#ffff00`) com espessura mínima de **1 px**.
- **Tracklog:** mantido azul (`#3ba6ff`) por padrão.
- **Animação e som:** mantidos ativados por padrão para novas configurações.
- **Atualizações:** checagem periódica da versão mais recente alterada para **30 minutos**, sem sobreposição de verificações.
- **Windows ARM64:** adicionados **Setup ARM64** e **Portable ARM64** nativos, workflow dedicado e seleção de asset pelo updater conforme a arquitetura.
- **Topologia RF × APRS-IS:** preservada a capitalização dos q-constructs; `qAR` direto continua RF quando aplicável, enquanto `qAr`/rotas remotas via APRS-IS são classificadas como Internet/iGate.
- **Migração de topologia:** enlaces antigos ambíguos com metadata de iGate deixam de permanecer classificados como RF, eliminando linhas de Internet tratadas como rádio.
- **Testes:** regressões adicionadas para Histórico contextual, botão Limpar, padrões do Mapa, cadência de atualização, Windows ARM64 e separação RF × APRS-IS.

## Concluído na v1.7.6

- **Atualizador Windows:** helper nativo CMD passa a ser o caminho principal para aplicar atualização automática; PowerShell permanece apenas como fallback compatível.
- **Exportação KML:** o desktop abre **Salvar como** para escolher pasta e nome do arquivo; cancelar não gera erro.
- **Mapa:** **Histórico** e **Exportar KML** foram movidos para a mesma barra contextual de **Estações, Tracklog e Topologia**.
- **Estatísticas:** novo ranking **Estações que mais interagiram**, baseado somente em conversas APRS manuais.
- **Filtro de conversas:** beacons, telemetria, ACK/REJ, queries, respostas automáticas, boletins e retries não entram no ranking; grupos multipartes não inflam a contagem.
- **Testes:** regressões adicionadas para updater Windows, Salvar como do KML, barra contextual do Mapa e ranking de conversas manuais.

## Concluído na v1.7.5

- **Exportação KML:** botão na barra superior com seleção de Estações, Posições, Tracklogs e Topologia/enlaces, todas ligadas por padrão, e escolha de período.
- **Validação geográfica:** posições 0,0, inválidas, saltos implausíveis e coordenadas incompatíveis com iGate RF conhecido são rejeitadas e registradas como anomalias.
- **Mapa/topologia/replay/exportação:** dados geográficos rejeitados deixam de participar de marcadores, linhas, distâncias, animações e KML.
- **Estatísticas:** novo bloco **Estações com problemas**, com ocorrência, recorrência e atalhos para Mapa/Logs.
- **Estatísticas:** novo bloco **Possíveis melhorias**, com baixa redundância, concentração em iGate e possíveis lacunas de cobertura, sempre apresentados como inferências.
- **Estatísticas:** Digipeaters e iGates dos rankings passam a ser clicáveis e levam diretamente ao Mapa quando há posição válida.
- **Mensagens:** conversas agrupadas podem ser ordenadas por Remetente ou Data, crescente/decrescente.
- **Mensagens:** ação **Apagar todas** limpa o histórico local após confirmação e atualiza contadores/indicadores.
- **Testes:** regressões adicionadas para coordenadas suspeitas, KML, Estatísticas e Mensagens.

## Concluído na v1.7.4

- **Atualizador — visibilidade de erros:** toast elevado acima do modal para não ficar desfocado pelo overlay.
- **Atualizador — erro inline:** falhas de download/instalação exibidas dentro do modal, com detalhe técnico e destaque visual.
- **Atualizador — recuperação:** após erro, botões de instalar, abrir Release e fechar modal voltam ao estado utilizável.
- **Acessibilidade:** status do updater usa região `aria-live="assertive"`.
- **Testes:** regressões adicionadas para z-index, erro inline e reativação dos controles.

## Concluído na v1.7.3

- **Atualizador:** corrigida a geração dos helpers PowerShell/Bash; os scripts passam a conter quebras de linha reais em vez de sequências literais `\n`.
- **Baixar e instalar:** os botões de atualização fornecem feedback imediato e disparam diretamente o fluxo de download/instalação.
- **Diagnóstico:** updater registra solicitação, asset, URL, caminho temporário, tamanho esperado/recebido, SHA-256 e falhas.
- **Estatísticas:** versões semânticas e aliases do mesmo cliente são consolidados por família canônica; **Dire Wolf 1.7/1.8/1.9** passam a aparecer como **Dire Wolf**.
- **Estatísticas:** nomes originais, aliases e TOCALLs permanecem preservados internamente para diagnóstico.
- **Testes:** adicionada regressão que gera os helpers reais e valida as quebras de linha, além do agrupamento por família e do acionamento do botão de atualização.

## Concluído na v1.7.2

- **Mapa:** Estações, Tracklog e Topologia observada movidos para a mesma linha contextual do botão Histórico, mantendo a barra com altura compacta e liberando mais área útil para o mapa.
- **Popup da estação:** Última recepção passa a exibir também o tempo decorrido, com atualização automática enquanto o popup permanecer aberto.
- **Idiomas:** tempo relativo da última recepção formatado em Português, English, Español e Français.
- **Estatísticas:** TOCALLs diferentes que resolvem para o mesmo nome amigável de software/dispositivo são consolidados em uma única linha, com quantidade e percentual recalculados.
- **Estatísticas:** identificadores técnicos permanecem preservados internamente e o PT2VHF APRS Client mantém o destaque correto após a consolidação.
- **Testes:** adicionadas regressões para os três ajustes da v1.7.2.

## Concluído na v1.7.1

- **Atualizador:** helper externo confirmado antes do encerramento; falha não fecha a aplicação; modal persistente e progresso/status durante instalação.
- **Atualizações:** indicador de nova versão com pulsação enquanto houver release pendente.
- **Tracklogs:** rejeição de saltos irreais no backend e quebra visual de segmentos históricos extremos/relocações.
- **Mapa:** removido Atividade; Estações, Tracklog e Topologia com liga/desliga e períodos independentes.
- **Mapa:** Histórico/Replay movido para barra contextual abaixo das abas, visível somente no Mapa.
- **Mensagens:** aba destacada/pulsando quando chega mensagem direta enquanto outra aba está ativa.
- **Estatísticas:** indicativos de Estações mais ativas clicáveis para abrir Mensagens com destinatário preenchido.
- **Sobre:** nova aba com Alex/PT2VHF, contatos, tiny.cc/aprs e envio manual de Announcement APRS BLNA.
- **Idiomas:** cobertura PT/EN/ES/FR ampliada em áreas estáticas e dinâmicas, com atualização imediata na troca de idioma.

