# Backlog

## Concluído na v1.8.17

- **Configuração — zoom (sugestão de PU2MUS/Marco):** o step do mapa deixa de ser fixo e passa a ser configurável em **0,05 / 0,10 / 0,25 / 0,50 / 1,00**, com aplicação imediata, persistência no SQLite e botão **Restaurar zoom padrão**.
- A sensibilidade da roda/touchpad é ajustada automaticamente junto com o step escolhido, mantendo os botões **+ / −** coerentes com a mesma granularidade.
- **Mensagens programadas (sugestão de PY2FDG/Fábio Guilherme):** adicionada área **Agendadas** na aba Mensagens com envio **único** ou **semanal recorrente**, usando o fuso local do sistema.
- Os agendamentos podem enviar para **estação específica**, **lista de estações**, **boletim APRS** ou **grupo APRS**.
- Para estações/listas, são preservadas as rotas **Automático, APRS-IS, RF direto e RF personalizado**, incluindo path RF quando aplicável.
- **Listas reutilizáveis de destinatários:** o usuário pode nomear e salvar conjuntos de indicativos e reutilizá-los em agendamentos futuros.
- Em listas, há **intervalo configurável entre destinos** e opção para continuar com os demais quando um envio falhar.
- Cada execução registra resumo e resultado por destino; mensagens individuais continuam aparecendo no histórico normal da aba Mensagens.
- **Falha de rota:** política configurável entre **pular ocorrência** ou **tentar novamente** após período definido.
- **Persistência e duplicidade:** agendamentos ficam no SQLite; a execução devida é reivindicada de forma atômica para evitar disparo duplicado após reinicialização próxima ao horário.
- A tela mostra **próxima execução, última execução, status/erro**, além de editar, ativar/desativar, excluir e **Executar agora** sem alterar a próxima ocorrência programada.
- **TNC/RF — indicação de estado:** porta serial aberta deixa de aparecer como sucesso pleno enquanto não houver KISS válido. O cabeçalho e a aba distinguem **aguardando dados, bytes sem KISS, AX.25 inválido e RX KISS ativo**.
- O estado sem KISS usa indicação visual de **atenção**, reservando o estado verde/sucesso para RX KISS/AX.25 realmente ativo.
- **Idiomas:** novos controles e estados cobertos em PT-BR, EN, ES e FR.
- **Regressão:** adicionada suíte v1.8.17 com testes funcionais de SQLite para configuração do zoom, listas/agendamentos, recorrência semanal e indicação TNC.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.


## Concluído na v1.8.16

- **Sobre:** indicativo de Adriano corrigido definitivamente para **PP5AU** na interface, testes e documentação ativa.
- **Mapa — zoom:** refinado para `zoomSnap: 0.10`, `zoomDelta: 0.10`, `wheelPxPerZoomLevel: 300` e `wheelDebounceTime: 20`, produzindo níveis intermediários bem mais finos.
- **Mensagens — Conteúdo:** filtros reunidos em um único menu pulldown com **Mensagens, Boletins, Grupos e Telemetria**.
- **Mensagens — ações globais:** adicionados **Marcar tudo** e **Desmarcar tudo**, com aplicação imediata e persistência das preferências.
- **Mensagens — grupos:** boletins de grupo passam a ter filtro próprio, separado dos boletins gerais.
- **Estações — Ver:** adicionada a mesma árvore de categorias/tipos de estação usada pelo Mapa, com **Selecionar tudo / Remover tudo**.
- **Mensagens — Ver:** adicionada a mesma árvore de tipos de estação, aplicada às estações envolvidas nas mensagens.
- **Filtros compartilhados:** **Mapa, Estações e Mensagens** passam a usar o mesmo estado central de categorias de estação; uma alteração em uma aba é refletida nas demais.
- **Mensagens — segurança do filtro:** quando uma mensagem não puder ser associada com segurança a uma estação conhecida, ela permanece visível por padrão.
- **Catálogo de estações:** criado catálogo completo separado do filtro textual da aba Estações para evitar que o filtro de pesquisa interfira na classificação das Mensagens.
- **Interface:** botões **Ver** e **Conteúdo** indicam visualmente quando há filtros ativos.
- **Regressão:** adicionada suíte específica da v1.8.16 para zoom, filtros de conteúdo, menus Ver compartilhados e PP5AU.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.


## Concluído na v1.8.15

- **Sobre:** corrigido o indicativo de Adriano para **PP5UA** na aba Sobre, testes e referências do projeto.
- **Mensagens — filtros de exibição:** adicionadas opções persistentes e independentes para **Mostrar mensagens**, **Mostrar boletins** e **Ocultar telemetria**, sem apagar o histórico.
- **Mapa — zoom mais gradual:** Leaflet passa a usar zoom fracionário com `zoomSnap=0,25`, `zoomDelta=0,25` e roda do mouse mais progressiva; o zoom fracionário é persistido no SQLite.
- **Estações — sugestão de PU2MUS/Marco:** ordenação por **Ícone / tipo**, lista estável durante a sessão, novas estações no fim da visualização corrente, envio rápido sem sair da aba, reutilização do último texto e proteção opcional para **DMR, D-Star e SSIDs -12 a -15**.
- **Mapa × lista de Estações:** filtros do menu **Ver** também são aplicados à lista de Estações, eliminando a divergência em que DMR/D-Star desapareciam apenas do mapa.
- **TNC/RF — diagnóstico de transporte:** a interface diferencia porta/serial conectada de RX KISS/AX.25 válido e de TX entregue ao transporte; contabiliza bytes RX/TX, frames KISS e frames AX.25 inválidos.
- **Kenwood TM-D700:** documentado o cenário de uso em **modo PKT**, sem forçar o modo TNC/digipeater interno. O Client passa a alertar quando há bytes seriais sem frame KISS reconhecível e deixa explícito que entregar bytes à serial não confirma emissão RF.
- **Regressão:** nova suíte v1.8.15 cobre os recursos acima e preserva os testes das versões anteriores.
- **Produção:** release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.


## Concluído na v1.8.14

- **Mensagens:** Automático / APRS-IS / RF direto / RF personalizado por envio, com path RF personalizado e retry preservando a rota.
- **Responsividade:** 1360×768 e 1280×720 cobertos pelas regras de baixa altura, mantendo Mensagens e ações do popup acessíveis.
- **Interações:** alvos identificados como não interativos e sem evidência de capacidade bidirecional ficam com Mensagem, Posição, Status, Ouvidos, Ping/ACK e Trace desabilitados.
- **Mapa — Elevação/Relevo:** DEM Terrarium real com corte por altitude, hillshade derivado do próprio DEM, slider vertical, máximo padrão de 3.000 m, faixa de 100 a 9.000 m, persistência e opacidade independente.
- **Sobre:** logo, projeto, contatos, tiny.cc/aprs, divulgação APRS, colaboradores e explicação explícita de APRS em PT-BR/EN/ES/FR.
- **Compatibilidade:** preservados o hotfix de migração SQLite da v1.8.12 e todos os recursos posteriores.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.13

- **Mensagens — rota por envio:** consolidado Automático / APRS-IS / RF direto / RF personalizado, com path por mensagem e retry preservando a rota.
- **Responsividade:** consolidadas as regras de baixa altura aplicáveis a 1360×768 e 1280×720, mantendo Mensagens e ações do popup acessíveis.
- **Interação APRS:** objetos/itens e infraestrutura sem evidência de comunicação bidirecional permanecem com Mensagem, queries, Ping/ACK e Trace desabilitados.
- **Mapa — Relevo com corte:** consolidado DEM real, slider vertical, máximo padrão de 3.000 m configurável entre 100 e 9.000 m, persistência e opacidade independente.
- **Sobre:** consolidada a apresentação do projeto, contatos, tiny.cc/aprs, divulgação APRS e traduções PT-BR/EN/ES/FR.
- **Regressão:** nova suíte v1.8.13 valida os cinco requisitos acima e preserva o hotfix SQLite da v1.8.12.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

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

- **TNC / RF — Kenwood TM-D700 conecta pela serial, mas não recebe nem transmite (relato de PU2MUS - Marco)**
  - **Diagnóstico incorporado na v1.8.15:** o Client agora separa serial aberta, bytes recebidos, frame KISS reconhecido, AX.25 válido e TX entregue ao transporte.
  - **Ainda pendente:** confirmar em hardware real qual protocolo/configuração do TM-D700 em modo PKT entrega RX/TX compatível com o Client e implementar qualquer adaptação específica necessária sem ativar o digipeater interno.
  - Cenário relatado: o **Kenwood TM-D700** conecta pela porta serial e o Client indica estado **Conectado**, porém pacotes recebidos no rádio (ex.: de um **TH-D75**) não entram no PT2VHF APRS Client, mesmo com a portadora sendo percebida pelo equipamento.
  - No mesmo cenário, não há evidência de transmissão efetiva de pacotes APRS pelo rádio a partir do Client.
  - O TM-D700 está sendo usado em **modo PKT**. **Não assumir que o rádio deve ser colocado em modo TNC**, pois nesse equipamento esse modo passa a acionar o TNC/digipeater interno e altera o comportamento operacional desejado.
  - Diferenciar claramente **porta serial aberta/conectada** de **TNC/RF operacional**: o estado “Conectado” só deve representar transporte serial disponível; a interface deve indicar separadamente se houve RX de frame válido e se o caminho de TX foi confirmado.
  - Adicionar diagnóstico de RX mostrando bytes recebidos, frames reconhecidos/descartados, erros de framing/protocolo e horário do último frame válido.
  - Adicionar diagnóstico de TX mostrando tentativa de envio, bytes/frame entregues à serial, eventual resposta/erro do equipamento e horário da última transmissão solicitada.
  - Revisar parâmetros e protocolo usados com o TM-D700 em **PKT**, incluindo baud rate, modo de framing esperado e comandos de inicialização necessários, sem interferir no digipeater interno.
  - Criar indicação visual como **Serial conectada / RX aguardando / RX ativo / TX aguardando / TX ativo / protocolo incompatível** para evitar falso positivo de funcionamento.
  - Incluir teste/simulador de regressão para serial conectada sem frames e para RX/TX válidos, preservando compatibilidade com os TNCs KISS já suportados.
  - Quando possível, permitir captura de diagnóstico suficiente para comparar o que chega da serial com o que o rádio está recebendo pelo ar.



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

- **Idiomas — continuar revisão global de textos residuais**
  - A aba **TNC / RF** foi revisada em PT-BR, EN, ES e FR na v1.8.1, incluindo textos estáticos, estados dinâmicos e mensagens técnicas conhecidas.
  - Evitar exibir diretamente ao usuário mensagens técnicas do backend em português quando a interface estiver em outro idioma; mapear erros e estados conhecidos para chaves de tradução, preservando o detalhe técnico somente quando necessário para diagnóstico.
  - Fazer uma **varredura completa em todas as abas e popups** do aplicativo para localizar textos estáticos ou dinâmicos que ainda não acompanham a troca de idioma.
  - Revisar especialmente **Mapa, Mensagens, Estações, Log, Estatísticas, TNC / RF, Configuração, Sobre, atualização, exportação KML, queries APRS, popups e toasts**.
  - Garantir que a mudança de idioma atualize imediatamente os componentes já abertos, sem exigir reinício ou recarregamento da aplicação.
  - Manter **Português (Brasil)** como idioma padrão e usar fallback seguro somente quando uma chave ainda não existir, evitando misturar dois idiomas na mesma tela.
  - Revisar terminologia técnica de APRS/TNC para não traduzir incorretamente termos de protocolo como **KISS, AX.25, APRS-IS, Digipeater, iGate, WIDE1-1, WIDEn-N, ACK/REJ, RFONLY, NOGATE e q-construct**.
  - Adicionar testes de regressão que verifiquem as quatro línguas nas principais telas e detectem textos PT-BR inesperados quando EN/ES/FR estiverem ativos.

- **TNC / RF — próximos passos após a v1.8.0**
  - Adicionar protocolo **AGWPE** como alternativa a KISS, mantendo KISS Serial/TCP como base estável.
  - Consumir RSSI/SNR, DCD, ocupação de canal e demais métricas somente quando o modem/TNC realmente as fornecer.
  - Evoluir o grafo textual “Quem fala com quem” para visualização gráfica interativa no Mapa/Estatísticas.
  - Criar simulador de transporte KISS completo para cenários de múltiplos digis/iGates e testes de congestionamento sem rádio físico.
  - Ampliar políticas do otimizador automático somente após coleta de uso real, preservando compatibilidade APRS e logs auditáveis.

- **Mapa — painel lateral de estação**
  - Substituir progressivamente o popup grande da estação por um painel lateral fixo, preservando o mapa visível durante a consulta.
  - Exibir Indicativo, última recepção, distância, software/dispositivo, posição, status, favorito, mensagens, Ping, Trace e estações ouvidas.
  - Incluir atalhos para **Mostrar log**, **Enviar mensagem**, **Ping/ACK**, **Trace**, **Posição**, **Status** e histórico de queries.
  - Em telas pequenas, transformar o painel lateral em painel inferior responsivo.
  - Ao trocar de estação, atualizar o mesmo painel sem criar sobreposição adicional no mapa.

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

## Concluído na v1.8.12

- **Migração de banco legado:** corrigida a inicialização quando a tabela `packets` ainda não possuía a coluna `medium`.
- **Ordem segura de schema:** `medium` e `rx_fingerprint` são adicionadas antes da criação dos índices dependentes.
- **Sem perda de dados:** a atualização preserva mensagens, estações, logs, tracklogs e histórico existente.
- **Teste de regressão:** schema legado sem `medium` é criado em banco temporário e migrado automaticamente por `init_db()`.
- **Produção:** hotfix completo Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.11

- **RF / origem de recepção:** pacotes persistidos passam a registrar explicitamente `RF` ou `APRS-IS`.
- **Evidência dupla:** o mesmo indicativo pode ter recepções RF e APRS-IS preservadas simultaneamente.
- **Deduplicação entre meios:** impressão lógica correlaciona a mesma transmissão RF/APRS-IS em janela curta para o total consolidado.
- **TNC / RF:** tabela de estações ouvidas passa a combinar `tnc_heard` com histórico persistente de pacotes RF.
- **Tabela RF:** mostra recepções, pacotes RF persistidos, distância, direta/via digi quando conhecida, tipo e path.
- **Estatísticas:** novo resumo RF × APRS-IS, com pacotes, estações únicas, frames RF, estações nos dois meios e total lógico.
- **Ranking de estações:** novas colunas RF e APRS-IS.
- **Diagnóstico:** eventos `tnc_rf_station_heard` e `tnc_rf_rx_summary`.
- **Configuração:** títulos dos blocos em laranja, fonte maior e hierarquia visual reforçada nos temas claro/escuro.
- **Testes:** RF-only, RF+APRS-IS, deduplicação, fallback TNC/RF, Estatísticas e estilo da Configuração.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.10

- **Conexão APRS-IS:** indicador de estado e botão Conectar/Desconectar consolidados em um único componente no cabeçalho.
- **Estados explícitos:** Desconectado, Conectando, Reconectando, Conectado e verificado, Conectado sem verificação e Conexão perdida.
- **Ação robusta:** conectar/desconectar determinado por `wanted/connected/verified`, sem depender do texto do botão.
- **Concorrência:** múltiplos cliques são bloqueados enquanto uma ação de conexão está em andamento.
- **Interface:** removida a redundância do indicador separado; estado + ação + contexto ficam no mesmo controle.
- **Sobre:** adicionada seção Agradecimentos / Colaboradores.
- **Colaboradores:** PP5UA Adriano, PY4EI Allan, PU2MUS Marco, PP5PK Daniel Kondlatsch, PT2YW Ywstter e PT2PAG Paulo Galvão.
- **Idiomas/Testes:** PT-BR, EN, ES e FR; regressões de estado, ação e presença dos colaboradores.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.9

- **Atualizações:** intervalo automático padrão de 15 minutos, configurável entre 5 e 1.440 minutos.
- **Persistência:** intervalo salvo no SQLite e aplicado imediatamente sem reinício.
- **Agendamento:** removido o timer fixo de 30 minutos; o scheduler é reprogramado ao salvar a configuração.
- **Objetos APRS:** armazenamento ampliado com primeira recepção, altitude máxima, velocidade, curso, path, meteorologia, comentário, status e estado ativo/inativo.
- **Balões/radiossondas:** popup amigável com dados de voo e meteorologia quando disponíveis.
- **WX:** popup contextual com temperatura, umidade, pressão, vento, rajada e chuva.
- **AIS:** popup com MMSI, velocidade, curso e destino quando presentes.
- **Repetidores/infraestrutura:** frequência, offset e CTCSS quando detectáveis.
- **Outros objetos:** apresentação genérica organizada, omitindo campos ausentes e sem inferências forçadas.
- **Dados técnicos:** formato APRS, path e pacote bruto permanecem acessíveis em seção recolhível.
- **Idiomas/Testes:** PT-BR, EN, ES e FR; regressões de configuração, scheduler, persistência e normalização de objetos.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.8

- **CPU / Mapa:** eliminada a possibilidade de múltiplas gerações pesadas de `/api/map-data` executarem simultaneamente.
- **Single-flight:** somente uma thread constrói o snapshot do mapa; chamadas concorrentes reutilizam o último resultado válido.
- **SQLite:** removidos `EXISTS` correlacionados por estação nas rotas de Mapa e Estações.
- **Interações:** cálculo consolidado de estações com mensagens/ACK/REJ/queries respondidas.
- **Índices:** adicionados índices específicos para os caminhos críticos de interação.
- **Polling do mapa:** refresh completo passa de 10 s para 15 s; tráfego animado mantém atualização independente.
- **Diagnóstico:** novo evento `map_data_build` registra tempo de geração e volume retornado.
- **TNC serial:** CIM/PowerShell removido do polling automático; polling leve a cada 30 s e scan completo sob demanda.
- **Cache serial:** scan completo pode ser reutilizado por 60 s sem perder os metadados avançados.
- **Testes:** regressões de single-flight, stale-cache, índices SQLite e polling serial leve.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.7

- **TNC / RF — descoberta serial:** combina pyserial, Windows CIM/PnP e SERIALCOMM para listar todas as COMs encontradas.
- **Equipamentos seriais detectados:** nova tabela com porta, equipamento/descrição, chipset/interface, fabricante, VID/PID, número de série/HWID e estado.
- **CH9102/CH340/CH341:** identificação explícita dessas interfaces, além de CP210x, FTDI e CDC/ACM.
- **Radtel RT-950 Pro:** identificação nominal somente quando houver evidência nos metadados; CH9102 genérico não é rotulado como Radtel.
- **TNC UART:** orientação condicional para RT-950 Pro e 115200 bps quando o modelo for identificado.
- **Porta manual:** campo COM editável com datalist, permitindo informar uma porta não enumerada.
- **Reescanear:** atualização manual e periódica dos dispositivos enquanto TNC / RF estiver aberto.
- **Seleção direta:** botão Usar em cada equipamento preenche a COM correspondente.
- **Diagnóstico:** mudanças na enumeração serial registram device, descrição, fabricante, HWID, VID/PID, serial e fontes utilizadas.
- **Erros de conexão:** mensagens específicas para porta inexistente/desconectada e porta ocupada/acesso negado.
- **Testes:** regressão com COM6/CH9102 e COM10/CH340 simultâneos, descoberta nativa, interface e fallback manual.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.6

- **Correção crítica do Mapa:** restaurados os itens/camadas que podiam desaparecer após a v1.8.5.
- **Geometria do Leaflet:** removida a alteração global de altura de header/abas/main em telas baixas; o mapa volta a usar a estrutura estável da v1.8.4.
- **1360×768:** a compactação permanece apenas em Mensagens e no popup da estação, sem alterar globalmente a área do mapa.
- **Mapa → Ver:** árvore básica é renderizada imediatamente, mesmo antes da primeira resposta do backend.
- **Viewport:** Leaflet executa invalidateSize e recarga visual após resize/orientationchange.
- **Recuperação de estado:** estado totalmente desabilitado por regressão é recuperado uma única vez.
- **Remover tudo:** passa a registrar intenção explícita para que a recuperação automática não reverta uma escolha do usuário.
- **Falha temporária de dados:** o menu Ver permanece disponível mesmo se /api/map-data falhar.
- **Testes:** novas regressões cobrem as oito categorias do menu Ver, viewport, recuperação e persistência.
- **Compatibilidade:** preservada a seleção de rota/path de mensagens da v1.8.5.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.5

- **Mensagens — rota por envio:** opções Automático, APRS-IS, RF direto e RF personalizado.
- **Automático:** mantém APRS-IS como prioridade e usa RF direto somente quando APRS-IS não estiver disponível e o TNC/RF estiver pronto.
- **RF personalizado:** path por mensagem com validação AX.25, incluindo WIDE1-1 e WIDE1-1,WIDE2-1.
- **TNC/KISS:** mensagens RF reutilizam o transporte existente e respeitam conexão, pausa e confirmação de TX.
- **Histórico:** grava e exibe meio efetivo e path transmitido em cada mensagem de saída.
- **Retry:** preserva a rota/path original por padrão e aceita substituição por seleção explícita do compositor.
- **Responsividade:** otimizações específicas de baixa altura para 1360×768 @ 100% e resoluções equivalentes.
- **Popup de estação:** limite de altura, rolagem interna e área de ações sticky em telas baixas.
- **Mensagens:** cabeçalho/compositor compactados por altura para manter lista, destinatário e envio acessíveis.
- **Idiomas/Testes:** PT-BR, EN, ES e FR; testes de path, rota, persistência e layout.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.4

- **Saúde da aplicação:** monitoramento separado de CPU/RAM do aplicativo e do sistema operacional.
- **Limites padrão:** CPU crítica em 90% e memória crítica em 90%, após 30 segundos sustentados.
- **Popup:** aviso não bloqueante com recurso, escopo, valor, limite, duração e horário.
- **Antirruído:** histerese de 5 pontos percentuais e cooldown padrão de 10 minutos.
- **Configuração:** ativação, limites, persistência e cooldown ajustáveis.
- **Diagnóstico:** alertas críticos registrados com versão, plataforma e métricas do aplicativo/sistema.
- **Mapa:** barra contextual com Histórico, Completo/período e demais controles alinhada à esquerda.
- **Idiomas/Testes:** PT-BR, EN, ES e FR; regressões de pico curto, condição sustentada, cooldown, recuperação e alinhamento.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.3

- **Estatísticas → Software / dispositivos APRS:** classificação em **Aplicativo APRS**, **Dispositivo / Hardware** e **Indeterminado**.
- **Filtros:** adicionados **Mostrar aplicativos APRS**, **Mostrar dispositivos** e **Mostrar não identificados**, todos persistentes e habilitados por padrão.
- **Ranking:** posição e percentual são recalculados apenas sobre as categorias atualmente visíveis.
- **Aplicativos:** PT2VHF APRS Client, APRSdroid, Dire Wolf, UI-View, WinAPRS e demais clientes reconhecidos ficam separados do hardware.
- **Dispositivos:** rádios D-STAR, rigs, HTs, trackers, digipeaters/iGates embarcados e equivalentes não concorrem com aplicativos quando ocultos.
- **Indeterminados:** metadados ambíguos não são forçados para software nem hardware.
- **Mapa → Ver:** substituído o botão **Tudo** por **Selecionar tudo** e **Remover tudo**.
- **Mapa → Ver:** ações globais sincronizam pais, filhos, filtros dinâmicos e persistência, incluindo AIS e Balão/Radiosonda.
- **Idiomas:** novos controles e categorias traduzidos em PT-BR, EN, ES e FR.
- **Testes:** regressões para classificação APRS, filtros/percentuais e ações globais de Mapa → Ver.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.2

- **Inicialização:** porta interna automática a partir de **8080**, avançando sequencialmente até encontrar a primeira disponível por bind real do servidor.
- **Desktop:** Windows, Linux e macOS passam a usar automaticamente a porta efetivamente reservada no WebView/navegador.
- **Instância existente:** Windows persiste temporariamente host/porta para uma nova abertura localizar a interface correta.
- **Interface:** a porta selecionada aparece em **Configuração → Interface local** e é registrada no diagnóstico do Windows.
- **Manual:** captura automática deixa de depender de porta fixa e acompanha a porta publicada pela aplicação.
- **Mapa → Ver → Objetos:** adicionada categoria **AIS**, independente de **Balão/Radiosonda**.
- **Classificação AIS:** identificação conservadora por AIS/MMSI/marcadores equivalentes; símbolo de barco isolado não força a categoria.
- **Mapa → Ver:** todos os itens permanecem habilitados por padrão em novas configurações, preservando preferências salvas.
- **Configuração:** removida a bandeira grande do seletor de idioma; permanece o seletor compacto e as bandeiras pequenas do cabeçalho.
- **Testes:** regressões para fallback de porta, AIS, defaults do menu Ver, interface local e remoção da bandeira grande.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.1

- **Mapa:** removido **Relevo sombreado**; Relevo com corte permanece como única camada de elevação.
- **Mapas-base:** Claro/Escuro corrigidos para operação sem API key usando OSM com estilo local.
- **Mapas-base:** adicionados **CyclOSM, Humanitário / HOT, OSM.DE e ÖPNVKarte**.
- **Resiliência:** fallback automático para OSM após falhas repetidas de tiles, com registro no diagnóstico.
- **Idiomas:** aba **TNC / RF** revisada em PT-BR, EN, ES e FR, incluindo conteúdo dinâmico e troca imediata de idioma.
- **Idiomas:** novos nomes e textos de ajuda dos mapas-base traduzidos.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.8.0

- Nova aba **TNC / RF** com conexão KISS TCP e KISS Serial, listagem de portas, monitor AX.25/TNC2 e estado no cabeçalho.
- Digipeater com perfis Fill-in/WIDE1-1, Wide/WIDEn-N e aliases personalizados.
- Supressão de duplicatas, prevenção de loop, limite de hops, rate limit por origem e fila TX por prioridade.
- iGate RF→APRS-IS com qAR e Internet→RF restritivo a mensagens para estações ouvidas diretamente por RF.
- Histórico SQLite de frames, estações ouvidas, decisões Digi/iGate e grafo de comunicação.
- Análise **Quem fala com quem** com modos desligado, observação/recomendação e automático conservador.
- TX automático, Digi e iGate bidirecional desligados por padrão, confirmação explícita e botão **PARAR TX**.
- Testes de KISS, AX.25, paths WIDE, loop, qAR, presença RF direta e defaults seguros.
- Release completa multiplataforma iniciando oficialmente a série **1.8.x**.

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


## Backlog — AIS no mapa

- **Popup amigável ao clicar em objeto AIS**
  - Ao clicar em uma embarcação/objeto AIS no mapa, abrir um popup formatado e legível, em vez de exibir dados crus.
  - Exibir apenas campos disponíveis; não mostrar linhas vazias, `null` ou placeholders desnecessários.
  - Mostrar, quando disponíveis:
    - nome da embarcação;
    - MMSI;
    - indicativo/callsign;
    - tipo de embarcação em texto legível;
    - status de navegação;
    - latitude/longitude;
    - velocidade sobre o fundo (SOG), em nós e opcionalmente km/h;
    - rumo sobre o fundo (COG);
    - proa/heading;
    - destino informado;
    - ETA;
    - calado;
    - dimensões da embarcação;
    - tempo desde a última atualização;
    - fonte dos dados.
  - Converter códigos AIS numéricos para descrições amigáveis sempre que possível.
  - Organizar as informações em seções compactas e consistentes com os demais popups do mapa.

- **Imagem da embarcação**
  - Tentar exibir uma **foto real da embarcação** quando houver fonte pública confiável na internet.
  - Priorizar a identificação por:
    1. MMSI;
    2. nome da embarcação;
    3. callsign;
    4. modelo/classe/tipo.
  - Carregar a imagem de forma assíncrona para que o popup textual abra imediatamente.
  - Usar cache local/temporário para evitar consultas repetidas para a mesma embarcação.
  - Identificar claramente a imagem como **Foto da embarcação** quando houver correspondência confiável.

- **Fallback visual**
  - Se não houver foto real disponível, tentar exibir uma **imagem/ilustração do mesmo modelo ou classe/tipo de embarcação**.
  - Quando for apenas uma representação do modelo/tipo, identificar explicitamente como **Imagem ilustrativa do modelo/tipo**, sem sugerir que seja a embarcação exata.
  - Se nenhuma imagem adequada estiver disponível, manter somente o popup textual, sem erro técnico intrusivo.

- **Comportamento e robustez**
  - A ausência ou falha da fonte de imagem não deve impedir a abertura do popup AIS.
  - Não bloquear a interface enquanto a imagem é consultada.
  - Preferir fontes públicas e estáveis, com identificação clara de origem quando apropriado.


## Backlog — Cobertura RF em mapa de calor

- Substituir os círculos individuais da camada de **Cobertura RF** por um **heatmap**.
- Cada ponto de recepção RF deve contribuir para a intensidade visual da área.
- Pontos próximos devem **se mesclar automaticamente**, formando manchas contínuas de cobertura.
- O comportamento deve ser **dependente do zoom**:
  - em zoom mais afastado, agrupar/mesclar mais os pontos, formando áreas amplas;
  - em zoom mais próximo, reduzir o raio de influência para revelar detalhes locais;
  - recalcular/redesenhar a camada quando o nível de zoom mudar.
- A intensidade poderá considerar, quando disponível:
  - quantidade de recepções;
  - SNR;
  - RSSI;
  - período atualmente selecionado no mapa.
- Áreas com maior densidade e/ou melhor qualidade RF devem aparecer mais intensas.
- Evitar marcadores circulares individuais sobrepostos, reduzindo poluição visual.
- Manter o filtro temporal e demais filtros já existentes da cobertura.
- Não gerar qualquer tráfego adicional no APRS/rádio; usar exclusivamente os dados de recepção já registrados.
- Preparar a arquitetura para permitir futuramente alternância entre:
  - **Mapa de calor**
  - **Pontos individuais**


## Backlog — Zoom do mapa com passos intermediários

- Reduzir o tamanho do **step de zoom** do mapa, permitindo níveis intermediários entre os níveis atuais.
- Objetivo: tornar o zoom mais suave e permitir enquadramento mais preciso, especialmente para análise de cobertura RF, tracklogs, topologia e objetos AIS.
- Preferir **zoom fracionário**, quando suportado pelo motor de mapa.
- Valor inicial recomendado:
  - `zoomDelta`: **0,25**;
  - `zoomSnap`: **0,05** ou **0,10**.
- Aplicar o mesmo comportamento a:
  - botões `+` / `-`;
  - roda do mouse;
  - gestos de zoom, quando aplicável;
  - controles programáticos que alterem o zoom.
- Manter compatibilidade com todos os tipos de mapa-base e overlays.
- Validar desempenho do heatmap de Cobertura RF com níveis fracionários de zoom.

