# PT2VHF APRS Client - v1.14.2

Cliente APRS-IS multiplataforma para **Windows, Linux e macOS**, com mapa, mensagens, estações, tracklogs, topologia observada, Log TNC2, banco SQLite local e atualização integrada.

A **v1.14.2** adiciona Cobertura RF em heatmap e amplia o popup AIS, preservando as melhorias de SAT, TNC/RF, mensagens e atualização automática das versões anteriores.

## Downloads da versão mais recente

Os arquivos abaixo apontam diretamente para a **release v1.14.2**, evitando links `latest/download` com nomes de arquivo de versões anteriores.

### Windows
- [Windows x64 — Instalador](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/PT2VHF_APRS_Client_Setup_x64_v1.14.2.exe)
- [Windows x64 — Portable](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/PT2VHF_APRS_Client_Portable_x64_v1.14.2.exe)
- [Windows ARM64 — Instalador](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/PT2VHF_APRS_Client_Setup_ARM64_v1.14.2.exe)
- [Windows ARM64 — Portable](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/PT2VHF_APRS_Client_Portable_ARM64_v1.14.2.exe)

### Linux
- [Linux x86_64 — AppImage](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/PT2VHF_APRS_Client_x86_64_v1.14.2.AppImage)
- [Linux x86_64 — DEB](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/pt2vhf-aprs-client_1.14.2_amd64.deb)
- [Linux x86_64 — TAR.GZ](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/PT2VHF_APRS_Client_Linux_x86_64_v1.14.2.tar.gz)
- [Linux ARM64 — AppImage](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/PT2VHF_APRS_Client_arm64_v1.14.2.AppImage)
- [Linux ARM64 — DEB](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/pt2vhf-aprs-client_1.14.2_arm64.deb)
- [Linux ARM64 — TAR.GZ](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/PT2VHF_APRS_Client_Linux_arm64_v1.14.2.tar.gz)

### macOS
- [macOS — Apple Silicon](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/PT2VHF_APRS_Client_macOS_arm64_v1.14.2.dmg)
- [macOS — Intel](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/PT2VHF_APRS_Client_macOS_x86_64_v1.14.2.dmg)

### Documentação
- [Manual PDF](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.14.2/PT2VHF_APRS_Client_Manual_v1.14.2.pdf)
- [Notas da versão mais recente](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/latest)



## Novidades da v1.14.2

- **Cobertura RF:** nova camada em heatmap Canvas, sem biblioteca externa e sem transmitir qualquer pacote adicional.
- **Qualidade:** RSSI/SNR influenciam a intensidade quando existem; na ausência deles, usa-se densidade de recepções RF.
- **Zoom:** raio adaptativo conforme o nível de zoom para mesclar mais em visão ampla e detalhar ao aproximar.
- **Período:** o heatmap respeita o período selecionado na barra do Mapa.
- **Mapa → Ver:** nova opção Cobertura RF, integrada a Selecionar tudo / Remover tudo.
- **AIS:** popup ampliado com nome, MMSI, IMO, indicativo, tipo, navegação, SOG/COG, proa, destino, ETA, calado e dimensões quando disponíveis.
- **AIS legível:** códigos comuns de tipo/status são traduzidos para descrições amigáveis.
- **Imagem AIS:** foto real continua disponível via provedor configurável por MMSI/IMO; sem correspondência, o fallback é explicitamente ilustrativo.
- **Robustez:** o enriquecimento externo é assíncrono e não bloqueia o popup textual.
- **Backlog:** item antigo de zoom intermediário encerrado porque o step configurável já existe.
- **TM-D700:** validação física continua pendente de equipamento real e segunda estação/monitor RF.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## Novidades da v1.14.1

- **SAT:** correção da renderização imediata da ISS e demais satélites selecionados.
- **Padrão:** somente ISS/NORAD 25544 selecionada em instalações novas.
- **Desempenho:** marcadores aparecem progressivamente; tracks são carregados em fila limitada.
- **Interface:** mapa, estações e mensagens em primeiro plano; configurações, beacon e agenda recolhidos.
- **Passagem:** contador à esquerda com nome/indicativo e estado AOS/LOS.
- **Menu:** aba superior abreviada para **SAT**.
- **Notificações:** sino removido da barra superior; Centro de notificações mantido em Configuração.
- **Alertas:** opção de nova estação desativada passa a ser respeitada imediatamente e após reinício.
- Release completa para Windows, Linux, macOS e Manual PDF.

## Novidades da v1.14.0

- **Satélites / ISS operacional:** estações recebidas, detalhes e mensagens APRS diretamente na aba.
- **Mensagens sincronizadas:** usa o mesmo pipeline da aba Mensagens, incluindo ACK/REJ, retries, rota e path.
- **Seleção compacta:** painel recolhível com pesquisa por nome, indicativo e NORAD.
- **Contador maior:** HH:MM:SS na barra operacional, somente para selecionados/favoritos elegíveis.
- **Beacon Satélite / curto:** path próprio, comentário curto, intervalo, elevação mínima, cobertura e parada no LOS.
- **Segurança RF:** consentimento explícito e mesmas proteções de TX do TNC/RF.
- **Saúde TNC:** painel restrito à aba TNC / RF.
- Release completa para Windows, Linux, macOS e Manual PDF.

## Novidades da v1.13.0

- **APRS confirmado:** a lista de satélites deixa de tratar packet/AX.25/GFSK genérico como APRS. Colibri-S é coberto por teste de regressão.
- **Contador de passagem:** próximo AOS APRS em HH:MM:SS, grande e amarelo, com troca automática para contagem até LOS durante a passagem.
- **Despertador:** aviso sonoro/visual configurável antes da cobertura, com deduplicação e ações rápidas.
- **TLE multifonte:** CelesTrak Amateur/Stations + AMSAT, prioridades, fallback, teste de fonte e atualização diária interna.
- **Controle operacional:** Monitorar / Ignorar / Fora do ar e serviços APRS/SSTV/Telemetria/Voz/Packet independentes.
- **Seleção rápida:** Marcar tudo / Desmarcar tudo respeitando filtros.
- **TM-D700/TM-D710:** perfil específico para terminal/PKT, separando velocidade serial da velocidade packet no RF.
- **Diagnóstico TNC:** captura limitada ASCII/HEX e estados específicos para terminal, KISS e AGWPE.
- **Segurança:** terminal/PKT não recebe TX KISS automático.
- **Autoteste:** informa camadas validadas e não declara TX RF físico sem teste real.
- Release completa multiplataforma com Manual PDF.

## Novidades da v1.12.0

- **Satélites / ISS:** nova aba dedicada para operação APRS/packet espacial.
- **Mapa orbital próprio:** posição atual, trajetória futura/passada, footprint/cobertura, estação local, múltiplos satélites e modo seguir.
- **Agenda de passagens:** cálculo SGP4 de AOS/TCA/LOS, elevação máxima, azimutes e duração para 24 h, 48 h ou 7 dias.
- **Dados orbitais:** sincronização de catálogo packet/APRS via SatNOGS e TLE via CelesTrak, com cache e época do TLE.
- **Frequências e Doppler:** painel mostra uplink/downlink, modo e estimativa de Doppler quando houver dados.
- **Alertas de passagem:** antecedência e elevação mínima configuráveis, popup e integração com o Centro de notificações.
- **Mapa → Ver → Satélites / ISS:** camada resumida opcional no mapa APRS principal, independente do mapa orbital dedicado.
- **Topologia RF × APRS-IS:** o meio real de recepção passa a ser propagado até a topologia. Pacote recebido pelo TNC como RF não vira Internet apenas por terminar em iGate.
- **Migração legada corrigida:** removida a rotina antiga que, a cada inicialização, convertia enlaces RF com metadado de iGate para Internet. O histórico RF é reparado a partir de `packets.medium='RF'`.
- **Diagnóstico da topologia:** popup/hover informa se a classificação veio de RF direto do transporte, RF inferido do path, APRS-IS confirmado ou evidência mista.
- **Janelas destacáveis:** Mensagens, Estações e Logs usam controles no padrão Windows — minimizar, maximizar/restaurar e fechar/encaixar — com geometria segura e persistente.
- **Logs destacável:** passa a usar a mesma infraestrutura de janela das demais abas.
- **Layout:** ação para restaurar a geometria padrão das janelas.
- **Menu superior:** removido o campo de busca da extremidade esquerda da barra contextual do mapa.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## Novidades da v1.11.1

- **RF → iGate:** o trecho físico que chega ao iGate permanece classificado como **RF**, inclusive quando o mesmo par de estações também foi observado via APRS-IS.
- **Linha tracejada:** passa a representar apenas enlaces **100% Internet/APRS-IS**, sem qualquer evidência RF para o mesmo par.
- **Evidência mista:** o backend consolida RF + Internet por origem/destino, dá precedência visual ao RF e preserva os dois contadores como metadados.
- **Popup/hover:** mostra **RF** como tipo principal quando houver RF e informa separadamente quantas observações também ocorreram via APRS-IS.
- **Paths qAR/qAO:** continuam representando a entrada física RF no iGate; qAr e demais caminhos exclusivamente APRS-IS continuam Internet.
- **Regressão:** adicionados testes para RF → iGate, evidência mista e Internet-only.
- Release completa multiplataforma com Manual PDF.

## Novidades da v1.11.0

- **Contadores TNC corrigidos:** RX/TX da sessão são reconciliados com os frames realmente persistidos, eliminando o cenário em que o TNC funciona mas os indicadores ficam em zero.
- **Health check automático:** diferencia transporte desconectado, porta aberta sem dados, bytes sem KISS, KISS com AX.25 inválido, KISS ativo, RX AX.25 operacional e RX/TX operacional.
- **Autoteste TNC:** simulador interno determinístico valida KISS RX, AX.25, parser, modelo de contadores, TX e ACK sem rádio físico.
- **Timeline do TNC:** registra mudanças reais de saúde/conectividade com horário e estado.
- **Centro de notificações:** sino no cabeçalho com histórico persistente de alertas e marcação de leitura.
- **Alertas configuráveis:** incorpora as correções da v1.10.1 para preferências, transições, deduplicação e quedas inesperadas.
- **SQLite:** painel de saúde com integridade, tamanho, WAL, fragmentação, política de retenção por tipo de dado e otimização manual segura.
- **Perfil operacional:** exibe pacotes, RF/APRS-IS, mensagens, caminhos observados e seção **Ouvido por** baseada em evidência de topologia.
- **Diagnóstico:** botão para copiar o diagnóstico completo do TNC em formato pronto para suporte.
- Release completa multiplataforma com regressões e Manual PDF.

## Novidades da v1.10.1

- **Estação apareceu:** passa a significar entrada/reentrada real na janela ativa, e não qualquer atualização de `last_heard`.
- **Estação desapareceu:** é disparado apenas quando a estação efetivamente sai da janela ativa configurada; ao reaparecer, um novo desaparecimento futuro pode alertar novamente.
- **Favorito apareceu:** segue a mesma transição real e respeita seu checkbox independentemente do alerta genérico de estação.
- **Nova mensagem:** deduplicação por ID evita avisos repetidos do mesmo registro.
- **TNC caiu / APRS-IS caiu:** alerta apenas em queda inesperada; desconexão voluntária não gera alarme.
- **Problema no banco:** um único aviso por episódio; após normalização, uma nova falha pode gerar novo alerta.
- **Configuração:** os checkboxes passam a ser aplicados/salvos imediatamente, mantendo também o botão **Salvar alertas**.
- **Regressão:** novos testes cobrem preferências `false`, separação entre estações ativas/desaparecidas, deduplicação e lógica por transição.

## Novidades da v1.10.0

- **QRZ.com:** enriquecimento opcional do perfil da estação via API XML, com foto principal quando fornecida, nome, cidade, estado/região, país, grid, link do indicativo, cache local e fallback seguro.
- **AIS:** provedor externo configurável por MMSI/IMO, com cache e exibição de foto somente quando houver associação inequívoca.
- **Métricas RF:** suporte extensível a RSSI, SNR, DCD, frequência, canal e origem; valores que o hardware não fornece permanecem explicitamente indisponíveis.
- **TM-D700 em PKT:** diagnóstico específico e roteiro formal de validação física. A compatibilidade física só será declarada após RX/TX confirmados com rádio real.
- **Soak test:** perfis de 24 h, 72 h e 7 dias, com CPU, RAM, threads, handles quando disponíveis, crescimento do banco e detecção de crescimento anormal de memória.
- **Migração:** matriz automatizada de bancos históricos 1.6.x, 1.7.x, 1.8.0, 1.8.4, 1.8.10, 1.8.18, 1.9.0 e banco novo.
- **Idiomas:** auditoria contínua PT-BR/EN/ES/FR, com paridade de dicionários, validação das chamadas de tradução e relatório de textos visíveis candidatos.
- **Produção:** release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## Novidades da v1.9.0

- **Mensagens e Estações destacáveis:** podem ser desacopladas da navegação, arrastadas e redimensionadas sobre o mapa, minimizadas e encaixadas novamente; posição e tamanho são preservados localmente.
- **Busca Global:** pesquisa indicativos/SSID, objetos APRS, meteorologia, AIS, repetidores e texto de comentário/status.
- **Organização de estações:** nome amigável, cor, nota e grupos definidos pelo usuário.
- **Backup completo:** exporta banco, mensagens, estações, favoritos, tracklogs, agendamentos, grupos e preferências; a restauração valida o SQLite e cria cópia pré-restauração.
- **Alertas configuráveis:** estação/favorito apareceu, estação desapareceu, nova mensagem, queda de TNC/APRS-IS e problema de integridade do banco.
- **Timeline unificada:** combina mensagens, posições, queries e tráfego RF em uma única sequência cronológica.
- **Modo apresentação:** mapa em tela cheia com controles mínimos para clubes, encontros e acompanhamento operacional.
- **TNC / RF:** botão **Testar TNC** executa diagnóstico não destrutivo do transporte, incluindo KISS Serial/TCP e AGWPE, sem declarar emissão RF quando apenas o transporte respondeu.
- **Painel de saúde da rede:** preserva KPIs, comparação entre períodos e grafo “Quem fala com quem” introduzidos na v1.8.18.
- **Exportações e suporte:** CSV, GeoJSON e pacote de diagnóstico sanitizado permanecem integrados.
- **Linux ARM64:** permanece parte do pipeline oficial ao lado de Windows x64/ARM64, Linux x86_64 e macOS ARM64/Intel.
- **TM-D700 em PKT:** continua explicitamente dependente de validação com hardware real; a aplicação não declara compatibilidade física ainda não comprovada.
- Release completa com testes de regressão e Manual PDF.

## Novidades da v1.8.18

- **AGWPE TCP:** transporte raw AX.25 integrado ao painel TNC/RF, além de KISS TCP e KISS Serial.
- **Busca rápida no Mapa:** localize indicativos completos ou parciais e abra o detalhe da estação.
- **Painel lateral de estação:** visualização fixa/responsiva com informações principais e atalhos de ação.
- **Saúde da rede:** novos KPIs de tráfego, RF × APRS-IS, duplicados, ACK, RTT e estações novas/desaparecidas.
- **Comparação entre períodos:** período atual contra o imediatamente anterior de mesma duração.
- **Quem fala com quem:** grafo visual SVG interativo das interações observadas.
- **CSV e GeoJSON:** exportação por período para Excel, QGIS e ferramentas externas.
- **Pacote de diagnóstico:** ZIP sanitizado com integridade do banco, plataforma, arquitetura e informações úteis de suporte.
- **Simulador KISS:** regressão de fragmentação, duplicidade e caminhos multi-hop sem depender de rádio físico.
- **Linux ARM64:** artefatos oficiais e updater consciente da arquitetura.
- **TM-D700 em PKT:** a validação física RX/TX continua dependente do equipamento real; a aplicação não declara compatibilidade que ainda não foi comprovada.
- **Métricas RF:** RSSI/SNR/DCD são consumidos somente quando fornecidos pelo modem/TNC.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## Novidades da v1.8.17

- **Mensagens → Agendadas:** crie envio único ou recorrência semanal sem precisar estar junto ao rádio no horário.
- O destino pode ser **uma estação**, **uma lista de estações**, **boletim APRS** ou **grupo APRS**.
- Para estação/lista, escolha **Automático, APRS-IS, RF direto ou RF personalizado**, incluindo path RF personalizado.
- **Listas de destinatários:** salve conjuntos de indicativos com nome e reutilize em diferentes agendamentos.
- Em listas, configure intervalo entre destinatários e escolha se uma falha deve interromper ou continuar os demais envios.
- Se a rota estiver indisponível, escolha entre **pular a ocorrência** ou **tentar novamente** após o período definido.
- A tela mostra **próxima execução, última execução, status e erro**, além de editar, ativar/desativar, excluir e **Executar agora**.
- Agendamentos e listas são persistidos no SQLite e protegidos contra disparo duplicado da mesma ocorrência após reinicialização.
- **Configuração → Mapa → Step do zoom:** escolha **0,05 / 0,10 / 0,25 / 0,50 / 1,00**; a alteração é aplicada imediatamente e fica persistida após salvar.
- A sensibilidade da roda/touchpad é ajustada junto com o step escolhido; **Restaurar zoom padrão** volta para 0,10.
- **TNC/RF:** serial conectada sem KISS válido passa a aparecer como estado de atenção. O Client diferencia **aguardando dados, bytes sem KISS, AX.25 inválido e RX KISS ativo**.
- O indicador verde/sucesso fica reservado para RX KISS/AX.25 realmente ativo.
- Novos controles e estados acompanham PT-BR, English, Español e Français.
- A validação física específica do **Kenwood TM-D700 em modo PKT** continua pendente para teste com o equipamento real.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Novidades da v1.8.16

- **Sobre:** Adriano corrigido para **PP5AU**.
- **Mapa:** zoom refinado para passos de **0,10**, com roda do mouse mais gradual.
- **Mensagens → Conteúdo:** novo menu pulldown com **Mensagens, Boletins, Grupos e Telemetria**.
- O menu Conteúdo inclui **Marcar tudo** e **Desmarcar tudo**, aplica o filtro imediatamente e persiste a seleção.
- **Grupos:** boletins de grupo podem ser mostrados/ocultados separadamente dos boletins gerais.
- **Estações → Ver:** mesma árvore de tipos/categorias usada no Mapa, incluindo **Selecionar tudo / Remover tudo**.
- **Mensagens → Ver:** mesma árvore compartilhada, filtrando mensagens conforme as estações envolvidas.
- **Sincronização:** Mapa, Estações e Mensagens usam o mesmo estado central do menu **Ver**.
- Mensagens sem classificação segura de estação permanecem visíveis para evitar ocultação indevida.
- O catálogo completo de estações é mantido separado do filtro textual da aba Estações.
- Os botões **Ver** e **Conteúdo** indicam quando há filtros ativos.
- Mantém o diagnóstico TNC/RF da v1.8.15 e a pendência de validação física do **Kenwood TM-D700 em PKT**.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Novidades da v1.8.15

- **Sobre:** indicativo de Adriano corrigido para **PP5AU**.
- **Mensagens:** filtros persistentes para **Mostrar mensagens**, **Mostrar boletins** e **Ocultar telemetria**.
- **Mapa:** zoom mais gradual, com níveis intermediários em passos de **0,25** e rolagem menos abrupta.
- O nível de zoom fracionário passa a ser salvo e restaurado pelo banco local.
- **Estações:** ordenação por **Ícone / tipo**, ordem visual estável durante atualizações e novas estações acrescentadas ao fim da lista corrente.
- **Mensagem rápida:** envio direto pela aba Estações, sem trocar de tela; o último texto fica disponível para o próximo destinatário.
- **Proteção:** opção para evitar envio rápido a **DMR, D-Star e SSIDs -12 a -15**, com indicação visual.
- **Mapa × Estações:** filtros selecionados em **Ver** também passam a valer para a lista de Estações.
- **TNC/RF:** o estado agora diferencia **serial conectada**, **bytes recebidos sem KISS reconhecido**, **frame KISS/AX.25 válido** e **TX entregue ao transporte**.
- O Client deixa explícito que um frame entregue à serial **não confirma, sozinho, que houve emissão RF**.
- **Kenwood TM-D700:** o cenário relatado por PU2MUS/Marco é documentado para uso em **modo PKT**; o Client não força o modo TNC/digipeater interno.
- A compatibilidade física específica RX/TX do TM-D700 em PKT permanece sujeita a validação com o equipamento real, caso seja necessária adaptação adicional.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Novidades da v1.8.14

- **Todos os backlogs solicitados ficam consolidados nesta release.**
- **Mensagens:** mantém seleção por envio em **Automático, APRS-IS, RF direto e RF personalizado**, incluindo path RF personalizado e retry preservando a rota.
- **Responsividade:** mantém as regras específicas para telas baixas, cobrindo **1360×768** e **1280×720** sem comprometer a geometria do mapa.
- **Interações APRS:** alvos identificados como não interativos e sem evidência de capacidade bidirecional ficam com **Mensagem, Posição, Status, Ouvidos, Ping/ACK e Trace desabilitados**.
- **Mapa → Relevo com corte:** o DEM Terrarium agora recebe **hillshade calculado a partir do gradiente local das próprias altitudes**, tornando o relevo visualmente sombreado sem depender de uma camada externa.
- O relevo mantém **corte por altitude**, slider vertical, máximo padrão de **3.000 m**, limite configurável de **100 a 9.000 m**, persistência e opacidade independente.
- **Sobre → O que é APRS?:** nova explicação clara de APRS, incluindo posição, mensagens, telemetria, meteorologia, **RF** e **APRS-IS**.
- A explicação acompanha o idioma selecionado em **Português, English, Español e Français**.
- Mantém logo, contatos, **tiny.cc/aprs**, divulgação por Announcement APRS e colaboradores.
- Preserva o hotfix de migração SQLite da v1.8.12 e os recursos consolidados na v1.8.13.
- Inclui regressões específicas da v1.8.14 e validador de produção atualizado.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Novidades da v1.8.13

- **Mensagens → Rota de envio:** consolida **Automático, APRS-IS, RF direto e RF personalizado**, incluindo path por mensagem e retry preservando a rota original.
- **Responsividade:** mantém a compactação específica de Mensagens e popup em telas baixas; a regra cobre **1360×768** e **1280×720** sem alterar a geometria global do mapa.
- **Estações sem capacidade bidirecional:** objetos/itens e infraestrutura sem evidência de suporte interativo ficam com **Mensagem, Posição, Status, Ouvidos, Ping/ACK e Trace desabilitados**.
- **Mapa → Camadas → Relevo com corte:** consolida DEM real, slider vertical, cota persistente, máximo padrão de **3.000 m**, limite configurável de **100 a 9.000 m** e opacidade independente.
- **Sobre:** consolida logo, apresentação do projeto, contatos, **tiny.cc/aprs**, divulgação por Announcement APRS, colaboradores e textos dinâmicos em **PT-BR, English, Español e Français**.
- **Migração SQLite:** preserva integralmente o hotfix da v1.8.12 para bancos antigos.
- **Testes:** nova suíte v1.8.13 impede regressão dos cinco requisitos consolidados e o validador de produção foi atualizado.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## Novidades da v1.8.12

- Corrige a falha de inicialização **`sqlite3.OperationalError: no such column: medium`** em bancos criados por versões anteriores.
- A migração agora adiciona **`medium`** e **`rx_fingerprint`** à tabela `packets` **antes** de criar os índices que usam essas colunas.
- **Não é necessário apagar ou recriar o banco.** Mensagens, estações, logs, tracklogs e histórico existente são preservados.
- Adiciona teste de regressão que parte de um schema legado realista, executa `init_db()` e confirma a migração completa.
- Mantém integralmente a v1.8.11:
  - estações recebidas por RF em **TNC / RF**;
  - resumo e colunas **RF × APRS-IS** em Estatísticas;
  - deduplicação lógica entre os dois meios;
  - títulos maiores e laranja na aba **Configuração**.

## Novidades da v1.8.11

- **RF × APRS-IS:** cada pacote recebido passa a preservar explicitamente o meio de entrada.
- Pacotes vindos do **TNC/KISS** são marcados como **RF**; pacotes recebidos do servidor continuam marcados como **APRS-IS**.
- **TNC / RF → Estações ouvidas por RF** passa a usar também o histórico persistente, evitando que estações RF desapareçam da tabela.
- A tabela mostra **Recepções, Pacotes RF, Distância, direta/via digi quando conhecida, último tipo e path**.
- **Estatísticas** ganha um resumo **Recepção RF × APRS-IS**, com pacotes, estações únicas, frames RF e estações observadas nos dois meios.
- O ranking de estações mostra colunas separadas **RF** e **APRS-IS**.
- A mesma transmissão observada pelos dois meios é correlacionada em um **total lógico deduplicado**, sem apagar a evidência individual de RF e Internet.
- Novos eventos de diagnóstico ajudam a validar o RX TNC/KISS e as estações RF observadas.
- Na aba **Configuração**, os títulos dos blocos ficam **laranja e maiores**, com melhor hierarquia visual nos temas claro e escuro.
- Inclui testes específicos para RF-only, RF+APRS-IS, deduplicação entre meios, tabela TNC/RF e estilo da Configuração.

## Novidades da v1.8.10

- **Conexão APRS-IS:** o cabeçalho passa a ter um único componente para mostrar o estado atual e executar a ação de conectar/desconectar.
- Estados exibidos diretamente: **Desconectado, Conectando…, Reconectando…, Conectado e verificado, Conectado sem verificação e Conexão perdida**.
- A ação disponível usa os estados reais do backend (`wanted`, `connected`, `verified`) e não depende mais do texto exibido.
- O controle usa indicador visual, texto principal e uma linha secundária com a ação/contexto.
- Cliques concorrentes são bloqueados enquanto a ação está em andamento.
- A aba **Sobre** ganha uma seção **Agradecimentos / Colaboradores**.
- Colaboradores reconhecidos nesta versão:
  - **PP5AU — Adriano**
  - **PY4EI — Allan**
  - **PU2MUS — Marco**
  - **PP5PK — Daniel Kondlatsch**
  - **PT2YW — Ywstter**
  - **PT2PAG — Paulo Galvão**
- A seção agradece sugestões, testes, validações e ajustes que ajudam na evolução contínua do software.
- Textos atualizados em **PT-BR, EN, ES e FR**.

## Novidades da v1.8.9

- **Atualizações:** checagem automática a cada **15 minutos** por padrão.
- **Configuração → Atualizações:** novo intervalo ajustável entre **5 e 1.440 minutos**, persistido no banco e aplicado sem reiniciar.
- A verificação manual continua disponível independentemente do intervalo automático.
- **Objetos APRS:** popups passam a exibir informações formatadas e amigáveis, omitindo campos vazios.
- **Balões/radiossondas:** altitude atual e máxima observada, estado de voo, velocidade vertical/horizontal, curso, frequência e meteorologia quando disponíveis.
- **Estações meteorológicas:** temperatura, umidade, pressão, vento, rajada e chuva quando presentes.
- **AIS/embarcações:** MMSI, velocidade, curso e destino quando informados.
- **Repetidores/infraestrutura:** frequência, offset e CTCSS quando detectáveis.
- Objetos passam a preservar **primeira recepção, altitude máxima, velocidade, curso, path, meteorologia, comentário e status**.
- Todo popup mantém **Dados técnicos** recolhidos, com formato APRS, path e pacote bruto.
- Objetos não identificados recebem apresentação genérica organizada, sem inventar significado para campos ausentes.
- Traduções atualizadas para PT-BR, EN, ES e FR.

## Novidades da v1.8.8

- **Mapa muito mais leve:** `/api/map-data` passa a usar single-flight global para impedir várias consultas SQLite pesadas ao mesmo tempo.
- Quando outra geração do mapa já está em andamento, o Client reutiliza o **último snapshot válido** em vez de ocupar outro worker do servidor.
- A consulta de interação de estações foi reestruturada para eliminar `EXISTS` correlacionados executados estação por estação.
- As abas **Mapa** e **Estações** compartilham a mesma estratégia de evidência de interação baseada em conjuntos.
- Novos índices SQLite aceleram mensagens recebidas, ACK/REJ enviados e respostas a queries APRS.
- O diagnóstico registra a duração de cada geração do mapa, além de quantidade de estações, objetos e pontos de tracklog.
- O refresh completo do mapa passa a ocorrer a cada **15 segundos**; o tráfego/animação continua com atualização independente.
- O Client preserva o mapa já exibido quando o backend estiver ocupado preparando o primeiro snapshot.
- **TNC / RF mais leve:** a enumeração CIM/PowerShell deixa de rodar no polling periódico.
- A atualização automática das portas seriais usa fontes leves a cada **30 segundos**; a varredura completa permanece disponível em **Reescanear**.
- A identificação avançada de CH9102/CH340 e do Radtel RT-950 Pro da v1.8.7 é preservada.
- Inclui testes de concorrência para impedir que múltiplas chamadas pesadas de `map_data` voltem a saturar os workers do servidor.

## Novidades da v1.8.7

- **Descoberta serial avançada:** combina pyserial, Windows CIM/PnP e SERIALCOMM para encontrar portas COM que estejam visíveis ao Windows.
- Nova seção **Equipamentos seriais detectados** na aba TNC / RF, mostrando porta, descrição/equipamento, interface/chipset, fabricante, VID:PID, número de série/HWID e estado.
- Reconhecimento explícito de interfaces **CH9102/CH9102F/CH9102X, CH340/CH341, CP210x, FTDI e CDC/ACM**.
- **Porta COM editável:** além da seleção dos equipamentos encontrados, é possível digitar manualmente uma COM.
- Botões **Atualizar portas / Reescanear** e atualização periódica enquanto a aba TNC / RF estiver aberta.
- Um equipamento detectado pode ser selecionado diretamente pelo botão **Usar**, preenchendo a porta serial correspondente.
- **Radtel RT-950 Pro:** o Client só usa o nome do rádio quando os metadados do sistema realmente o identificarem; um CH9102 genérico não é automaticamente chamado de Radtel.
- Para **CH9102**, a interface mostra orientação condicional sobre o RT-950 Pro em **TNC UART**; quando o modelo for identificado, o baud rate é ajustado para **115200 bps**.
- A enumeração serial passa a ser registrada no diagnóstico com as diferentes fontes e metadados disponíveis.
- Inclui testes de regressão com **COM6/CH9102 e COM10/CH340 simultâneos**.
- Mantém integralmente os recursos de mapa da v1.8.6 e as rotas de mensagem APRS-IS/RF da v1.8.5.

## Novidades da v1.8.6

- Corrige a regressão em que **itens/camadas do mapa podiam desaparecer** após a v1.8.5.
- Restaura a geometria global estável do mapa, evitando alterações de altura de `header`, abas e `main` em telas baixas.
- Mantém a otimização para **1360×768** na aba Mensagens e no popup de estação sem interferir na área do Leaflet.
- **Mapa → Ver** é montado imediatamente com Estações, Digipeaters, iGates, Objetos APRS, Tracklogs, Enlaces RF, Enlaces iGate/APRS-IS e Pacotes em movimento.
- O mapa recalcula o viewport após redimensionamento/orientação e recarrega os itens visíveis.
- Inclui recuperação única de um estado de visibilidade totalmente desabilitado por regressão, sem desfazer um **Remover tudo** explicitamente acionado.
- O menu **Ver** permanece acessível mesmo durante uma falha temporária de `/api/map-data`.
- Preserva **Automático / APRS-IS / RF direto / RF personalizado** e path por mensagem da v1.8.5.
- Inclui testes de regressão específicos para os itens do mapa.

## Novidades da v1.8.5

- **Mensagens → Rota de envio:** Automático, APRS-IS, RF direto e RF personalizado.
- **Automático:** preserva APRS-IS como primeira escolha; RF direto é usado apenas quando necessário e disponível.
- **RF personalizado:** path por mensagem, como `WIDE1-1` ou `WIDE1-1,WIDE2-1`, validado antes do envio.
- As mensagens RF reutilizam o **TNC/KISS** existente e respeitam a política de TX do painel **TNC / RF**.
- O histórico mostra **APRS-IS ou RF** e o **path efetivamente usado**.
- O **Retry** preserva a rota original por padrão; uma rota explícita selecionada no compositor pode substituir a rota/path.
- **1360×768:** cabeçalho, aba Mensagens e popup da estação agora se adaptam melhor à altura disponível.
- O popup da estação usa rolagem interna e mantém as ações acessíveis em telas baixas.
- Traduções atualizadas em **Português, English, Español e Français**.
- Mantém integralmente alertas de CPU/RAM, Estatísticas, mapas/camadas, TNC/RF, atualização integrada e demais recursos da v1.8.4.

## Novidades da v1.8.4

- **Saúde do aplicativo:** monitora separadamente CPU/RAM do PT2VHF APRS Client e do sistema operacional.
- **Alertas críticos:** padrão de 90% para CPU e memória, exigindo 30 s de condição sustentada antes do popup.
- **Popup não bloqueante:** informa recurso, escopo, valor, limite, duração e horário, com acesso ao log de diagnóstico.
- **Antirruído:** histerese de 5 pontos percentuais e cooldown padrão de 10 min; após recuperação, um novo alerta exige novo período crítico sustentado.
- **Configuração:** limites, persistência, cooldown e ativação ajustáveis em **Saúde do aplicativo**.
- **Mapa:** barra contextual com Histórico, período/Completo, Ver, Velocidade, Tipo de mapa, Camadas e KML alinhada à esquerda.
- Novos textos traduzidos para **Português, English, Español e Français**.
- Mantém integralmente Estatísticas, TNC/RF, mapas/camadas, mensagens, atualização integrada e demais recursos da v1.8.3.

## Novidades da v1.8.3

- **Estatísticas → Software / dispositivos APRS:** filtros separados para **Aplicativos APRS**, **Dispositivos/Hardware** e **Não identificados**.
- O ranking e os percentuais são recalculados sobre o conjunto visível, permitindo analisar **somente aplicativos APRS**.
- Clientes como **PT2VHF APRS Client, UI-View, WinAPRS, APRSdroid e Dire Wolf** deixam de competir diretamente com rádios D-STAR, rigs, HTs e trackers quando o filtro de dispositivos está desligado.
- Itens ambíguos ficam como **Indeterminados**, evitando classificação forçada.
- **Mapa → Ver:** o antigo botão **Tudo** foi substituído por **Selecionar tudo** e **Remover tudo**.
- As ações globais incluem categorias, subcategorias e filtros dinâmicos, com persistência da escolha.
- Novos controles traduzidos em **Português, English, Español e Français**.
- Mantém integralmente a porta dinâmica, AIS, TNC/RF, mapas sem API key e demais recursos da v1.8.2.

## Novidades da v1.8.2

- **Porta local automática:** o cliente começa em **8080** e avança para 8081, 8082… quando encontra conflito, usando a primeira porta realmente disponível.
- A porta efetivamente escolhida aparece em **Configuração → Interface local** e é usada automaticamente pelo WebView/navegador.
- **Mapa → Ver → Objetos:** nova categoria **AIS**, separada de **Balão/Radiosonda**.
- **Mapa → Ver:** todos os itens continuam habilitados por padrão em novas configurações, sem sobrescrever escolhas já salvas.
- **Configuração:** removida a bandeira grande do seletor de idioma; permanecem o seletor compacto e as pequenas bandeiras do cabeçalho.
- A captura do Manual PDF e os launchers Windows/Linux/macOS acompanham a porta dinâmica.
- Mantém integralmente TNC/RF, Digipeater, iGate inteligente, mapas sem API key e traduções da v1.8.1.

## Novidades da v1.8.1

- Remove **Relevo sombreado** e mantém **Relevo com corte** como camada de elevação.
- Corrige **Claro/Escuro** para funcionar sem API key.
- Adiciona **CyclOSM, Humanitário/HOT, OSM.DE e ÖPNVKarte**.
- Adiciona fallback automático para OSM quando um provedor alternativo falhar.
- Revisa a aba **TNC / RF** em **Português, English, Español e Français**, incluindo textos dinâmicos e troca imediata de idioma.
- Mantém integralmente KISS Serial/TCP, Digipeater, iGate inteligente, grafo “Quem fala com quem” e segurança de TX da v1.8.0.

## Novidades da v1.8.0

### TNC / RF
- Nova aba **TNC / RF** para operar o cliente também com rádio local, sem substituir o APRS-IS.
- **KISS TCP** para Dire Wolf e outros modems compatíveis e **KISS Serial** para TNCs físicos.
- Detecção/listagem de portas seriais, baud rate, conexão/reconexão e estado TNC no cabeçalho.
- Monitor de frames **AX.25/APRS** recebidos e transmitidos, com origem, destino, path, tipo e representação TNC2.

### Digipeater
- Perfis **Fill-in (WIDE1-1)**, **Wide/Regional (WIDEn-N)** e **Personalizado**.
- Supressão de duplicatas por assinatura do pacote e janela temporal.
- Proteção contra loop, limite de hops e rate limit por estação.
- Fila de transmissão com prioridade para **ACK/REJ e mensagens** sobre telemetria/status repetitivos.

### iGate inteligente
- **RF → APRS-IS** com qAR e preservação do pacote recebido.
- **APRS-IS → RF** restrito a mensagens cujo destinatário tenha sido ouvido **diretamente por RF** dentro da janela configurada.
- Tabela própria de estações ouvidas por RF, distinguindo última audição direta de recepções posteriores via digi.
- Decisões de gating ficam registradas com o motivo de envio, bloqueio ou supressão.

### Quem fala com quem
- O cliente constrói um grafo de interações com origem, destino, meio RF/APRS-IS, quantidade, ACK/REJ e última atividade.
- Modos do otimizador: **Desligado**, **Observação/Recomendação** e **Automático conservador**.
- O modo automático atua em prioridades, duplicatas, gating e contenção de tráfego de baixa prioridade; **não cria um protocolo proprietário nem reescreve arbitrariamente paths APRS de terceiros**.

### Segurança operacional
- **TX automático, Digipeater e iGate Internet→RF ficam desligados por padrão.**
- Para liberar transmissão automática é necessário marcar uma confirmação explícita.
- O botão vermelho **PARAR TX** interrompe imediatamente novas transmissões automáticas sem derrubar a recepção TNC.
- O histórico de frames, decisões e relações fica no SQLite local com retenção configurável.

## Novidades da v1.7.7

- **Histórico:** fica somente na barra contextual do Mapa; o botão global antigo não é mais recriado durante o build.
- **Mensagens:** a ação vermelha **Apagar todas** passa a se chamar **Limpar**.
- **Topologia:** padrão amarelo (`#ffff00`) com **1 px**, a menor espessura disponível.
- **Tracklog:** permanece azul (`#3ba6ff`) por padrão.
- **Animação e som:** ativos por padrão em novas configurações.
- **Atualizações:** verificação automática da versão mais recente a cada **30 minutos**.

## Novidades da v1.7.6

- **Atualização automática Windows:** helper CMD nativo como caminho principal, com confirmação mais robusta antes de fechar o aplicativo.
- **KML:** abre **Salvar como** no aplicativo desktop para escolher pasta e nome do arquivo.
- **Mapa:** **Histórico** e **Exportar KML** ficam na barra contextual de Estações/Tracklog/Topologia.
- **Estatísticas:** novo ranking **Estações que mais interagiram**, considerando somente mensagens manuais entre operadores e excluindo tráfego automático.
- **Testes:** regressões cobrindo updater Windows, KML, barra do Mapa e ranking de conversas.

## Novidades da v1.7.5

- **Exportar KML** na barra superior, com Estações, Posições, Tracklogs e Topologia/enlaces selecionados por padrão.
- Rejeição de posições **0,0**, inválidas, saltos implausíveis e coordenadas incompatíveis com recepção RF observada por iGate conhecido.
- Novos blocos em Estatísticas: **Estações com problemas** e **Possíveis melhorias**.
- Digipeaters e iGates dos rankings são clicáveis e levam diretamente ao Mapa.
- Conversas agrupadas podem ser ordenadas por **Remetente** ou **Data**, com ordem crescente/decrescente.
- **Apagar todas** limpa somente o histórico local de mensagens, após confirmação.

## Destaques da v1.7 e da série 1.6

### Identidade visual
- A **logo APRS oficial enviada para o projeto** é a única fonte da identidade visual: cabeçalho, favicon, bandeja do Windows, ícones Windows/Linux/macOS e capa do Manual PDF.
- Todos os ícones de plataforma são derivados de `pt2vhf_aprs/static/img/app_logo.png`; não há desenho alternativo para macOS nem conversão de uma logo SVG diferente para o manual.
- O pipeline valida a presença e o formato PNG da logo antes de gerar os pacotes.

### Configuração
- Configuração organizada em seções, iniciando diretamente pela Estação APRS, sem bloco introdutório redundante.
- **Conectar ao iniciar** fica na seção APRS-IS e vem habilitado por padrão em novas instalações.
- Se houver alterações não salvas e o usuário tentar mudar de aba, o cliente oferece **Salvar e sair**, **Descartar alterações** ou **Cancelar**.
- Botão **Restaurar configuração padrão** sem apagar mensagens, estações, logs ou tracklogs.
- Chaveamento rápido de tema no cabeçalho.
- Idiomas **Português** (padrão), **English**, **Español** e **Français**, com seletor rápido no topo e persistência da preferência.
- A v1.7.1 amplia a cobertura de tradução de textos estáticos e dinâmicos e atualiza imediatamente as áreas dependentes do idioma.

### Identificação do próprio cliente
- As transmissões geradas pelo aplicativo usam o TOCALL experimental **APZVHF**, reservado aqui para identificar o **PT2VHF APRS Client** enquanto não houver uma alocação oficial específica.
- Isso permite que o ranking da aba Estatísticas acompanhe a quantidade de instalações observadas do próprio cliente.

### APRS-IS e filtros
- Servidor padrão do aplicativo: `soam.aprs2.net:14580`, com tentativa alternativa por `rotate.aprs2.net` quando aplicável.
- Novas instalações usam o filtro:
  `p/PP/PQ/PR/PS/PT/PU/PV/PW/PX/PY/ZV/ZW/ZX/ZY/ZZ`
- Filtros personalizados de instalações existentes são preservados.
- Editor gráfico combina:
  - filtro Brasil;
  - raio usando a posição da estação ou centro informado;
  - prefixos;
  - indicativos exatos;
  - área geográfica;
  - tipos de pacote.
- Interpretação de filtros conhecidos, aviso para componentes não representados, validação básica e botão **Copiar filtro**.

### Mensagens
- Conversas agrupadas podem ser ordenadas **A → Z** ou **Z → A** clicando em **Conversas**.
- Selecionar uma conversa preenche automaticamente o campo **Destino**, incluindo SSID; alterar o destinatário também sincroniza a conversa em foco, evitando divergência entre a conversa visível e o indicativo que receberá a mensagem.
- Os botões **Agrupado por remetente**, **Minhas mensagens** e **Não lidas** são compactos e mantêm seus rótulos em uma linha.
- Quando chega uma mensagem direta enquanto outra aba está aberta, a aba **Mensagens** fica destacada/pulsando até o usuário acessá-la.
- Em **Estatísticas → Estações mais ativas**, o indicativo é clicável e abre Mensagens com o destinatário já preenchido para resposta rápida.
- Mensagens longas são divididas sem `1/2`, `2/2` ou outros marcadores visíveis; as partes respeitam limites de palavra sempre que possível.
- O controle interno continua mantendo identificação de grupo e status agregado, como **2/3 confirmadas** ou **Todas confirmadas**.
- Retry individual de partes e retry automático configurável por timeout/número máximo de tentativas.
- Cada retry usa novo ID APRS.
- O peso de fonte configurado em Mensagens é aplicado também a **De**, **Para** e **Tipo**.
- Botão **Não lidas** para mostrar somente mensagens individuais recebidas ainda não lidas, inclusive no modo agrupado.
- O estado lida/não lida é persistido; **Ler mensagem**, seleção de conversa ou seleção explícita de mensagem atualizam esse estado.
- Estações favoritas recebem **estrela amarela** e ficam priorizadas nas conversas agrupadas e nas sugestões do campo Destino.

### Log
- A coluna **Hora** mantém data e hora em uma única linha.
- Clique em **Hora** para alternar entre mais antigos → mais recentes e mais recentes → mais antigos.
- Colunas e cabeçalhos usam alinhamento consistente.

### Mapa, Log e Estatísticas
- Mapas-base **OpenStreetMap, OpenTopoMap, Claro, Escuro, CyclOSM, Humanitário / HOT, OSM.DE, ÖPNVKarte e Esri World Imagery**.
- **Claro e Escuro não exigem API key**: usam tiles OpenStreetMap com tratamento visual local no cliente.
- Em **Camadas**, **Clima** permanece independente do mapa-base e **Relevo com corte** usa DEM real para destacar somente terreno a partir da cota selecionada.
- **Relevo sombreado foi removido na v1.8.1**.
- Se um mapa-base alternativo falhar repetidamente, o cliente volta automaticamente para **OpenStreetMap** e registra o evento no diagnóstico.
- O **Relevo com corte** possui slider vertical no lado direito do mapa, máximo padrão de 3.000 m configurável até 9.000 m e opacidade independente.
- A antiga área **Atividade** foi removida do Mapa. **Estações**, **Tracklog** e **Topologia observada** têm controles independentes de liga/desliga e período (**Completo, 1 h, 6 h, 24 h e 7 dias**), todos fora do canvas.
- O **Histórico/Replay** passa a ser um controle contextual logo abaixo das abas e só aparece quando o **Mapa** está ativo.
- Na v1.7.2, **Estações**, **Tracklog** e **Topologia observada** ficam na mesma linha contextual do **Histórico**, mantendo a barra compacta e liberando mais área útil para o mapa.
- O popup da estação mostra a data/hora da **Última recepção** acompanhada do tempo decorrido (minutos, horas ou dias), atualizado enquanto o popup permanece aberto.
- Tracklogs ignoram saltos de posição incompatíveis com deslocamento realista; o backend preserva a última posição válida e o mapa também quebra linhas históricas em saltos anômalos/relocações.
- A **Legenda** do Mapa pode ser minimizada/expandida; a preferência fica salva localmente para a próxima execução.
- Tracklogs automáticos de estações móveis.
- O popup da estação oferece **Mostrar log**, abrindo o Log já filtrado pelo indicativo/SSID.
- As estatísticas da rede ficam na aba **Estatísticas**, com **Completo** como período padrão, além de 1 h, 6 h, 24 h e 7 dias.
- Ranking de **estações mais ativas** por tráfego útil, excluindo telemetria, iGates e digipeaters; rankings dedicados de digipeaters e iGates, enlaces que deixaram de aparecer, comparação com o período anterior e métricas agregadas.
- **Ranking de software/dispositivos APRS** com nome amigável resolvido pela base APRS Device Identification, quantidade e percentual; o identificador técnico permanece interno e deixa de poluir a apresentação.
- A v1.7.2 consolida em uma única linha TOCALLs diferentes que resolvem para o mesmo nome amigável de software/dispositivo, recalculando quantidade e percentual sem misturar versões com nomes distintos.
- A v1.7.3 consolida também **versões e aliases da mesma família de cliente**. Ex.: **Dire Wolf 1.7, 1.8 e 1.9** aparecem como uma única linha **Dire Wolf**; nomes originais e TOCALLs continuam preservados internamente para diagnóstico.
- A aba **Estatísticas** usa fonte padrão ligeiramente maior e ganha controle próprio de tamanho da fonte em Configurações.
- O Mapa ganhou **legenda dos tipos de linhas**: tracklog, enlace RF, IGate/APRS-IS, replay temporal e pacote em movimento. Em qAR/qAO, o salto físico até o IGate é tratado como RF; o papel de IGate é mantido como metadado, não como meio do enlace.
- Animação do tráfego APRS em modos **Histórico** e **Ao vivo**, com Play/Pausa, início, avanço/recuo, velocidades 0,5x/1x/2x/5x/10x, timestamp e contadores. Em novas instalações, a animação **Ao vivo vem ativada por padrão**, podendo ser desativada em Configurações.
- Em pacotes com múltiplos enlaces observados, os segmentos podem ser animados simultaneamente, reproduzindo a propagação multi-hop.
- Cada transmissão recebida pode gerar som curto e destacar temporariamente em vermelho o marcador da estação de origem; som e destaque são configuráveis separadamente.
- Estações favoritas são persistidas e ficam fixadas no topo da aba Estações; a estrela também aparece no popup do mapa e na área de Mensagens.

### Queries APRS e diagnóstico
- No popup de cada estação no Mapa há botões para **Posição**, **Status**, **Ouvidos**, **Ping/ACK** e **Trace**.
- O Ping/ACK mede o tempo até a confirmação APRS e registra RTT/timeout.
- O Trace usa somente o caminho efetivamente recebido. Hops com posição conhecida são desenhados no mapa; os demais continuam listados como não localizados.
- Em Configuração é possível habilitar respostas automáticas a queries de posição, status e trace. O padrão é desligado para evitar transmissões inesperadas.
- O histórico de queries e respostas fica no banco local e é usado pelo diagnóstico do popup.
- O popup exibe uma área **Resultado da última query** com status, resposta, RTT e caminho do Trace, além do botão **Ver histórico de queries**.

- O indicador **Nova versão** pulsa quando há atualização disponível. O clique abre um modal persistente; a aplicação só encerra depois que o helper externo de atualização confirma que iniciou corretamente.

### Atualização integrada
- **Verificar atualizações automaticamente** — habilitado por padrão e executado na abertura e depois a cada **5 minutos**.
- Quando aparece **Nova versão**, clicar no indicador ou em **Baixar e instalar nova versão** inicia o fluxo automático.
- Na v1.7.3, o botão de instalação fornece feedback imediato e o gerador dos helpers PowerShell/Bash foi corrigido para gravar quebras de linha reais, evitando o caso em que o clique parecia não produzir efeito.
- Na v1.7.4, qualquer falha de atualização é mostrada **dentro do modal**, com o detalhe técnico preservado; o toast também fica acima do modal, sem desfoque, e os controles são reativados após o erro.
- O diagnóstico do updater registra solicitação, asset, URL, caminho temporário, tamanho, SHA-256 e erros de instalação.
- O cliente identifica **plataforma, arquitetura e formato em execução**, seleciona o asset exato da Release oficial, confere o tamanho e calcula **SHA-256**; quando o GitHub fornece digest SHA-256, o valor também é validado.
- Um **updater auxiliar separado** é iniciado antes do encerramento do processo atual. A aplicação tenta encerrar seus componentes de forma limpa; se a instância anterior permanecer viva após o timeout, o helper encerra somente o PID daquela instância antes de instalar.
- Um lock em arquivo com PID impede duas instâncias de iniciarem atualizações concorrentes e permite recuperar lock obsoleto após crash.
- **Windows Portable:** mantém backup para rollback, troca o executável pelo asset Portable e abre a nova versão.
- **Windows Setup:** executa o instalador correspondente com elevação/UAC quando necessária e relança a aplicação.
- **Linux:** AppImage e TAR.GZ são substituídos pelo novo binário; instalações DEB usam dpkg/pkexec quando disponível; a nova versão é relançada.
- **macOS:** o DMG é montado pelo updater, o bundle é substituído quando o local é gravável ou instalado em ~/Applications como fallback, e a nova versão é aberta.
- Configurações e banco SQLite ficam fora dos binários e são preservados. Em caso de falha antes da substituição, a versão funcional existente não é removida.

## Conexão e identificação

Para conectar ao APRS-IS são exigidos:
- Indicativo;
- Latitude;
- Longitude;
- Altitude.

O passcode APRS-IS é calculado automaticamente a partir do indicativo-base. O SSID não altera o passcode.

Se a geolocalização não fornecer altitude, o cliente pode usar **0 m** como contingência para não bloquear a conexão, mantendo aviso para o usuário informar o valor real. Ao transmitir beacon ainda com essa contingência, a transmissão é permitida e uma recomendação não bloqueante é exibida.

## Dados locais

O banco SQLite é mantido fora dos binários e preservado nas atualizações:

- Windows: `%LOCALAPPDATA%\PT2VHF APRS Client\data\pt2vhf_aprs.db`
- Linux: `~/.local/share/PT2VHF-APRS-Client/data/pt2vhf_aprs.db`
- macOS: `~/Library/Application Support/PT2VHF APRS Client/data/pt2vhf_aprs.db`

A exportação JSON de configuração pode conter o passcode APRS-IS em texto legível. Guarde o arquivo em local seguro.

## Linux

### AppImage
```bash
chmod +x PT2VHF_APRS_Client_x86_64_v1.6.1.AppImage
./PT2VHF_APRS_Client_x86_64_v1.6.1.AppImage
```

### Debian/Ubuntu
```bash
sudo apt install ./pt2vhf-aprs-client_1.6.1_amd64.deb
pt2vhf-aprs-client
```

### tar.gz
Consulte `docs/INSTALL_LINUX.md` para o fluxo portátil completo.

O workflow executa smoke tests no Ubuntu 22.04 e 24.04. Em desktops Linux com `notify-send`, mensagens pessoais podem gerar notificação nativa. No macOS, o cliente usa a notificação do sistema quando disponível.

## Política de versionamento

Após a **v1.6**, correções e melhorias incrementais seguem a série **v1.6.1, v1.6.2, v1.6.3, ...**. A passagem para **v1.7** somente ocorrerá mediante orientação explícita do mantenedor. Consulte `VERSIONING.md`.

## Segurança e assinatura

- A interface HTTP local escuta em `127.0.0.1`.
- Use somente arquivos publicados na Release oficial.
- Os builds podem permanecer sem assinatura/notarização de plataforma enquanto o projeto conclui esses processos; consulte `CODE_SIGNING_POLICY.md` e a documentação de instalação.
- Não desative mecanismos de segurança do sistema operacional globalmente para executar o cliente.

## Desenvolvimento

Validação local:

```bash
python -m compileall -q pt2vhf_aprs windows_app.py linux_app.py macos_app.py tools
python -m pytest -q
node --check pt2vhf_aprs/static/js/app.js
```

O workflow oficial também gera SBOMs, inventários de licenças e o manual PDF da versão.

---

**Por Alex, PT2VHF**


### Sobre e divulgação APRS
- Nova aba **Sobre**, com apresentação de **Alex, PT2VHF**, objetivo do projeto, link **tiny.cc/aprs**, WhatsApp **+55 61 98402-3634** e e-mail **alexpmr@gmail.com**.
- A aba acompanha o idioma corrente (**PT/EN/ES/FR**).
- O botão de divulgação prepara um **Announcement APRS BLNA** usando o indicativo/SSID corrente como remetente, mostra prévia, permite edição e exige confirmação explícita.
- O envio é manual e único; não existe repetição automática da divulgação.
