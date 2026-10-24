## 1.14.58 - 2026-10-24

- Retenção: **todos os itens passam a ser permanentes por padrão** — estações, digis, iGates, enlaces RF e Internet, objetos, tracklogs, mensagens, boletins, grupos, pacotes, log APRS, eventos de topologia e mapa de calor (Configuração → Retenção e tamanho do banco). "Restaurar padrões" volta para Permanente.
- Instalações existentes: categorias que ainda estavam no padrão antigo (30 ou 90 dias) passam a Permanente uma única vez; prazos que o usuário escolheu diferente do padrão são mantidos. Nenhum dado é apagado pela mudança.
- Mesmo critério para o cartão antigo "Saúde e retenção do banco" (antes 90 a 365 dias) e para o histórico do TNC (antes 14 dias; agora 0 = permanente, aceita até 3.650 dias).

## 1.14.57 - 2026-10-24

- **Corrigido (causa principal): enlaces de digis, iGates e estações fixas sumindo do mapa com o tempo** — desde a v1.14.44. A posição de cada ponta do enlace vinha do tracklog, aceitando só pontos de até 12 h antes/depois do pacote; mas o tracklog só ganha ponto novo quando a estação se desloca ≥ 10 m. Estação fixa tinha um único ponto (o da primeira escuta) e, passadas 12 h, nenhum enlace novo dela tinha posição — por isso um banco novo mostrava tudo e, com os dias, sobravam poucos enlaces (relato: 7 RF fixos e 4 iGate com 156 digis e 292 iGates). Agora, se a posição atual da estação continua a mesma do último ponto do tracklog (até 100 m), esse ponto vale para o enlace. Estação que mudou de lugar continua sem reaproveitar o ponto antigo.
- Na primeira abertura, os eventos já gravados sem posição são preenchidos uma única vez com essa regra (sem apagar nada) e as pontas novas entram no mapa de calor. "Reparar estrutura" no Verificar banco também refaz esse preenchimento.

## 1.14.56 - 2026-10-24

- **Corrigido: enlaces RF fixos, móveis e iGate sumindo do mapa.** O `aprslib` entrega o vento das estações meteorológicas (`_DDD/SSS`, ex.: `090/012` = 22 km/h) como rumo/velocidade, e iGates LoRa parados relatam `000/002` (3,7 km/h). Desde a v1.14.50, velocidade > 3 km/h em dois pontos do tracklog tornava a estação "móvel": iGates e digis fixos com meteorologia passavam a mostrar só o último contato por 3 h e seus enlaces iGate eram descartados — no relato, o mapa recebia 5 enlaces RF fixos com 158 digis e 290 iGates. Agora a velocidade só classifica como móvel se os pontos do tracklog estiverem espalhados por pelo menos 0,5 km, e o vento de estação meteorológica não é mais gravado como velocidade (estação e tracklog). Vale para bancos existentes, sem apagar nada.
- Configuração → **Verificar banco** ganha o item **Enlaces no mapa**: quantos enlaces RF fixos o mapa recebe e quantos ficam visíveis, RF móveis dentro do prazo de 3 h, iGate, e por que os demais ficam ocultos — ponta sem marcador no mapa (estação apagada pela retenção/limpeza ou sem posição atual), estação hoje a mais de 5 km da posição do enlace, inferido com mais de 250 km, ou estações tratadas como móveis (com exemplos). Mostra também o último evento RF com posição. Relato: enlaces RF fixos e móveis não aparecem mesmo marcados em Ver; não reproduzido com dados de teste, o diagnóstico mostra a causa no banco real.

## 1.14.55 - 2026-10-23

- Mapa → Ver → **Planejamento** (portado do PT2VHF Mesh Analyzer v0.6.41–v0.6.43, adaptado ao APRS):
  - **Analisar enlace entre 2 pontos:** clique em dois pontos do mapa, digite coordenadas ou um indicativo (ou use a própria estação). Perfil de altimetria com curvatura da Terra (k = 4/3), linha de visada e 1ª zona de Fresnel; perda em espaço livre, perda por obstrução (difração Deygout, ITU-R P.526), sinal estimado no receptor em dBm, µV e unidades S (S9 = −93 dBm em VHF), margem sobre a sensibilidade para decodificar 1200 bps (padrão −113 dBm ≈ 0,5 µV) e veredito Viável / Marginal / Inviável com o motivo; pior obstáculo marcado no mapa; altura de antena que libera 60% da zona de Fresnel; quando as duas pontas são estações, mostra se uma já ouviu a outra por RF. Padrões: **145,570 MHz** (frequência APRS no Brasil), 25 W, antenas de 3 dBi a 10 m, 1 dB de cabo — todos editáveis. Pontos arrastáveis. PDF.
  - **Melhor ponto para instalar estação:** desenhe a área no mapa (Ctrl+Z desfaz; feche no primeiro vértice, com duplo clique ou em Concluir; vértices editáveis). Os topos de morros diferentes aparecem numerados do mais alto para o mais baixo no mapa e na tabela (altitude, desnível, distância, direção e coordenadas), com indicação de ponto na borda da área, referência opcional (centro, minha estação, ponto do mapa ou indicativo), enlace de cada ponto, surveys salvos, CSV e PDF com mapa de relevo, tabela e perfis.
  - Elevações dos tiles de terreno Terrarium (AWS Open Data, base SRTM, ~30–40 m), guardados em `terrain-tiles/` na pasta de dados para uso sem internet; Open-Meteo como alternativa; mensagem de erro com o motivo real.
- Aplicativo de desktop (Windows, Linux e macOS): salvar PDF com diálogo nativo (`save_binary_file`).
- Nova dependência: `reportlab` (PDF).

## 1.14.54 - 2026-10-22

- TNC (#118): novo cartão **Teste de recepção (não transmite)** na aba TNC / RF. "Escutar agora" ouve por 10, 20 ou 30 s e explica o resultado: nada recebido (cabo/porta, modo KISS, velocidade serial, RTS/DTR, frequência), texto legível (TNC em modo terminal), bytes ilegíveis (velocidade serial errada, com as alternativas comuns), KISS sem AX.25 válido ou pacotes válidos (lista os primeiros). Com o TNC conectado, observa a sessão atual sem reabrir a porta; desconectado, abre a porta só para ler. O teste antigo lia apenas os bytes já disponíveis no instante da abertura e quase sempre retornava zero.
- TNC: **Monitor de bytes ao vivo** — mostra cada bloco recebido (ASCII + HEX), cada pacote AX.25 decodificado e cada frame inválido, atualizado a cada segundo (últimos 300 eventos em memória).
- Configuração → Retenção e tamanho do banco: botão **Verificar banco** — integridade do arquivo (quick_check), tabelas e colunas exigidas pelo mapa, quantos eventos de enlace têm posição para serem desenhados (total e últimas 24 h), enlaces RF cuja origem não tem posição, último pacote e espaço livre. Explica por que enlaces podem não aparecer sem precisar apagar o banco. Quando falta estrutura ou geometria, **Reparar estrutura** recria tabelas/colunas/índices ausentes, refaz o preenchimento de posição dos eventos, REINDEX e ANALYZE — nenhum registro é apagado.
- Backlog: Automações/Auto-resposta (#125), LEDs TX/RX (#124) e Grid Locator (#106) já estavam implementados desde a v1.14.40–v1.14.46; títulos de pendência atualizados.
- CI: geração do manual em PDF fixada em Ubuntu 24.04 (a migração de `ubuntu-latest` para Ubuntu 26 quebrou o passo) e anotação do comando que falhar.

## 1.14.53 - 2026-10-22

- Mapa de calor da Cobertura RF com armazenamento e retenção próprios: nova tabela `rf_coverage_cells` (células de ~1 km por dia UTC, com TX/RX), alimentada a cada evento RF e preenchida uma única vez a partir do histórico de `topology_events` (~3 s para 100 mil eventos). Novo item **Configuração → Retenção → "Mapa de calor (cobertura RF)"** (padrão Permanente), independente de tracklogs, estações, digis, enlaces e eventos de topologia; também em "Limpar tudo" e nas Estatísticas por categoria.
- Mapa de calor: cada ponto passa a cobrir **5 km de diâmetro** (raio geográfico de 2,5 km, antes 1,5 km) ao redor de estações, digis e trackers; limite de tela ampliado para 320 px para manter o tamanho real com zoom próximo; degradê mais cheio até a borda.
- Corrigido (desde a v1.14.44): a tela de retenção iterava um único elemento — não exibia os valores salvos (todas as categorias apareciam como "24 horas") e o botão **Salvar** falhava.

## 1.14.52 - 2026-10-21

- Mapa de calor da Cobertura RF no estilo clássico: densidade acumulada colorida pela paleta azul → ciano → verde → amarelo → laranja → vermelho; raio geográfico de ~1,5 km por ponto (5 a 40 px conforme o zoom), em vez de 20–76 px fixos; removida a mistura `screen` que desbotava as cores. Legenda "Cobertura RF: baixa → muito alta".
- Atualizações: ao detectar versão nova, além do indicador no cabeçalho, abre o aviso perguntando "Deseja atualizar agora?" com Baixar e instalar / Ver Release / Depois. "Depois" adia a mesma versão por 24 h; não sobrepõe outro aviso aberto.

## 1.14.51 - 2026-10-21

- Mapa: **Cobertura RF (mapa de calor)**. Ao habilitar a opção no menu Ver, o mapa mostra um mapa de calor com todo ponto onde houve ao menos uma transmissão RF (posição de quem transmitiu um salto) ou recepção RF (posição de quem ouviu ou repetiu), usando as coordenadas do momento de cada pacote em `topology_events`, diretas ou inferidas pelo path. Pontos agregados em células de ~1 km com peso logarítmico; APRS-IS puro e coordenadas APRS inválidas (#121) não entram. Antes a opção mostrava só pontos de digipeaters móveis, como círculos.
- Menu Ver: a segunda opção "Cobertura RF" (v1.42, que só usava pacotes do TNC local e ficava vazia com tráfego APRS-IS) foi removida; quem a tinha ligada continua com a cobertura ligada. Contagem de pontos exibida.

## 1.14.50 - 2026-10-21

- Mapa (#116): tracker circulando dentro de uma cidade (ex.: Ceilândia → digi na Asa Norte) deixava uma linha RF fixa para cada ponto do trajeto. A detecção de móvel exigia deslocamento ≥ 25 km; agora uma estação com pelo menos 2 pontos de tracklog acima de 3 km/h também é móvel e mostra só o último contato como RF móvel, com TTL.
- Mapa: rede de segurança — para cada origem → destino → tipo, apenas o segmento do contato mais recente é desenhado, com a geometria desse contato. Substitui a regra da v1.14.35 de um segmento por região visitada; o histórico continua no SQLite e nas contagens de pacotes.

## 1.14.49 - 2026-10-20

- Mapa (#116): estações móveis que só transmitem (trackers, ex.: PU2CAR-9 ouvido por um digi fixo) passam a mostrar o enlace do **último contato RF válido**, na posição daquele momento, como RF móvel, com o TTL configurável (padrão 3 h) e o filtro Ver → Enlaces móveis. Antes eram descartados por completo e só apareciam durante a animação de tráfego. Contatos antigos continuam somente no SQLite, sem linhas "aranha". Substitui a regra anterior da #94 para trackers, por decisão do mantenedor.
- Menu Ver: contagem em Tracklogs, Enlaces RF fixos, Enlaces móveis e Enlaces iGate / APRS-IS, calculada com os mesmos filtros do mapa e exibida mesmo com a camada desmarcada; um "0" distingue camada sem dados de camada desligada.
- Diagnóstico: erros de JavaScript do navegador/WebView e um resumo da renderização do mapa (navegador, canvas, caixas do menu Ver, enlaces e tracklogs recebidos e desenhados) passam a ser registrados no `diagnostics.log` (`client_js_error`, `client_map_render`), para investigar o computador Windows 10 em que tracklogs e enlaces fixos não aparecem.

## 1.14.48 - 2026-10-19

- Mapa offline: `leaflet.js` 1.9.4 (mesmo hash SRI do CDN) e imagens incluídos em `static/vendor/leaflet`; o mapa deixa de depender do unpkg.com. `.gitattributes` impede conversão CRLF que quebraria o SRI no Windows.
- TNC serial (#118): novas opções Linha DTR / Linha RTS (Padrão, Ativada, Desativada), aplicadas antes de abrir a porta para não gerar pulso de PTT; estado DTR/RTS/CTS/DSR/CD/RI na aba TNC, no status e no diagnóstico. O padrão mantém o comportamento anterior.
- Posições APRS inválidas (#121): migração única e reversível coloca em `position_quarantine` os tracklogs gravados a partir de pacotes DDMM malformados (ex.: PP5BLU-15) e substitui a posição contaminada da estação pela última posição válida, ou nenhuma; `packets` não é alterado e `restore_quarantined_positions()` desfaz.
- Atualizador Setup (#103): instalador executado com `/LOG`; relançamento a partir da pasta registrada pelo Inno Setup; sucesso declarado somente quando a instância nova confirma a versão alvo. Falso sucesso vira `version_mismatch`, exposto em `/api/update-status` e avisado na interface.
- Recordes RF (#86): ordenação alternável entre distância entre extremidades e percurso total (soma dos saltos); o título declara a métrica.
- Mapa/AIS: o enriquecimento dos popups AIS (foto e dados da embarcação) nunca era instalado, porque `window.map` ainda era o `<div id="map">` quando os complementos v110/v142 rodavam e `.on` falhava (`map.on is not a function`). Agora aguardam o mapa Leaflet real.
- Manutenção: topologia espaço-temporal ligada explicitamente em `database.py` (sem substituição de funções em tempo de execução; ~310 linhas de código morto removidas); teste desatualizado que bloqueou o build da v1.14.47 corrigido.
- Inclui as mudanças da v1.14.47 (#128, #99), cujos pacotes não chegaram a ser publicados porque o CI falhou.
- **Validação física pendente:** RX do RT-950 Pro na COM10 com DTR/RTS desativadas (#118), atualização Setup no Windows 10 afetado (#103), migração no banco real do PP5AU (#121) e enlaces órfãos (#116), que depende do banco real.

## 1.14.47 - 2026-10-19

- Cabeçalho (#128): versão com mesma fonte, tamanho e peso do título PT2VHF APRS Client, incluindo comportamento responsivo; versão da aba Sobre permanece inalterada.
- Interface Web (#99): remoção dos prefixos visíveis "Web em uso", "Web LAN" e "Web local" do endereço IP:porta no cabeçalho. Indicação de sessão remota em laranja e diagnóstico no tooltip preservados.
- Downloads: tabela inicial do README continua mostrando exclusivamente os contadores de cada arquivo da versão publicada.
- Testes de regressão de HTML/CSS/JS e compilação multiplataforma pelo CI.
- Permanecem abertos: comunicação serial COM10 com Radtel RT-950 Pro (#118), enlaces RF órfãos (#116) e atualizador Portable em máquinas afetadas, pendentes de testes físicos.

## 1.14.46 - 2026-10-18

- Automações: nova aba principal com **Auto-resposta**, migrada da configuração antiga, preservando habilitação, texto e janela de proteção no SQLite.
- Auto-resposta: mensagens privadas distintas disparadas seguidamente recebem respostas; retransmissões duplicadas são filtradas, com limite antialagamento e bloqueio de respostas automáticas reconhecidas.
- Barra superior: indicadores compactos **TX ○ RX ○** que utilizam contadores APRS-IS e TNC, flashes independentes para TX e RX, baseline no primeiro status e tooltip por transporte.
- APRS: rejeição preventiva de posição não comprimida cujos minutos sejam >=60, incluindo o pacote real de PP5BLU-15, em APRS-IS e TNC; preservar payload bruto e histórico auditável, evitando atualização da posição e novos eventos topológicos contaminados.
- Topologia: omitir da camada de mapa eventos legados cujo pacote bruto original possui minutos APRS inválidos; nenhuma remoção em massa de SQLite.
- Novos testes de regressão sobre automações, quadro APRS inválido, RX/TX agregados e dados históricos.
- **Pendente no hardware e em campo:** COM10 Radtel RT-950 Pro (#118), validacão abrangente de enlaces órfãos (#116), saneamento assistido de posições antigas, updater portátil e demais itens não selecionados do backlog.

## 1.14.45 - 2026-10-18

- Regressão visual corrigida (#122): RF comum volta a usar a cor e a espessura configuradas, com **traço contínuo** mesmo quando inferido pelo path.
- Internet/iGate permanece tracejado e usa cor independente; RF móvel e temporário preservam seus estilos próprios.
- A classificação de RF inferido permanece explícita no popup/hover e nos metadados; não se promove RF não confirmado a enlace diretamente ouvido.
- Testes automatizados adicionais protegem os estilos de RF/Internet e o contraste no mapa.
- **Pendentes:** validação visual no banco real; coordenadas APRS malformadas (#121), TNC COM10 PP5AU (#118) e enlaces órfãos (#116) continuam abertos.

## 1.14.44 - 2026-10-18

- Beacon manual (incluindo ícone de cabeçalho) e automático: despacho para todos os meios ativos e autorizados, APRS-IS e KISS/TNC/RF, com resultado independente por transporte; RF enfileirado não implica confirmação de irradiação.
- Botão manual sem cooldown; agendamento também funciona com TNC como único transporte ativo. Cabeçalho TCPIP* da Internet nunca é reutilizado no AX.25 RF.
- Radtel RT-950 Pro: novo perfil KISS UART com sugestão 115200 bps por seleção explícita, sem alteração automática de configuração persistida; diagnóstico de porta aberta sem RX permanece disponível.
- Enlaces órfãos: RF inferido apenas do APRS-IS que não coincide com posições atuais dos dois marcadores deixa de ser desenhado na visão geral; evidências/eventos permanecem acessíveis na API e no histórico/rotas.
- Testes automatizados específicos de beacon multicanal, falhas parciais, KISS, configuração serial e geometria histórica.
- **Pendências não encerradas:** teste físico RT-950 Pro de PP5AU na COM10; evidência visual de enlaces órfãos em Brasília, avaliação de mais itens do backlog e validação de instaladores no Windows real.

## 1.14.43 - 2026-10-18

- Enlaces RF móveis: somente a observação válida mais recente por estação móvel, sem linhas históricas acumuladas, com geometria do evento e expiração independente.
- Configuração > Mapas: tempo de vida de enlaces móveis (0,25 a 168 horas; padrão 3 horas), cor e espessura próprias.
- Ver > Enlaces móveis: nova categoria opcional, com visibilidade persistida e legenda separada de RF fixo/temporário.
- Testes de regressão: chegada fora de ordem, TTL, path inferido, ausência de coordenadas, direção invertida, configuração e camada visual.
- Requer validação de campo com exportação da base que originou os enlaces órfãos.

## 1.14.42 - 2026-10-17

- Atualizador portátil Windows: reinicializar ambiente PyInstaller ao abrir a nova versão; limpar referências ao runtime temporário anterior e restaurar a busca nativa de DLLs no helper.
- Preservados o backup, a confirmação de saúde HTTP e o rollback da atualização portátil.
- Testes de regressão de RF temporário, Grid Locator, layout, mensagens e atualização; smoke HTTP e matriz de migração SQLite.
- Limitações: confirmação física do erro de DLL, rádios e acesso LAN externo permanecem pendentes; esta versão não encerra integralmente o backlog.

## 1.14.41 - 2026-10-16

- Mapa: enlace RF temporário com cor ciano e espessura 3 px por padrão, configuráveis, validade de 3 h desde o último contato direto; novo contato renova o prazo e linhas expiradas saem do mapa sem refresh.
- Topologia: incorpora correções de filtragem de digi/trackers móveis, histórico geográfico e bloqueio de linhas sintéticas; preservar dados para Cobertura RF observada.
- Estação: modo Grid Locator Maidenhead (4/6/8/10 caracteres), conversão bidirecional e aplicação explícita do centro da célula sem alterar precisão só por trocar o modo.
- Interface: CPU e RAM empilhados no cabeçalho; busca RF compactada em uma linha no desktop.
- Diagnóstico: fallback seguro da pilha de certificados do Windows nos downloads do atualizador.
- Testes automatizados de regressão para RF temporário, trackers móveis, layout e Grid Locator.
- **Pendências conhecidas:** não representa solução integral do backlog; requer validação física de rádio/APRS, histórico de cobertura RF e atualização em máquinas com falha, Web LAN e outras issues abertas.

## 1.14.40 - 2026-10-15

- Mapa: remover os controles duplicados de Velocidade e Tipo de mapa da barra principal; conservar o tipo de mapa em Configuração > Mapa e transferir a velocidade da animação para o mesmo bloco.
- Apresentação: o botão passa a alternar entrada e saída, permanecendo acessível em tela cheia; ESC permanece compatível.
- Interface: melhorar quebra de linha e organização responsiva da barra do mapa.
- Regressão: adaptar as verificações automatizadas à nova localização dos controles.
- **Limitações conhecidas:** a identificação contextual do controle “OPÇÃO” e sua inclusão dentro de Histórico ainda requer validação na interface em execução; testes reais de RF, LAN e Windows Legacy seguem pendentes.

## 1.14.39 - 2026-10-14

- Recordes RF observados: remover o prazo absoluto de 45 s dos jobs de cálculo em segundo plano, incluir botão X para cancelamento efetivo, tempo decorrido e ETA baseado na evolução de cada fase; polling com timeout mais tolerante.
- Estatísticas: novo resumo por categoria com quantidades de estações únicas, mensagens RX/TX, boletins, grupos, objetos APRS, pacotes, pontos de tracklog, digis, iGates e enlaces. Endpoint independente da análise pesada de Recordes RF.
- Configurações/Retenção: realçar categoria Pacotes (já existente), adicionar botões Limpar tudo por categoria, prévia, confirmação expressa e limpeza assíncrona em lotes, preservando as demais categorias, políticas e mensagens TX pendentes.
- Mapa/Topologia: ocultar na vista geral enlaces RF associados a repetidores com deslocamento confirmado por evidências geográficas múltiplas; dados históricos permanecem intactos.
- Camada Ver > Cobertura RF observada: amostras por célula de digipeaters móveis, separando RF direto e inferido e sem interpolar cobertura não amostrada.
- Testes de regressão de processamento, estatísticas, retenção e mapa. A confirmação operacional em bancos reais grandes continua sendo necessária.

## 1.14.38 - 2026-10-14

- RF no mapa: todo enlace classificado como RF exibido usa linha contínua, cor e espessura das Configurações; Internet/iGate continua tracejada e com cor própria.
- RF inferido e RF legado mantêm classificação auditável nos detalhes. Continua ativo o bloqueio visual de hops inferidos >250 km sem comprovação; sem regressão para digipeaters móveis PT2AP.
- Atualizador: diagnóstico por categoria (TLS/certificado, DNS, timeout, HTTP 403 e indisponibilidade), sem ocultar o erro original; opção de retentativa manual.
- HTTPS: duas consultas ao endpoint GitHub com timeout moderado e, no Windows, fallback seguro via PowerShell/.NET com certificados/proxy do sistema operacional, sem desabilitar TLS.
- Fallback final à página oficial do GitHub identifica somente a tag; sem metadados de assets, instalação automática é corretamente bloqueada.
- Testes regressivos para erros SSL, Win10, publicação limitada, classificação RF e preservação da verificação segura. O sucesso real em Windows 10 recém-instalado depende de novo teste na máquina afetada.

## 1.14.37 - 2026-10-14

- Novo botão Caminhos possíveis: busca explícita origem-destino fora do ranking de Recordes RF.
- Resultados separados: mesmo pacote/path, eventos contemporâneos, alcançabilidade histórica compatível e hipótese sem prova conjunta.
- Digis móveis: posição histórica incompatível entre dois contatos reais RF é bloqueio, não prova de rota interestadual contínua.
- Alertas para saltos longos inferidos, observações afastadas no tempo e ausência de geometria do evento.
- Hipóteses não viram linhas no mapa nem registros de enlaces no SQLite.
- Ranking atual continua classificado pela distância entre extremidades; seletor de ordenação por soma de hops permanece no backlog.
- Regressões sintéticas incluídas; validação com histórico RF de campo e com instalações Windows permanece necessária.

## 1.14.36 - 2026-10-13

- Mapa RF: segmentos inferidos a partir de paths APRS-IS aparecem em cinza tracejado e não são apresentados como RF direto comprovado.
- Mapa geral: hops inferidos sem evidência direta e com separação geográfica acima de 250 km não recebem linha reta; permanecem no histórico e podem ser analisados ao selecionar explicitamente a rota. O limiar é apenas visual, não um limite físico de propagação.
- Eventos: cálculo de confirmação RF considera todos os registros do segmento, incluindo quando coexistem evidências inferidas e recepção via TNC.
- Topologia: impede traçados com coordenadas históricas nulas convertidas inadvertidamente em 0/0.
- Configurações APRS-IS: novas instalações usam `r/4000`, expandido para `r/latitude/longitude/4000` com base na estação. Filtros já salvos permanecem inalterados.
- Navegador: diagnóstico específico quando HTTP na rede local impede geolocalização sem HTTPS ou localhost.
- Regressões: LU9DCE ↔ PU2XTC-4, digipeater móvel, caminhos inferidos, evidências mistas, filtro radial e matriz de compilação.

## 1.14.35 - 2026-10-12

- Mapa/topologia: corrigido o efeito elástico dos enlaces de digipeaters e iGates móveis, exemplificado pelo PT2AP com Starlink ao viajar do Sul a Brasília.
- A API /api/topology usa coordenadas históricas de topology_events, não GPS atual de stations; enlaces legítimos RF permanecem ancorados onde realmente ocorreram, com segmentos independentes por localidade.
- Preservada distinção entre RF via TNC, RF inferido pelo path e Internet/APRS-IS. Sem posição histórica válida, a aresta permanece no banco mas não é desenhada artificialmente no mapa.
- Popup/hover passam a indicar geometria histórica e momento de observação; chave dos segmentos impede colisões na mesma dupla em lugares diferentes.
- Exportação KML e JSON de diagnóstico passam a oferecer geometria histórica coerente com o mapa.
- Suíte de testes: PT2AP no Sul/Uberaba/Brasília, evidência por SSID e meio, coordenadas ausentes e endpoint Flask real.
- A regressão real fica aberta até validação em campo com o banco original da estação; outras pendências históricas seguem documentadas.

## 1.14.34 - 2026-10-12

- Atualizador Windows Portable: retentativas de backup/substituição em caso de arquivo bloqueado; confirmação de que o servidor do novo executável iniciou e tentativa de recuperação automática da versão anterior.
- Inicializador Windows: grava sinal de prontidão para o helper de atualização somente após o servidor HTTP local estar disponível.
- Janela integrada: se pythonnet/CLR falhar, registrar a falha e oferecer navegador funcional sem diálogo modal .NET bloqueante; criação do WebView também protegida por fallback.
- Bandeja de notificações: nova imagem APRS de alto contraste, fundo opaco e tamanho útil, gerada separadamente do ICO de atalhos, com logs de fallback.
- Mensagens programadas: painel inline convertido em modal responsivo; novos agendamentos, edição e gerenciador de listas somente sob demanda; proteção contra perda de alterações não salvas, foco e teclado.
- Mantidas as correções de Web LAN e Configuração realizadas na v1.14.33.
- Aviso: migração a partir de v1.14.31 Portable pode exigir atualização manual inicial, porque seu helper antigo permanece instalado naquela versão.
- Pendente de comprovação física: erro .NET/pythonnet em máquinas específicas, problema de cleanup _MEI do PyInstaller e popup intermitente Win7. Não considerar sanados apenas pelo sucesso dos builds.

## 1.14.33 - 2026-10-12

- Configuração: restaurado o controle visível para silenciar ou reativar avisos de estação nova (station_appeared), preservando salvamento imediato no backend.
- Windows: ícone multirresolução APRS com lettering grande e contraste, incluindo bandeja de notificação e atalhos.
- Web: abertura do navegador pelo IP da rede local e porta efetiva quando LAN está ativa e acessível; fallback seguro em localhost.
- Novas instalações: acesso Web LAN habilitado por padrão; opção de abrir uma aba adicional no navegador permanece desligada. Preferências já gravadas preservadas.
- Atividade Web: sessões remotas visíveis identificadas por heartbeat, indicador IP ampliado e destaque laranja/preto enquanto houver usuário ativo; expiração em 75 s, sem confundir último acesso com sessão presente.
- Endpoints Web, testes de regressão, traduções e pipeline multiplataforma sincronizados.
- Observação: validação em hardware Win7 real e regressão conhecida do atualizador Windows 11 permanecem em investigação.

## 1.14.32 - 2026-10-12

- **Interface Web LAN:** validação real do usuário com dois computadores Windows 11; funcionou pelo loopback, pelo IP LAN do host e pelo acesso remoto na rede privada. Issue #76 encerrada neste cenário.
- **Verificação automática de HTTP:** smoke real contra backend Flask/Waitress com HTML, JavaScript, ping da API/versionamento e endpoint de prova; integrado aos builds Windows modernos e Windows 7 Legacy em Python 3.8.
- **Windows 7 Legacy:** preservado o runtime separado, instalador e Portable x64, provas de versão do executável e do aplicativo instalado, sem exigir WebView2.
- **Documentação:** atualizado o procedimento de acesso Web LAN no Windows 7 e retirada a falsa classificação de falha de acesso no Win11.
- **Pendências distintas preservadas:** janelas transitórias em Windows 7 e regressão de atualização/boot PyInstaller/pythonnet em Windows 11 exigem teste físico e diagnóstico adicional; **esta release não reivindica correção dessas ocorrências**.
- **Pacote completo:** Windows x64/ARM64, Win7 SP1 x64 Legacy Setup/Portable, Linux x86_64/ARM64, macOS Intel/Apple Silicon e Manual PDF, sujeito à publicação do workflow após CI.

## 1.14.31 - 2026-10-12

- **Windows 11/7 — acesso Web LAN:** a liberação do Firewall deixa de executar duas solicitações UAC concorrentes; usa uma única operação elevada que substitui a regra anterior e instala a porta TCP efetiva, limitada a `LocalSubnet`. A regra não fica mais vinculada ao caminho do EXE, que pode mudar no Windows Portable.
- **Perfis de rede:** a regra de acesso local limitada à sub-rede funciona também quando o Windows marca a rede como Pública, sem exigir a desativação do firewall. O compartilhamento continua desligado por padrão e requer autorização explícita do usuário via UAC. Recomenda-se apenas LAN confiável.
- **Detecção IPv4:** apresenta endereços alternativos quando o host possui Wi-Fi, Ethernet, adaptador virtual ou VPN.
- **Diagnóstico efetivo:** `/api/local-interface/remote-probe` permite confirmar HTTP em outro computador. O servidor só informa acesso externo confirmado se receber solicitação real com IP não-loopback; detectar IP e conectar pelo próprio host não basta.
- **Interface:** distingue URL informativa de URL realmente compartilhável, alerta para reinício total após habilitar LAN e orienta a testar portas/endereços disponíveis.
- **Win7 Legacy:** mantém correção para executar `netsh` sem console visível e cache de 60 segundos. Acrescenta monitor nativo temporário `EnumWindows` que registra janelas transitórias dos processos filhos no diagnóstico para investigar o popup externo ainda não identificado.
- **Banco SQLite:** preserva todas as políticas de retenção por categoria e o histórico de enlaces RF independentes da expiração dos nós.
- **Testes:** operação única de Firewall, porta exata, cache, evidência externa, bind real em `0.0.0.0`, regressão Windows 7 e documentação.
- **Regressão histórica:** atualizado o teste da v1.14.28 para diferenciar o IP meramente detectado da URL compartilhável apenas em modo LAN. Testes físicos de Win7 e acesso entre dois computadores permanecem necessários antes de fechar as ocorrências de campo.
- **Documentação:** manual PDF revisado com procedimentos para liberar a porta e testar a partir de outro computador na mesma LAN.
- **Entrega completa:** Windows 11 x64/ARM64 (Setup e Portable), Windows 7 Legacy x64 (Setup e Portable), Linux x86_64/ARM64 (AppImage, DEB, TAR), macOS Intel/Apple Silicon (DMG), SBOM/licenças e Manual PDF.

## 1.14.30 - 2026-10-12

- **Web LAN funcional e diagnóstico:** a opção LAN continua exigindo salvamento e reinício, mas o novo teste verifica o socket no IPv4 LAN e na porta efetiva, distinguindo bind confirmado, restrição a localhost e reinício pendente; não confunde teste local com confirmação externa.
- **Firewall Windows:** regra restrita ao perfil Privado, sub-rede local, porta e executável da edição em uso. Diagnóstico identifica regras antigas de outra versão/porta.
- **Windows 7 Legacy Portable:** correção de falso erro `Shell encerrou imediatamente (exit=0)` quando Chromium repassa `--app` a um processo existente.
- **Retenção SQLite:** seção em Configuração para retenção por categoria: estações, digipeaters, iGates, enlaces RF, enlaces Internet/iGate, objetos APRS/AIS/radiossondas, tracklogs, mensagens individuais, boletins, mensagens de grupo, pacotes, logs APRS e eventos de topologia.
- **Permanente e histórico:** RF/digipeaters/iGates permanentes por padrão. Links históricos independentes dos registros de nós; remoção de estação não executa cascata sobre `topology_edges`.
- **Capacidade:** tamanho do banco no painel, políticas salvas, limpeza manual confirmada e manutenção em pequenos lotes com worker em segundo plano; nenhuma compactação bloqueante automática.
- **Migração conservadora:** bancos com dados existentes precisam de ativação explícita da primeira limpeza automática; novas instalações podem usar o agendamento padrão.
- **Testes:** regressões SQLite, isolamento de categorias, proteção de enlaces, diagnóstico LAN e handoff Chromium no Windows 7. Acessibilidade entre duas máquinas depende também do firewall e da rede reais e permanece sujeita à validação física.
- **CI:** asserção histórica da v1.14.26 alinhada à assinatura atual de diagnóstico LAN, preservando as verificações de regressão.
- **Gate de release:** testes automatizados de retenção com nós expirados/enlaces preservados, diagnóstico de bind LAN, sintaxe JavaScript e handoff Win7; builds e manual condicionados a CI verde.
- Release completa: Windows x64/ARM64, Windows 7 Legacy x64 Setup/Portable, Linux x86_64/ARM64, macOS Intel/Apple Silicon e Manual PDF.

## 1.14.29 - 2026-10-11

- **IP LAN independente do bind:** o cliente passa a detectar `lan_ip` mesmo quando o servidor está restrito a `127.0.0.1`.
- **Novo `display_url`:** endereço informativo separado da URL interna e da URL realmente compartilhável.
- **Cabeçalho:** quando existe IPv4 LAN válido, exibe o IP real da máquina, por exemplo `192.168.10.2:8080`, em vez de `127.0.0.1:8080`.
- **Semântica preservada:** `share_url` só aponta para a LAN quando o servidor realmente está acessível pela LAN; `scope` continua indicando acessibilidade real.
- **Instalações existentes:** a detecção do IP real não depende de recriar banco/configuração.
- **Regressões:** testes cobrem bind localhost com IP LAN detectado e bind `0.0.0.0` com URL compartilhável.
- Mantidas as correções da v1.14.28 e do Windows 7 Legacy.
- **Gate de release:** publicação condicionada aos testes v1.14.29, incluindo bind localhost com `display_url` no IPv4 LAN real.
- Release completa para Windows x64/ARM64, Windows 7 SP1 x64 Legacy, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.28 - 2026-10-11

- **Cabeçalho Web:** removido o texto literal `\\n` que aparecia entre o endereço e os controles.
- **Sem botão de copiar:** removidos `webAccessCopyButton`, handler de clipboard e CSS relacionado.
- **Indicador passivo:** o endereço Web deixa de ser botão/click target e passa a ser apenas informativo.
- **IP LAN autoritativo:** quando `scope=lan`, o frontend usa `lan_ip` e a porta publicada para montar o endereço e não aceita `127.0.0.1`/`0.0.0.0` como URL principal.
- **Browser:** a abertura automática continua sendo controlada exclusivamente por **Configuração → Abrir também no navegador ao iniciar**.
- **Diagnóstico:** preservados `bind_host`, `display_host`, `lan_ip`, `share_url` e `scope` no runtime.
- **Regressões:** testes específicos impedem o retorno do botão de copiar, clique no endereço, `\\n` literal e fallback LAN para loopback.
- Mantidas integralmente as correções de Windows 7 Legacy, updater e empacotamento da v1.14.27.
- **Gate de release:** publicação condicionada aos testes v1.14.28, incluindo ausência de botão de copiar/`\\n` literal e prioridade do IPv4 LAN no frontend.
- Release completa para Windows x64/ARM64, Windows 7 SP1 x64 Legacy, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.27 - 2026-10-11

- **Win7 Portable:** removidas as dependências `pywebview` e `pythonnet` do runtime Legacy após a regressão da v1.14.26 em Windows 7 real.
- **Shell Win7 estável:** Chrome/Chromium/Brave são usados em modo `--app` quando disponíveis, criando uma janela dedicada sem abas/barra de endereço; o backend e o ícone de bandeja permanecem ativos.
- **Fallback seguro:** se não houver navegador compatível para modo app, a interface abre no navegador padrão sem encerrar o processo, com diagnóstico registrado.
- **Diagnóstico:** inicialização Legacy registra versão, executável, argumentos, URL, navegador selecionado e falhas de shell.
- **Setup × versão anterior:** o instalador encerra qualquer processo `PT2VHF_APRS_Client_Win7_Legacy*.exe`, inclusive Portable versionado ainda aberto.
- **Empacotamento limpo:** `build`, `dist` e `dist-win7` são removidos antes do build Legacy para impedir reutilização de artefatos antigos.
- **Setup usa artefato fresco:** o Inno Setup passa a incluir o Portable versionado recém-copiado para `dist-win7`.
- **Version probe:** o executável Legacy aceita `--write-version` para validação automatizada sem iniciar a interface.
- **Smoke do Portable:** o pipeline executa o Portable recém-gerado e confirma que a versão embutida coincide com `VERSION`.
- **Smoke do Setup:** o instalador é executado silenciosamente em diretório temporário; o executável instalado é então consultado e precisa reportar exatamente a mesma versão.
- **Updater Legacy:** mantida a seleção exclusiva dos assets Windows 7 Setup/Portable, atualização in-place do Portable e rollback.
- **Gate de release:** publicação só ocorre após probe de versão do Portable e do executável realmente instalado pelo Setup Legacy.
- Release completa para Windows x64/ARM64, Windows 7 SP1 x64 Legacy, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.26 - 2026-10-11

- **Windows 7 Legacy desktop:** removido o `--browser` forçado; Setup e Portable passam a iniciar como aplicação desktop com shell WebView empacotada.
- **Runtime Legacy:** adicionados pywebview 4.4.1 e pythonnet 3.0.3 ao ambiente isolado do Windows 7, mantendo Python 3.8.10/PyInstaller 5.13.2.
- **Updater Win7:** Setup e Portable reconhecem seus próprios modos e selecionam exclusivamente assets Legacy.
- **Portable in-place:** a atualização substitui o executável atual no mesmo caminho, mantém backup para rollback e relança automaticamente a nova versão.
- **Web LAN — IP real:** detecção prioriza IPv4 LAN válido e ignora loopback, endereço indefinido e link-local.
- **Web LAN — abrir/copiar:** clicar no endereço abre exatamente o URL publicado no navegador padrão; copiar fica em botão separado.
- **Firewall:** diagnóstico informa estado LAN/porta; no Windows, o usuário pode autorizar explicitamente uma regra de entrada TCP limitada ao perfil Privado e à porta efetiva.
- **Segurança:** firewall/Defender nunca são desabilitados; não há UPnP, port-forwarding ou exposição automática à Internet/WAN.
- **i18n:** novos controles e mensagens de Web LAN/firewall recebem cobertura nos dez idiomas.
- **Regressões:** novos testes cobrem desktop Win7, updater Legacy, separação de assets, Web LAN, firewall e metadados da release.
- **Pipeline:** publicação condicionada à validação v1.14.26, pytest, sintaxe JS/Python, build Win7 Legacy e demais artefatos multiplataforma; validador LAN corrigido antes da publicação final.
- Release completa para Windows x64/ARM64, Windows 7 SP1 x64 Legacy, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.25 - 2026-10-11

- **Windows 7 Legacy:** Windows 7 SP1 x64 passa a ter Setup e Portable próprios, construídos com Python 3.8.10/PyInstaller 5.13.2 e interface no navegador, sem dependência de WebView2.
- **Canal Legacy isolado:** o atualizador identifica a edição Win7 e procura exclusivamente assets Legacy, impedindo substituição automática por um build moderno incompatível.
- **Windows moderno preservado:** Windows 10/11 continuam usando o build principal em Python 3.12/WebView2; nenhuma dependência moderna foi rebaixada para acomodar o Win7.
- **Acesso Web LAN:** nova opção opt-in permite servir a interface para outros dispositivos da rede local; localhost continua sendo o padrão seguro.
- **Endereço no cabeçalho:** a barra superior mostra Web local ou Web LAN com o IPv4 utilizável e a porta realmente reservada, permitindo copiar o URL completo.
- **Cabeçalho compacto:** o seletor rápido de tema sai da barra superior; o tema permanece em Configuração e continua sendo aplicado imediatamente. Enviar Beacon passa a usar um botão compacto com ícone e acessibilidade por tooltip/aria-label.
- **Internacionalização:** removido o fallback silencioso para Inglês quando outro idioma está selecionado; textos sem tradução explícita não são mais mascarados em Inglês, e os novos controles LAN recebem traduções nos dez idiomas suportados.
- **Auditoria i18n:** a validação passa a detectar regressões de fallback indevido, paridade dos catálogos, entradas vazias e textos visíveis candidatos fora do mecanismo de tradução.
- **Sobre:** PY2FDG — Fábio passa a constar entre os colaboradores, com crédito pelas sugestões de mensagens agendadas e usabilidade.
- **Manual e Release:** documentação passa a identificar claramente os artefatos modernos e Win7 Legacy e a política de suporte mínimo.
- Release completa para Windows x64/ARM64, Windows 7 SP1 x64 Legacy, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.24 - 2026-10-11

- **Recordes RF — algoritmo:** o ranking deixa de recalcular `_compatible_events()` para o caminho inteiro a cada expansão e passa a propagar incrementalmente a evidência histórica selecionada hop a hop.
- **Desempenho:** eventos por enlace são pré-amostrados uma única vez, preservando diversidade espacial para digis/trackers móveis; estados equivalentes são podados por posição/hop e cada origem possui orçamento de expansões.
- **Cache e single-flight:** resultados do ranking são cacheados por período/parâmetros e cálculos concorrentes reutilizam a mesma execução.
- **Deadline interno:** o backend possui orçamento próprio de cálculo para impedir workers presos por vários minutos; quando existe resultado anterior válido, ele pode ser reutilizado como fallback.
- **Jobs assíncronos:** novo fluxo `/api/topology/rf-records/jobs` executa o ranking em segundo plano, fornece status/progresso e suporta cancelamento.
- **Progresso real:** Estatísticas mostra 0–100%, etapa atual, itens concluídos, nós, enlaces, candidatos e tempo decorrido.
- **Overlay global:** o relógio central passa a exibir barra e percentual para operações que fornecem progresso determinado.
- **Resiliência:** erro transitório não apaga o último ranking válido do mesmo período; a interface informa o problema e oferece **Tentar novamente**.
- **Compatibilidade:** `GET /api/topology/rf-records` permanece disponível com cache e erro estruturado.
- **Testes:** novas regressões cobrem multi-hop incremental, ausência de reprocessamento integral do caminho, progresso monotônico, cache, job assíncrono e preservação do último ranking válido.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.23 - 2026-10-10

- **10 idiomas:** adicionados Alemão (de-DE), Italiano (it-IT), Japonês (ja-JP), Polonês (pl-PL), Holandês (nl-NL) e Chinês simplificado (zh-CN), mantendo PT, EN, ES e FR.
- **Catálogos dedicados:** os seis novos idiomas recebem catálogos completos alinhados ao catálogo principal, opções no seletor rápido e em Configuração, bandeiras próprias e locale para datas/números.
- **CJK:** Japonês e Chinês recebem fallback tipográfico apropriado para renderização Unicode.
- **Auditoria i18n:** o verificador de traduções passa a validar presença e quantidade de entradas dos seis novos catálogos.
- **Estatísticas:** removida a rolagem vertical interna remanescente; a aba passa a expandir no documento e usar somente a rolagem principal da janela.
- **Rota RF no mapa:** `route.edges` passa a ser fonte autoritativa durante o foco da rota, criando imediatamente segmentos aceitos pelo motor mesmo quando ainda não constam no snapshot de `/api/topology`.
- **Refresh de topologia:** chamadas concorrentes não são mais descartadas quando `topologyLoadBusy` está ativo; uma nova passagem é enfileirada e executada ao final.
- **Caso PY4RC-15:** o hop final inferido PY1MRG-15 → PY4RC-15 passa a aparecer imediatamente quando já estiver incluído na rota calculada.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.22 - 2026-10-10

- **Ranking RF multi-hop:** Recordes RF passam a manter rotas de alcançabilidade com intermediários explícitos e podem preferir uma cadeia multi-hop válida para o mesmo par de extremidades.
- **Histórico preservado:** topology_edges antigos sem topology_events completos ganham fallback por coordenadas históricas próximas ao last_seen; nós móveis não usam posição atual distante para reinterpretar o passado.
- **Período Completo:** enlaces históricos válidos permanecem disponíveis enquanto seus dados existirem no banco.
- **Exportar JSON:** novo botão na aba Mapa gera diagnóstico técnico versionado com estações, objetos, tracklogs, topologia, eventos históricos, digipeaters, iGates e Recordes RF.
- **Privacidade do diagnóstico:** a exportação não inclui configuração sensível, senhas, tokens ou chaves de API.
- **Filtros do Mapa:** ocultar uma estação, objeto, digi ou iGate não remove automaticamente as linhas de enlace; a visibilidade das linhas depende das próprias camadas RF/APRS-IS.
- **Ícone Windows:** a arte APRS fornecida passa a ser a fonte do ícone do executável/barra de tarefas/Alt+Tab, com AppUserModelID dedicado.
- **Salvar como:** a ponte nativa de arquivos de texto aceita KML e JSON conforme a extensão solicitada.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.21 - 2026-10-10

- **Estatísticas sem timeout falso:** o carregamento principal deixa de depender do cálculo pesado de Recordes RF e retorna os indicadores essenciais primeiro.
- **Recordes RF progressivos:** rotas/recordes passam para endpoint independente e são atualizados em segundo plano sem derrubar o restante da aba.
- **Cache de Estatísticas:** resultados por período são compartilhados por 30 segundos entre workers, evitando recomputações repetidas do histórico completo.
- **Single-flight do grafo RF:** somente um worker reconstrói cada grafo por período/banco; requisições concorrentes aguardam e reutilizam o mesmo resultado.
- **Cache RF coalescido:** ingestão APRS contínua não apaga imediatamente um grafo recém-calculado; a atualização permanece limitada ao TTL curto.
- **Autocomplete de rotas:** chamadas antigas de origem são canceladas, resultados base são reutilizados localmente e consultas filtradas só ocorrem quando necessárias.
- **Diagnóstico de performance:** tempos de cálculo dos principais componentes de Estatísticas e do grafo RF passam a ser registrados quando excedem o limiar.
- **Último resultado válido:** falha ou timeout de atualização não zera os cartões; a interface mantém a última leitura válida ou mostra “Indisponível”.
- **Indicador global de processamento:** spinner/relógio central passa a aparecer somente após 320 ms, suporta operações concorrentes e modo não bloqueante.
- **Rotas e Estatísticas:** análise de rota RF, histórico completo e Recordes RF usam o indicador de processamento durante operações demoradas.
- **Estatísticas em fluxo único:** removida a rolagem interna do ranking Software / dispositivos APRS e dos demais subblocos; somente a área principal da aba rola verticalmente.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.20 - 2026-10-10

- **Rotas RF como alcançabilidade:** a análise deixa de exigir que um pacote tenha percorrido toda a cadeia de uma só vez; enlaces RF válidos observados em momentos distintos podem formar uma rota histórica.
- **Coordenadas por evento:** cada hop usa a posição histórica das estações no instante daquele contato, preservando corretamente digis/trackers móveis.
- **Continuidade espacial:** um nó móvel só conecta dois hops históricos quando suas coordenadas nos dois eventos são compatíveis; deslocamentos entre regiões não viram pontes artificiais.
- **Intermediários preservados:** cadeias A→B, B→C, C→D são exibidas como A→B→C→D, sem colapsar automaticamente em um falso A→D.
- **Inferidos longos:** hops RF inferidos de 250 km ou mais, sem cadeia intermediária sustentada, deixam de ser tratados como enlace físico direto.
- **Semântica explícita:** rotas distinguem observada no mesmo pacote, reconstruída por eventos contemporâneos e alcançabilidade histórica.
- **Mapa de rotas:** usa as coordenadas históricas selecionadas para cada hop, não a posição atual dos nós.
- **Tracklog:** intervalo superior a 30 minutos sem nova posição encerra o segmento; o próximo ponto inicia novo segmento.
- **KML:** exportação aplica a mesma segmentação temporal do mapa, evitando retas entre pontos separados por longos períodos sem rastreamento.
- **Testes:** regressões cobrem alcançabilidade histórica, tracker móvel, hop inferido longo e segmentação temporal do tracklog/KML.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.19 - 2026-10-10

- **Topologia RF espaço-temporal:** rotas deixam de tratar um indicativo móvel como um vértice fixo ao longo de todo o histórico.
- **Digis/trackers móveis:** um nó como PT2AP-10 pode atuar como elo enquanto está próximo das estações envolvidas, mas enlaces observados horas depois e centenas de quilômetros adiante não são mais costurados na mesma rota.
- **Posição no instante do enlace:** novos eventos de topologia passam a gravar latitude/longitude das duas extremidades no momento da observação; distâncias históricas deixam de usar a posição mais recente da estação.
- **Migração automática do histórico:** eventos legados recebem, quando disponível, a posição do tracklog mais próxima de seu timestamp, sem apagar o banco existente.
- **Janela temporal de rota:** uma rota RF observada exige que todos os hops coexistam numa janela máxima de 30 minutos.
- **Continuidade espacial:** o nó compartilhado entre dois hops precisa permanecer espacialmente compatível no intervalo, evitando pontes artificiais criadas por estações móveis em viagem.
- **Refinamento inferido mais conservador:** a janela de reconstrução de hops inferidos cai de 36 horas para 30 minutos.
- **Ranking de enlaces/rotas:** distâncias passam a ser calculadas pela geometria histórica selecionada para a rota, eliminando falsos recordes causados pelo deslocamento posterior de trackers.
- **Caso de regressão real:** adicionados testes para o cenário PP2ITG-15 → PT2AP-10 em Itumbiara versus PT2AP-10 → PY5CTV-13 muitas horas depois no Sul.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.18 - 2026-10-09

- **Mapa — Acompanhar Estação:** o popup de uma estação ganha ação explícita para iniciar acompanhamento em tempo real.
- **Centralização contínua:** ao acompanhar, o popup fecha, o mapa preserva o zoom atual e mantém a estação centralizada a cada nova posição; arrastar o mapa encerra o modo.
- **Painel flutuante:** durante o acompanhamento são exibidos indicativo, velocidade, curso e tempo desde o último pacote, atualizado mesmo quando a estação deixa de transmitir.
- **Tracklog unificado:** o novo fluxo reutiliza o mecanismo de seguimento já existente, evitando estados paralelos.
- **Mensagens — retry coerente:** retransmissões reaproveitam o mesmo message ID e atualizam a mesma mensagem lógica em vez de criar uma nova cadeia de IDs.
- **ACK/REJ terminal:** confirmações e rejeições não podem ser sobrescritas por atualizações tardias de TX ou retry.
- **Deduplicação de RX:** retransmissões da mesma mensagem, com remetente/destino/ID/texto iguais, não geram entradas lógicas duplicadas no histórico.
- **ACK por RF/TNC:** mensagens pessoais recebidas por RF passam a ser confirmadas pelo mesmo meio quando o TX RF estiver habilitado e confirmado.
- **ACK RF resiliente:** frames RF repetidos dentro da janela de supressão continuam sem duplicar dados, mas reenviam o ACK quando aplicável, cobrindo ACK perdido no ar.
- **Regressões:** testes cobrem terminalidade de ACK, reutilização de ID/linha no retry, deduplicação de RX, ACK RF e interface de acompanhamento.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.17 - 2026-10-09

- **Configuração em fluxo único:** removidas barras de rolagem verticais internas dos cards/subblocos; toda a aba passa a usar somente o scroll principal da Configuração.
- **Blocos dinâmicos incluídos:** a regra também cobre seções adicionadas por módulos como integrações, saúde do banco, resposta automática, backup, grupos e alertas.

- **Backup completo corrigido:** o botão deixa de ser um link simples e passa a executar uma operação explícita, com erro/sucesso visível.
- **Salvamento nativo no desktop:** Windows, Linux e macOS usam diálogo nativo para escolher onde salvar o ZIP; o modo navegador mantém fallback por Blob/download.
- **Backend de backup robusto:** falhas retornam erro JSON explícito, ZIP vazio é rejeitado e a resposta recebe headers `no-store`.
- **Indicador global de processamento:** novo overlay central com relógio animado e mensagem contextual para operações demoradas.
- **API reutilizável:** `showProcessing`, `updateProcessing`, `hideProcessing` e `withProcessing` ficam disponíveis para fluxos assíncronos longos.
- **Aplicado em operações críticas:** backup completo, restauração e exportação KML passam a mostrar processamento em andamento.
- **Refinamento RF inferido:** hops longos apenas inferidos pelo path são investigados contra o grafo RF conhecido, excluindo a própria aresta original.
- **Intermediários reconstruídos:** quando existe cadeia melhor sustentada e temporalmente próxima, o painel/mapa expandem o trecho e identificam os nós como reconstruídos/prováveis.
- **Sem fabricação de rota:** quando não há evidência suficiente, o trecho permanece inferido e o painel mostra “Intermediários não identificados”.
- **RF direto preservado:** enlaces RF diretamente observados nunca são quebrados apenas pela distância.
- **Critério conservador:** reconstrução prioriza RF direto, exige recorrência para caminhos apenas inferidos, restringe janela temporal e evita grandes desvios artificiais.
- **Regressões:** testes cobrem reconstrução, ausência de cadeia, RF direto longo, preferência por evidência direta, proximidade temporal, backup e overlay.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.16 - 2026-10-09

- **Tracklog com acompanhamento:** clicar em um tracklog ativa o modo de seguimento; novas posições mantêm a estação centralizada sem alterar o zoom escolhido.
- **Controle manual preservado:** arrastar o mapa encerra o acompanhamento; alterar o zoom mantém o modo ativo e recentraliza o tracklog no novo nível.
- **Troca de seleção:** clicar em outro tracklog transfere o acompanhamento; selecionar outra estação encerra o seguimento do tracklog anterior.
- **Ranking com enquadramento máximo:** ao abrir uma rota do Ranking, o mapa usa o maior zoom possível que ainda comporta todo o trajeto e todos os nós.
- **Painel considerado no enquadramento:** o cálculo reserva a área ocupada pelo painel de análise para evitar esconder a rota atrás do popup lateral.
- **Todos os nós da rota visíveis:** cada indicativo listado no painel recebe uma identificação visual no mapa, inclusive quando o marcador normal está filtrado, ausente ou sobreposto.
- **Marcadores temporários de rota:** nós sem marcador normal recebem marcador temporário próprio; nós que já possuem símbolo normal recebem apenas um rótulo de rota, evitando duplicar o símbolo APRS.
- **Limpeza consistente:** os marcadores temporários são removidos ao encerrar ou trocar a análise de rota.
- **Regressões:** novos testes cobrem acompanhamento de tracklog, zoom preservado, enquadramento sem `maxZoom` artificial e visibilidade integral dos nós.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.15 - 2026-10-09

- **Rotas RF em malhas densas:** removido o corte prematuro da antiga DFS (`route_limit * 4`), que podia ignorar enlaces RF válidos depois dos primeiros caminhos encontrados.
- **Busca best-first:** caminhos simples passam a ser ordenados pela qualidade da evidência e número de hops; evidência RF direta tem prioridade sobre RF inferido do path.
- **Sem veto por distância:** comprimento geográfico continua informativo, mas não exclui um enlace RF observado.
- **Corredor RF completo:** a API retorna todos os enlaces RF elegíveis que podem participar de uma rota entre origem e destino dentro do horizonte de hops.
- **Mapa coerente com a topologia:** durante a pesquisa, todos os enlaces elegíveis permanecem visíveis; selecionar uma rota apenas destaca seus trechos e reduz a ênfase dos demais.
- **Evidência por rota:** painel informa quantidade de trechos diretos, inferidos e legados e identifica a evidência de cada hop.
- **Horizonte ampliado:** pesquisa manual usa 12 hops por padrão, contra 8 anteriormente.
- **Proteção transparente:** em malhas excepcionalmente combinatórias, um limite alto de expansões protege o cliente; se atingido, a interface informa a truncagem e preserva os enlaces elegíveis.
- **Regressões:** testes cobrem corredor completo, prioridade de evidência direta, enlace longo sem veto de distância e integração frontend/backend.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.14 - 2026-10-08

- **Terminologia RF consolidada:** painel de rotas, autocomplete e mensagens deixam de usar “RF confirmado” e passam a refletir corretamente o modelo de **RF observado** restaurado na v1.14.13.
- **Painel de rota:** removida a exibição de confiança/heurística obsoleta da v1.14.12; cada trecho passa a mostrar a origem real da classificação quando disponível.
- **Pesquisa manual:** preservado o mesmo foco exclusivo dos Recordes RF, mantendo somente origem, destino, intermediários e enlaces das rotas encontradas.
- **Rotas alternativas:** continuam disponíveis no mesmo painel, com destaque individual e enquadramento automático.
- **RF × Internet:** APRS-IS/Internet continua sem completar rota RF e permanece como evidência independente.
- **Estatísticas:** mantido o fluxo vertical contínuo, sem barra vertical interna nos rankings.
- **Regressão:** novos testes verificam a ausência dos rótulos obsoletos e a preservação do modelo RF observado.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.13 - 2026-10-08

- **Mapa — pesquisa de duas estações:** ao pesquisar origem e destino, a visualização passa a usar o mesmo foco exclusivo dos Recordes RF: ficam visíveis apenas origem, destino, intermediários e enlaces das rotas encontradas.
- **Rotas alternativas:** quando houver mais de uma rota RF observada, o mapa mantém somente o conjunto de nós/enlaces dessas alternativas e o painel permite destacar cada caminho.
- **RF observado restaurado:** removidos como filtro de exclusão os thresholds de distância/quantidade de observações introduzidos na v1.14.12; enlaces RF observados voltam a compor o grafo mesmo quando longos ou com poucos hops.
- **RF × Internet preservado:** APRS-IS/Internet continua sem completar rota RF; evidências RF e Internet do mesmo par permanecem independentes.
- **Estatísticas:** reforçado o fluxo vertical contínuo do ranking de software e demais blocos, sem barra de rolagem vertical interna.
- **Regressões:** testes cobrem enlace RF longo observado, exclusão de iGate/APRS-IS do grafo RF e foco exclusivo da pesquisa manual.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.12 - 2026-10-09

- **RF confirmado:** Pesquisa RF e Recordes RF deixam de aceitar automaticamente qualquer aresta marcada como `rf`; cada trecho passa por uma heurística de evidência e plausibilidade.
- **Níveis de confiança:** trechos podem ser classificados como RF confirmado, RF provável, RF inconsistente ou Internet/APRS-IS.
- **Plausibilidade física:** distâncias maiores exigem evidência direta/repetida mais forte; um trecho excepcionalmente longo com poucas observações deixa de compor uma rota 100% RF.
- **Propagação excepcional preservada:** enlaces muito longos continuam possíveis quando houver quantidade forte de evidência direta suficiente.
- **Histórico reavaliado dinamicamente:** rotas e Recordes RF são recalculados com a nova heurística sem apagar os dados brutos armazenados.
- **Painel de análise RF arrastável:** o painel lateral pode ser movido pelo cabeçalho dentro da área do mapa, com limites para não sair da tela.
- **Estatísticas sem scroll interno:** cards, ranking de software/aplicações, estações e Recordes RF usam apenas a rolagem vertical principal da aba.
- **UI:** resultados de rota passam a usar explicitamente o rótulo RF confirmado e exibem a justificativa/confiança dos trechos.
- **Regressão:** novos testes cobrem trechos curtos confirmados, longos inconsistentes, propagação excepcional com evidência forte, filtro do grafo, painel arrastável e ausência de scroll vertical interno.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.11 - 2026-10-08

- **Recordes RF:** o ranking passa a usar como critério principal a distância geográfica direta entre as duas estações extremas, da maior para a menor, desde que exista rota RF completa entre elas.
- **Distância da rota:** a soma dos hops continua exibida como informação complementar, sem influenciar a posição no ranking.
- **Deduplicação por par:** cada par origem/destino aparece uma única vez no ranking, mesmo quando há caminhos RF alternativos.
- **Mapa:** o botão “Rotas RF” passa a se chamar **“Pesquisar”**.
- **Cabeçalho:** “Versão atualizada” passa a **“Atualizada”**.
- **TNC:** indicador superior simplificado para LED vermelho/verde + texto **TNC**; detalhes permanecem no tooltip.
- **APRS-IS:** indicador superior simplificado para LED vermelho/verde + texto **APRS-IS**; detalhes permanecem no tooltip.
- **Layout:** indicadores TNC/APRS-IS ficaram mais compactos para liberar espaço no cabeçalho.
- **Regressão:** testes cobrem ordenação por distância direta, deduplicação de pares e os novos rótulos/status do cabeçalho.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.10 - 2026-10-08

- **Mapa — barra responsiva:** controles acima do mapa deixam de ficar recortados; a barra quebra de linha quando necessário e o mapa recalcula automaticamente a altura disponível.
- **Controles compactos:** campos de origem/destino, selects e botões usam larguras menores e mais próximas do conteúdo.
- **Autocomplete RF:** origem e destino passam a sugerir indicativos progressivamente; a origem usa estações conhecidas no grafo RF e o destino continua restrito a rotas RF completas.
- **Estatísticas sem rolagem interna:** rankings e tabelas deixam de usar altura vertical fixa; a rolagem principal fica na página da aba.
- **Recordes RF:** novo ranking das rotas RF completas mais longas, com hops, distância total, evidência e observações.
- **Foco exclusivo de recorde:** clicar num recorde abre somente aquela rota e suas estações no mapa, ocultando topologia, objetos e tracklogs alheios ao trajeto até o foco ser limpo.
- **RF estrito:** recordes e autocomplete usam o mesmo grafo RF da análise de rotas; APRS-IS/Internet não completa caminhos.
- **Regressão:** novos testes cobrem autocomplete, períodos, deduplicação de sentido inverso, recordes multi-hop, layout responsivo e foco exclusivo.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.9 - 2026-10-08

- **Mapa — pesquisa por indicativo:** novo campo localiza rapidamente uma estação no mapa.
- **Rotas RF completas:** após informar a origem, o segundo indicativo oferece somente destinos alcançáveis por uma cadeia completa de enlaces RF observados no período selecionado.
- **Múltiplas rotas:** o mapa entra em modo de foco e oculta enlaces alheios ao par pesquisado; um painel lateral lista todas as alternativas RF completas encontradas.
- **Detalhamento de rota:** cada alternativa mostra sequência de hops, distância por trecho, distância total, distância direta, evidência temporal e quantidade de observações.
- **Seleção visual:** clicar em uma rota destaca seus enlaces e reduz a ênfase das demais; fechar a análise restaura a topologia normal.
- **RF estrito:** APRS-IS/Internet nunca é usado para completar artificialmente uma rota RF.
- **Enlaces — hover:** o painel de detalhes passa a mostrar o comprimento do enlace em metros ou quilômetros e o popup do enlace exibe o mesmo valor.
- **Regressão:** novos testes cobrem candidatos RF, múltiplos caminhos, exclusão de Internet, direção de consulta e marcadores da interface.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.8 - 2026-10-08

- **Configuração — retenção granular:** Saúde e retenção do banco passa a oferecer presets por categoria: Não apagar, 1 dia, 1 semana e 1 mês.
- **SQLite leve:** Mensagens, Tracklogs, Log APRS, Enlaces/Topologia, frames/decisões TNC, notificações e pacotes podem ter políticas independentes.
- **Compatibilidade:** valores de retenção já existentes são preservados; instalações antigas não têm sua política sobrescrita na atualização.
- **Enlaces/Topologia:** arestas agregadas antigas passam a seguir a mesma janela dos eventos de topologia, mantendo mapa e banco coerentes.
- **Limpeza manual:** Aplicar limpeza agora informa registros removidos e espaço estimado recuperável; Otimizar banco continua disponível para efetivar VACUUM.
- **Mensagens — resposta automática:** novo recurso opcional com texto customizável e cooldown por remetente.
- **Anti-loop:** autoresposta só atua em mensagem direta para a própria estação; ACK/REJ, queries e boletins não disparam resposta, e o cooldown impede ciclos entre duas estações automáticas.
- **Roteamento seguro:** resposta recebida via APRS-IS responde por APRS-IS; mensagem RF responde por RF direto, respeitando os mesmos bloqueios e confirmações de TX.
- **Histórico:** mensagens disparadas automaticamente ficam marcadas no banco com metadado `automated`.
- **Regressão:** novos testes cobrem migração/configuração, cooldown, filtros de autoresposta, histórico automático e retenção de topologia.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.7 - 2026-10-08

- **Backend/SQLite (#49):** reduzida a contenção observada na v1.14.6, sem alterar a retenção padrão para 5 dias.
- **TNC/RF:** criação e migração do schema deixam de rodar em cada polling de status/saúde; passam a ocorrer uma vez por caminho de banco.
- **Mapa:** RX APRS contínuo deixa de invalidar imediatamente o snapshot completo; rebuilds são coalescidos por 30 s.
- **Mapa — leitura:** validação de posições reutiliza as estações já carregadas no mesmo build.
- **SQLite:** adicionados cache conservador, temp_store em memória, wal_autocheckpoint explícito e índices para consultas quentes de packets/topologia.
- **Compatibilidade:** preservados WAL, busy timeout, classificação RF/APRS-IS, dados existentes e política de retenção do usuário.
- **Regressão:** novos testes cobrem schema TNC one-shot, coalescimento do mapa e os novos índices/pragmas.
- Release completa prevista para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.6 - 2026-10-07

- **SAT/ISS removido do cliente principal:** retirados aba SAT, mapas/órbitas, catálogo/TLE, passagens, alertas, estações/mensagens satelitais, beacon satelital e rotas dedicadas.
- **Build mais leve:** removida a dependência `sgp4`, os assets JS/CSS e os serviços de backend exclusivos do módulo orbital.
- **Escopo:** o PT2VHF APRS Client volta a concentrar-se no APRS terrestre; uma solução dedicada a APRS via satélite poderá ser tratada separadamente.
- **Topologia iGate/Internet:** evidência APRS-IS confirmada deixa de ser descartada quando o mesmo par de estações também possui evidência RF.
- **RF preservado:** pacotes recebidos efetivamente por TNC/RF e caminhos qAR/qAO continuam classificados como RF; ser iGate não transforma um enlace RF em Internet.
- **Evidência mista:** RF e APRS-IS passam a ser mantidos como enlaces independentes, com contadores próprios e indicação de evidência mista.
- **Mapa:** RF é desenhado primeiro; enlace Internet confirmado fica tracejado e em primeiro plano, preservando a leitura quando as geometrias coincidem.
- **Migração:** preferências/cache SAT de versões anteriores deixam de ser carregados ou executados; os dados do usuário não são apagados de forma destrutiva.
- **Regressão:** testes garantem remoção estrutural do SAT e retorno/renderização de enlaces iGate/APRS-IS, inclusive quando existe RF para o mesmo par.
- Release completa prevista para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.5 - 2026-10-07

- **Configuração — detecção de alterações:** o estado dirty passa a ser recalculado pelo snapshot real do formulário; eventos ocorridos durante carregamento assíncrono deixam de ser ignorados.
- **Configuração — resposta lenta:** `loadConfig()` rastreia geração de edição e campos tocados, preservando alterações locais quando um GET antigo termina depois da edição.
- **Botão inferior Salvar configuração:** compara formulário com baseline persistido no momento do clique e envia apenas os campos alterados.
- **Salvar e sair:** usa o mesmo patch do botão inferior e mantém no modal a mensagem real do backend quando houver rejeição.
- **Descartar alterações e sair:** restaura o último estado carregado em memória e navega sem executar `GET /api/config`; funciona mesmo com backend temporariamente indisponível.
- **Continuar na Configuração:** permanece uma operação local e não altera o formulário.
- **Configuração migrada:** valores legados fora da faixa atual não impedem salvar outro campo não relacionado; a validação continua obrigatória quando o próprio campo é modificado.
- **Pós-save:** removida a recarga GET obrigatória logo após POST; o retorno confirmado do backend passa a ser o novo baseline.
- **SAT #52:** corrigido o uso de `$().forEach` nos serviços monitorados; agora usa `querySelectorAll()`.
- **SAT — isolamento de erro:** falhas de renderização do painel de detalhes são tratadas por `safeRenderDetail()` e deixam de cair no tratamento de erro orbital.
- **Testes:** novas regressões pytest e Playwright para instalação migrada, GET lento, botão inferior, erro real, descarte offline e serviços SAT.
- Release completa Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.4 - 2026-10-07

- **Configuração:** corrigido o modal de alterações pendentes para concluir corretamente Salvar e sair, Descartar alterações e sair e Continuar na Configuração.
- Fluxo de saída com controle de concorrência, indicação acessível de progresso/erro, modal temporariamente recolhido durante confirmações nativas e preservação das alterações se o salvamento falhar.
- O botão normal Salvar configuração e a persistência SQLite continuam usando o mesmo backend.
- **Estações:** botão direito na linha do indicativo abre Mensagem rápida com destinatário preenchido, reusando validações, fila, roteamento e ACK/REJ já existentes.
- **Mapa:** enlaces exclusivamente Internet/APRS-IS deixam de ser ocultados quando filtros de visibilidade dos marcadores de estações/iGates estão desativados. A camada Enlaces iGate/APRS-IS permanece independente e respeita seu próprio liga/desliga.
- **Classificação:** conexões qAr/APRS-IS confirmadas permanecem Internet tracejada; qAR/qAO RF e evidência mista seguem a política existente sem criar rotas fictícias.
- **Ícones:** pictograma de antena de alto contraste específico para ícones do sistema (Windows/Linux/macOS), legível em 16/24 px; logomarca oficial preservada no cabeçalho e manual.
- **Alertas:** corrigido `$(...).forEach is not a function` no módulo de alertas configuráveis; coleção passa a usar `querySelectorAll()` tanto no autosave quanto em Salvar alertas.
- **Mapa — janela curta:** adicionados períodos de **15 min** e **30 min**. Topologia, RF ouvido, KML e cobertura RF aceitam frações de hora sem truncar para período completo.
- **SAT responsivo:** a grade muda para uma coluna até 1320 px, preserva no mínimo ~340 px para a lateral quando em duas colunas, permite quebra de nomes e invalida o tamanho do Leaflet via ResizeObserver.
- **Banco/backend:** a abertura de Configuração usa saúde SQLite leve, sem `PRAGMA quick_check` e `COUNT(*)` integrais nas tabelas grandes; checagem profunda permanece nas rotinas explícitas/testes.
- **Validação:** testes automatizados de regressão mais testes reais em Chromium/Playwright durante a criação das telas do manual para salvar, descartar, cancelar, alertas, botão direito, enlace Internet e responsividade SAT.
- TM-D700 permanece encerrado administrativamente: não há alegação de teste físico RF.
- Release completa Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.3 - 2026-10-06

- **Barra superior:** novo botão **Enviar Beacon** para disparo manual imediato sem navegar até Configuração.
- O botão reutiliza exatamente o mesmo endpoint e a mesma configuração do beacon manual já existente, com bloqueio temporário dos dois botões durante o envio para impedir duplo clique/disparo duplicado.
- **Estações — falso positivo de digipeater corrigido:** o classificador de interação deixa de usar o frame APRS bruto/path como prova de infraestrutura.
- Paths como **WIDE1-1,WIDE2-1** deixam de transformar a estação de origem em digipeater; eles representam apenas o caminho solicitado para o pacote.
- O backend passa a fornecer evidência explícita de infraestrutura quando um indicativo foi realmente observado como hop intermediário utilizado ou como iGate em q-construct.
- Objetos/itens APRS continuam não interativos, e infraestrutura comprovada sem evidência de capacidade bidirecional continua protegida contra envio dirigido.
- Adicionada regressão específica para HT/estação comum usando WIDE e para digipeater realmente observado no path.
- Atualizados README, backlog, histórico interno e Manual PDF.
- A validação física externa do Kenwood TM-D700 permanece pendente.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.2 - 2026-10-06

- **Cobertura RF:** nova camada de mapa em formato heatmap Canvas, sem dependência externa e sem gerar tráfego adicional.
- A camada usa somente evidência RF persistida; pontos com RSSI/SNR recebem ponderação de qualidade e os demais usam densidade de recepções como fallback.
- **Zoom adaptativo:** o raio de influência varia com o nível de zoom, mesclando mais pontos em visão ampla e revelando detalhes ao aproximar.
- **Período:** o heatmap acompanha o período selecionado na barra do Mapa.
- **Mapa → Ver:** Cobertura RF é adicionada como item independente e acompanha Selecionar tudo / Remover tudo.
- **AIS:** popup de embarcação ampliado com nome, MMSI, IMO, indicativo, tipo, status de navegação, SOG, COG, proa, destino, ETA, calado, dimensões e fonte quando disponíveis.
- **Códigos AIS:** tipos/status numéricos comuns são convertidos para descrições legíveis.
- **Foto AIS:** preservado o provedor externo configurável por MMSI/IMO e o cache local; quando houver associação confiável, a foto real é apresentada.
- **Fallback AIS:** sem foto real, o Client pode mostrar uma representação vetorial claramente marcada como imagem ilustrativa do tipo.
- O enriquecimento AIS é assíncrono e falhas do provedor não impedem a abertura do popup textual.
- O backlog antigo de zoom intermediário é encerrado, pois o step configurável já existe desde a v1.8.17.
- A validação física externa do Kenwood TM-D700 permanece pendente por exigir rádio real e monitor RF.
- Adicionada suíte de regressão v1.14.2 e validador de produção.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.14.1 - 2026-10-06

- **SAT — correção crítica do mapa orbital:** satélites selecionados são desenhados imediatamente, sem esperar o polling periódico de status.
- **ISS:** NORAD 25544 é o único satélite selecionado por padrão em instalações novas; seleção vazia explícita continua vazia após reinício.
- **Renderização progressiva:** posição atual tem prioridade sobre footprint e trajetórias; fila de tracks limitada evita rajadas de requisições em “Marcar tudo”.
- **Desseleção segura:** requisições atrasadas não recriam marcadores de satélites já desmarcados.
- **Feedback orbital:** estados de carregamento, TLE indisponível e erro de cálculo deixam de produzir mapa silenciosamente vazio.
- **Layout SAT:** mapa, estações recebidas e mensagens passam a ocupar o espaço principal; detalhes, alertas, TLE, filtros, beacon e agenda ficam recolhidos por padrão.
- **Próxima passagem:** contador alinhado à esquerda, com satélite/indicativo identificado; durante passagem ativa mostra “EM PASSAGEM” e contagem até LOS.
- **Menu superior:** “Satélites / ISS” foi abreviado para **SAT**; o título interno continua completo.
- **Notificações:** removido o sino da barra superior; o Centro de notificações permanece acessível em Configuração.
- **Alertas de nova estação:** preferência desmarcada passa a ser aplicada imediatamente e persistida como fonte efetiva para o polling de alertas.
- **CI/publicação:** o workflow completo deixa de competir com o workflow de produção na publicação da mesma Release.
- Adicionados testes de regressão para seleção padrão, renderização imediata, layout recolhível, contador, sino e preferências de alertas.

## 1.14.0 - 2026-10-06

- **Satélites / ISS — operação completa:** a aba passa a concentrar mapa, próxima passagem, estações recebidas, mensagens APRS, beacon satelital e agenda.
- **Estações APRS na aba Satélites:** lista recente com RF/APRS-IS, quantidade de pacotes, contexto satelital, última recepção, distância e mensagens.
- **Filtros operacionais:** selecionados + favoritos, apenas selecionados, apenas favoritos ou passagem ativa; período, somente RF e somente estações com mensagens.
- **Mensagens integradas:** destinatário preenchido ao clicar na estação, histórico local, ACK/REJ/status, Enter para enviar e Shift+Enter para quebra de linha.
- **Motor único:** o envio na aba Satélites reutiliza `/api/messages/send`, o mesmo pipeline da aba Mensagens, incluindo rota, path, retries, ACK/REJ e persistência.
- **Seleção compacta:** painel de satélites recolhível por padrão, resumo de selecionados/favoritos e ação Editar seleção.
- **Pesquisa rápida:** busca por nome, indicativo/designação ou NORAD, integrada aos filtros; Marcar tudo/Desmarcar tudo respeitam a busca visível.
- **Contador reposicionado:** sai da aba superior e vai para a barra operacional da aba Satélites, com fonte maior e formato HH:MM:SS.
- **Contador e despertador:** consideram somente satélites selecionados ou favoritos, com APRS confirmado, estado Monitorar e serviço APRS ativo.
- **Beacon Satélite / curto:** perfil RF independente do beacon terrestre, com path próprio, comentário curto, intervalo, elevação mínima, cobertura/LOS e consentimento explícito.
- **Beacon seguro:** usa o mesmo pipeline TNC/RF, respeita TX confirmado/pausado e bloqueia protocolo serial terminal/PKT.
- **Preview de beacon:** mostra o frame e tamanho estimado antes do envio e alerta para frame excessivamente longo.
- **Histórico de beacon:** registra satélite, frequência, path, payload, tamanho e resultado.
- **Saúde operacional do TNC:** componente passa a ser inserido estritamente dentro de TNC / RF e não pode aparecer em Configuração ou Sobre.
- Adicionados testes de regressão para todos os itens acima.

## 1.13.0 - 2026-10-06

- **Satélites APRS:** catálogo padrão passa a exibir somente satélites com APRS confirmado; AX.25, packet, GFSK ou telemetria genérica não são promovidos automaticamente para APRS.
- **Colibri-S:** adicionada regressão garantindo que o NORAD 61746 não seja classificado como APRS apenas por operar packet/AX.25.
- **Filtros de catálogo:** opções Somente APRS, APRS + Packet/AX.25 e todos os digitais.
- **Seleção rápida:** novos botões Marcar tudo e Desmarcar tudo, respeitando o filtro visível e sem alterar favoritos.
- **Contador da próxima passagem:** indicador grande amarelo em HH:MM:SS ao lado de Satélites / ISS, atualizado a cada segundo sem recalcular toda a agenda.
- **Passagem ativa:** contador troca automaticamente de tempo até AOS para tempo restante até LOS.
- **Despertador de aproximação:** antecedência configurável, som próprio, popup, deduplicação, silenciar passagem, favoritar e abrir/seguir satélite.
- **TLE multifonte:** CelesTrak Amateur, CelesTrak Stations e AMSAT nasabare.txt com ativação, prioridade, teste individual, fallback e deduplicação por NORAD ID.
- **Atualização automática:** scheduler interno diário, padrão 00:00 local, sem wget/grep/at ou tarefas do sistema operacional.
- **Estado operacional:** cada satélite pode ser Monitorado, Ignorado ou marcado Fora do ar sem perder a preferência na próxima atualização de TLE.
- **Serviços por satélite:** APRS, SSTV, Telemetria, Voz/FM e Packet/AX.25 podem ser habilitados/desabilitados individualmente.
- **Fontes orbitais:** painel mostra estado das fontes e o detalhe do satélite separa fonte do catálogo e fonte TLE.
- **TM-D700/TM-D710:** diagnóstico passa a distinguir KISS de terminal/command mode e separa baud rate serial de packet RF 1200/9600.
- **Perfis TNC:** Genérico KISS, Kenwood TM-D700, Kenwood TM-D710, Kantronics/TNC terminal e genérico.
- **Diagnóstico serial:** amostra limitada ASCII/HEX, estados terminal-aware e orientação que não sugere menu KISS inexistente no TM-D700.
- **Segurança:** TX automático é bloqueado em perfil serial terminal/PKT; uso de TX permanece restrito a transportes/protocolos compatíveis.
- **Autoteste TNC:** passa a informar separadamente transporte, framing/protocolo, AX.25, RX, modelo de TX e deixa explícito que TX físico RF não foi validado.
- **AGWPE:** preservado como caminho operacional para RX AX.25, incluindo o cenário real reportado pelo PU2MUS; TX físico continua dependente de validação no ar.
- Adicionados testes de regressão para classificação APRS, fontes/fallback, scheduler, persistência operacional, alarmes/controles e diagnóstico TM-D700.

## 1.12.0 - 2026-10-05

- Nova aba **Satélites / ISS** com mapa orbital dedicado para APRS/packet espacial.
- Sincronização de catálogo com SatNOGS e elementos TLE com CelesTrak, usando cache local e informação de época/fonte.
- Propagação SGP4 para posição orbital, altitude, velocidade, footprint, azimute, elevação, alcance e estimativa de Doppler.
- Agenda de passagens com AOS/TCA/LOS, elevação máxima, azimutes e duração em janelas de 24 h, 48 h ou 7 dias.
- Alertas configuráveis de passagem integrados ao Centro de notificações.
- **Mapa → Ver** ganha Satélites / ISS como camada opcional e independente do mapa orbital dedicado.
- Corrigida definitivamente a classificação RF × APRS-IS: o meio real de recepção é propagado do pipeline de pacotes para a topologia.
- Removida a migração legada da v1.7.7 que reconvertia enlaces RF com metadado de iGate para Internet a cada inicialização.
- Migração v1.12 reconstrói evidência RF histórica a partir de pacotes persistidos com `medium='RF'`.
- Popup/hover de topologia passa a informar a origem da classificação.
- Mensagens, Estações e Logs passam a usar controles de janela no padrão Windows: minimizar, maximizar/restaurar e fechar/encaixar.
- Corrigida a restauração/redimensionamento após minimizar e adicionada recuperação segura de geometria fora do viewport.
- Aba Logs torna-se destacável.
- Removido o campo de busca da extremidade esquerda da barra contextual do mapa.
- Adicionadas regressões para SGP4, passagens, topologia RF, janelas destacáveis e integração de Satélites.

## 1.11.1 - 2026-10-05

- Corrigida a topologia RF → iGate: evidência RF tem precedência visual sobre evidência APRS-IS para o mesmo par origem/destino.
- Linha tracejada passa a ser usada somente quando o enlace é exclusivamente Internet/APRS-IS.
- Enlaces com evidência mista permanecem contínuos/RF e expõem contagens separadas de RF e Internet nos metadados.
- Popup e hover deixam de rotular como “Entrada no iGate” um trecho que possui evidência RF.
- Mantida a semântica de qAR/qAO como entrada RF e qAr como Internet/APRS-IS.
- Adicionados testes de regressão para RF → iGate, evidência mista e Internet-only.

## 1.11.0 - 2026-10-05

- Corrigidos contadores RX/TX do TNC com reconciliação por frames persistidos da sessão.
- Adicionado health check operacional do TNC com classificação automática do estágio de funcionamento.
- Adicionado autoteste interno KISS/AX.25, incluindo RX, TX, ACK e validação do modelo de contadores.
- Adicionada timeline de saúde do TNC.
- Adicionado centro persistente de notificações.
- Incorporadas as correções completas dos alertas configuráveis da v1.10.1.
- Adicionado painel de saúde e retenção do SQLite, com limpeza por política e otimização manual.
- Perfil da estação ampliado com indicadores operacionais, caminhos e “Ouvido por”.
- Adicionados testes de regressão para contadores persistidos, notificações, retenção, perfil operacional e simulador.

## 1.10.1 - 2026-10-05

- Corrigido o sistema de alertas configuráveis para respeitar estritamente opções desmarcadas.
- "Estação apareceu" passa a ser baseado em transição real de presença, não em qualquer atualização de last_heard.
- "Estação desapareceu" passa a ser rearmável após a estação reaparecer.
- "Nova mensagem" ganha deduplicação por ID.
- Quedas de TNC/APRS-IS não alertam em desconexão voluntária.
- Alerta de integridade SQLite passa a ser único por episódio.
- Preferências de alertas são persistidas automaticamente ao alterar os controles.
- Adicionados testes de regressão específicos para toda a cadeia de alarmes.

## 1.10.0 - 2026-10-04

- Perfil externo de estação via QRZ.com XML API, opt-in, com credenciais, cache e foto quando fornecida oficialmente.
- Provedor AIS genérico/configurável por MMSI/IMO, sem scraping e com cache.
- Metadados RF extensíveis: RSSI, SNR, DCD, frequência, canal e origem; DCD serial é lido quando exposto pelo driver.
- Diagnóstico dedicado do Kenwood TM-D700 em PKT e protocolo formal de validação física.
- Soak test integrado com perfis prolongados e relatório de possível memory leak.
- Matriz de migração histórica integrada à CI.
- Auditoria contínua de traduções com paridade ES/FR, validação de chamadas tr() e relatório de strings visíveis candidatas.
- Mantidas todas as funções da v1.9.0 e builds Windows x64/ARM64, Linux x86_64/ARM64 e macOS ARM64/Intel.

## 1.9.0 - 2026-10-04

- **Interface destacável:** Mensagens e Estações podem ser desacopladas e mantidas sobre o Mapa com arraste, redimensionamento, minimização, encaixe e persistência local de geometria.
- **Busca Global:** pesquisa estações, objetos, WX, AIS, repetidores e texto contextual.
- **Organização:** metadados de estação com nome amigável, cor, nota e grupos.
- **Backup completo:** geração ZIP com snapshot SQLite e manifesto versionado; restauração valida integridade e cria backup pré-restauração.
- **Alertas:** preferências independentes para estação/favorito apareceu, estação desapareceu, nova mensagem, TNC/APRS-IS desconectado e integridade do banco.
- **Timeline:** visão cronológica única de mensagens, posições, queries e RX/TX RF.
- **Modo apresentação:** mapa em tela cheia com controles mínimos.
- **TNC / RF:** botão de teste não destrutivo para KISS Serial, KISS TCP e AGWPE.
- **Correção crítica preservada:** mantém o hotfix que substitui `$().forEach()` por `$$().forEach()` nos campos de transporte do TNC/RF.
- **Análise:** preserva saúde da rede, comparação de períodos, grafo interativo, CSV e GeoJSON.
- **Plataformas:** pipeline completo com Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.
- **Hardware:** TM-D700 em PKT continua sujeito a validação física; métricas RF seguem limitadas ao que o modem/TNC realmente fornecer.

# Changelog

## 1.8.18 - 2026-10-04

- **TNC / RF — AGWPE:** adiciona transporte **AGWPE TCP** em modo raw AX.25, ao lado de KISS TCP e KISS Serial, com host, porta e radio port configuráveis.
- **Busca rápida:** o Mapa ganha busca por indicativo completo/parcial, priorizando correspondência exata e favoritos, com acesso ao painel lateral da estação.
- **Painel lateral:** nova visão responsiva de estação preserva o mapa visível e oferece atalhos para Mensagens e Log.
- **Estatísticas — saúde da rede:** consolida pacotes, estações, RF × APRS-IS, duplicidade, ACK, RTT e estações novas/desaparecidas.
- **Comparação temporal:** compara o período atual com o período imediatamente anterior de mesma duração, com delta absoluto e percentual sem divisão artificial por zero.
- **Quem fala com quem:** o grafo deixa de ser apenas textual e ganha visualização SVG interativa baseada nas interações observadas.
- **Exportação:** adiciona **CSV** compatível com Excel e **GeoJSON** para ferramentas GIS/QGIS.
- **Diagnóstico:** adiciona resumo de integridade SQLite, plataforma, arquitetura, conexão e armazenamento, além de **pacote ZIP sanitizado** para suporte.
- **Simulador KISS:** adiciona cenários de fragmentação, duplicidade e múltiplos hops para regressão sem rádio físico.
- **Linux ARM64:** pipeline oficial para TAR.GZ, AppImage quando suportado pelo AppImageKit e DEB arm64; updater passa a selecionar assets da arquitetura correta.
- **Segurança de atualização:** impede seleção cruzada de assets Linux x86_64 e ARM64.
- **TM-D700:** mantém explicitamente a validação física RX/TX em modo PKT como pendência de hardware; diagnóstico e captura permanecem disponíveis.
- **Métricas RF:** RSSI/SNR/DCD e ocupação de canal continuam sendo exibidos somente quando o equipamento/protocolo fornecer dados reais.
- Inclui regressões específicas da v1.8.18 e mantém as suítes anteriores.
- Release completa para Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## 1.8.17 - 2026-10-03

- **Mensagens programadas:** nova área **Agendadas** na aba Mensagens, com envio único ou recorrência semanal.
- Os agendamentos suportam **estação específica, lista de estações, boletim APRS e grupo APRS**.
- Para estações/listas, mantém seleção de rota **Automático, APRS-IS, RF direto e RF personalizado**, incluindo path RF personalizado.
- **Listas de destinatários:** permite criar conjuntos reutilizáveis de indicativos, nomeá-los e usá-los em agendamentos.
- Em listas, adiciona intervalo configurável entre destinos e opção de continuar com os demais quando um destino falhar.
- **Falhas e retries:** permite pular a ocorrência ou tentar novamente depois de um período configurável.
- Cada execução registra próxima/última execução, status, erro e resumo com resultado por destino; **Executar agora** testa o agendamento sem alterar a ocorrência futura.
- Agendamentos e listas ficam persistidos no SQLite e a reivindicação da ocorrência devida é atômica para evitar disparos duplicados após reinicialização.
- **Configuração → Mapa:** adiciona **Step do zoom do mapa** com 0,05 / 0,10 / 0,25 / 0,50 / 1,00, aplicação imediata e persistência.
- A sensibilidade da roda/touchpad acompanha automaticamente o step escolhido; há botão **Restaurar zoom padrão**.
- **TNC/RF:** serial aberta sem KISS válido passa a ser estado de atenção, não sucesso. Cabeçalho e painel distinguem aguardando dados, bytes sem KISS, AX.25 inválido e RX KISS ativo.
- O indicador verde fica reservado para transporte com RX KISS/AX.25 realmente ativo.
- Novos textos cobertos em PT-BR, EN, ES e FR.
- Inclui suíte de regressão v1.8.17 com testes funcionais de SQLite, recorrência semanal, zoom configurável e indicação TNC.
- Mantém aberta a validação física específica do Kenwood TM-D700 em modo PKT.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.16 - 2026-10-03

- **Sobre:** corrige o indicativo de Adriano para **PP5AU**.
- **Mapa:** refina o zoom para passos de **0,10**, com `zoomSnap=0.10`, `zoomDelta=0.10`, `wheelPxPerZoomLevel=300` e `wheelDebounceTime=20`.
- **Mensagens → Conteúdo:** substitui os controles separados por um único menu pulldown com **Mensagens, Boletins, Grupos e Telemetria**.
- O menu Conteúdo inclui **Marcar tudo** e **Desmarcar tudo**, aplica as mudanças imediatamente e persiste as preferências.
- **Boletins de grupo** passam a ser controlados separadamente dos boletins gerais.
- **Estações → Ver:** adiciona a árvore de categorias/tipos de estação usada pelo Mapa, com **Selecionar tudo / Remover tudo**.
- **Mensagens → Ver:** adiciona a mesma árvore de tipos de estação e filtra mensagens conforme as estações envolvidas.
- **Mapa, Estações e Mensagens** usam o mesmo estado central de filtros, evitando divergência entre as abas.
- Mensagens cuja estação não possa ser classificada com segurança permanecem visíveis por padrão.
- Um catálogo completo de estações é mantido separadamente do filtro textual da aba Estações, evitando que a busca local altere a classificação das Mensagens.
- Os botões **Ver** e **Conteúdo** indicam visualmente quando existem filtros ativos.
- Inclui regressões específicas para zoom, filtros de conteúdo, menus compartilhados e PP5AU.
- Atualiza dois testes legados da árvore **Ver** para validar os helpers compartilhados sem depender da posição das funções no arquivo.
- Mantém o diagnóstico TNC/RF da v1.8.15 e a pendência de validação física do Kenwood TM-D700 em modo PKT.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.15 - 2026-10-03

- **Sobre:** corrige o indicativo de Adriano para **PP5AU**.
- **Mensagens:** adiciona filtros persistentes e independentes para **Mostrar mensagens**, **Mostrar boletins** e **Ocultar telemetria**.
- **Mapa:** habilita zoom fracionário mais gradual com passos de **0,25**, rolagem mais suave e persistência do nível intermediário no SQLite.
- **Estações:** adiciona ordenação explícita por **Ícone / tipo**, mantém a ordem visual durante atualizações e acrescenta estações novas ao final da lista corrente.
- **Mensagem rápida pela lista:** permite selecionar uma estação e enviar mensagem sem sair da aba Estações, mantendo texto, filtros e posição de rolagem para o próximo destinatário.
- **Proteção de destinatários:** opção para evitar envio rápido a estações identificadas como **DMR, D-Star ou SSIDs -12 a -15**, mantendo aviso visual.
- **Mapa × Estações:** a lista de Estações passa a respeitar os mesmos filtros do menu **Ver**, inclusive DMR/D-Star.
- **TNC/RF:** passa a diferenciar transporte serial aberto de RX KISS/AX.25 efetivo e TX entregue ao transporte.
- O diagnóstico TNC registra **bytes RX/TX**, **frames KISS**, **frames AX.25 inválidos**, último erro RX e estados como aguardando, bytes sem KISS e RX ativo.
- **Kenwood TM-D700:** documenta o uso relatado em **modo PKT** e deixa explícito que o Client não deve forçar o modo TNC/digipeater interno; entregar bytes à serial não é tratado como confirmação de emissão RF.
- Mantém em aberto a validação física específica do TM-D700 em PKT caso seja necessária adaptação de protocolo/configuração.
- Inclui suíte de regressão e validador de produção da v1.8.15.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.14 - 2026-10-02

- Fecha integralmente os cinco backlogs consolidados na linha 1.8.
- **Sobre → O que é APRS?:** adiciona explicação explícita de APRS, cobrindo posição, mensagens, telemetria, meteorologia, RF e APRS-IS.
- A explicação acompanha **PT-BR, English, Español e Français** e muda imediatamente com o idioma da interface.
- **Mapa → Relevo com corte:** passa a aplicar **hillshade calculado diretamente do DEM Terrarium**, usando gradiente local de altitude e iluminação de relevo.
- O hillshade preserva o corte por cota, o slider vertical, máximo padrão de **3.000 m**, faixa configurável de **100 a 9.000 m** e opacidade persistente.
- Mantém **Automático / APRS-IS / RF direto / RF personalizado** por mensagem.
- Mantém a responsividade de baixa altura para **1360×768 e 1280×720**.
- Mantém bloqueadas Mensagem, Posição, Status, Ouvidos, Ping/ACK e Trace para alvos identificados como não interativos sem evidência de suporte bidirecional.
- Preserva integralmente o hotfix SQLite da v1.8.12 e a consolidação da v1.8.13.
- Adiciona testes e validador de produção específicos da v1.8.14.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.13 - 2026-10-02

- Consolida e valida **Mensagens → Rota de envio** com **Automático, APRS-IS, RF direto e RF personalizado**, incluindo path por mensagem e retry preservando a rota original.
- Reforça a regressão de **responsividade em telas baixas**, cobrindo a regra usada em **1360×768** e **1280×720**, com compositor de Mensagens compacto e ações do popup de estação acessíveis.
- Consolida o bloqueio de interações para **objetos/itens APRS e infraestrutura sem evidência de capacidade bidirecional**, desabilitando Mensagem, Posição, Status, Ouvidos, Ping/ACK e Trace.
- Consolida **Mapa → Camadas → Relevo com corte**, usando DEM real, slider vertical, cota persistente, máximo padrão de 3.000 m configurável de 100 a 9.000 m e opacidade independente.
- Consolida a aba **Sobre**, com identidade do projeto, contatos, tiny.cc/aprs, divulgação APRS e traduções PT-BR/EN/ES/FR.
- Mantém integralmente a correção de migração SQLite da **v1.8.12** para bancos existentes.
- Adiciona suíte de regressão dedicada aos cinco requisitos consolidados e atualiza o validador de produção para a v1.8.13.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.12 - 2026-10-02

- Corrige falha de inicialização em instalações atualizadas a partir de banco antigo: **`sqlite3.OperationalError: no such column: medium`**.
- A migração da tabela `packets` passa a adicionar primeiro as colunas **`medium`** e **`rx_fingerprint`** e somente depois criar os índices que dependem delas.
- O hotfix é **não destrutivo**: preserva mensagens, estações, logs, tracklogs e demais dados existentes.
- Adiciona teste de regressão que recria explicitamente um banco legado sem `medium`, executa `init_db()` e confirma a migração automática.
- O teste confirma também a criação posterior dos índices `idx_packets_medium_time`, `idx_packets_medium_call_time` e `idx_packets_fingerprint_time`.
- Mantém integralmente as melhorias da v1.8.11: recepção **RF × APRS-IS** nas Estatísticas, estações RF na aba TNC/RF e títulos laranja/maiores na Configuração.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.11 - 2026-10-02

- Corrige a perda da origem de recepção nos pacotes: cada entrada persistida passa a registrar explicitamente **RF** ou **APRS-IS**.
- Adiciona uma impressão lógica do pacote que ignora o path APRS para correlacionar a mesma transmissão observada pelos dois meios em uma janela curta.
- A aba **TNC / RF → Estações ouvidas por RF** passa a usar evidência persistente e consegue recuperar estações RF mesmo quando o resumo `tnc_heard` estiver incompleto.
- A tabela RF passa a mostrar **Recepções, Pacotes RF persistidos, Distância, recepção direta/via digi quando conhecida, último tipo e path**.
- A posição/distância é incorporada quando a estação possui coordenadas válidas e a estação local está configurada.
- As **Estatísticas** passam a exibir um resumo **RF × APRS-IS**, incluindo pacotes RF, estações únicas RF, frames RF recebidos, pacotes APRS-IS, estações vistas nos dois meios e total lógico deduplicado.
- O ranking de estações ganha colunas separadas **RF** e **APRS-IS**, preservando os dois fatos de recepção para o mesmo indicativo.
- O indicador superior **Pacotes observados** passa a preferir o total lógico deduplicado entre meios quando disponível.
- A recepção RF não é inferida a partir do indicativo: somente pacotes que entraram efetivamente pelo pipeline TNC/KISS recebem `medium=RF`.
- Recepção APRS-IS continua registrada separadamente, mesmo quando o mesmo indicativo ou a mesma transmissão também foi vista por RF.
- Adiciona diagnóstico **tnc_rf_station_heard** para nova estação RF e resumo periódico **tnc_rf_rx_summary**.
- Na aba **Configuração**, os títulos dos blocos passam a usar **laranja**, fonte maior e hierarquia visual mais clara, com adaptação para tema claro/escuro e telas menores.
- Inclui regressões para RF-only, RF+APRS-IS, deduplicação entre meios, fallback da tabela TNC/RF, Estatísticas e estilo dos blocos de Configuração.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.10 - 2026-10-02

- Unifica no cabeçalho o **indicador de estado APRS-IS** e a ação **Conectar/Desconectar** em um único componente clicável.
- O novo controle mostra diretamente estados como **Desconectado, Conectando…, Reconectando…, Conectado e verificado, Conectado sem verificação e Conexão perdida**.
- A ação disponível deixa de ser inferida pelo texto do botão e passa a usar os estados reais do backend: `wanted`, `connected` e `verified`.
- O componente exibe texto principal de estado e uma linha secundária com a ação/contexto, além de cor e indicador visual.
- Cliques concorrentes são bloqueados enquanto uma ação de conectar/desconectar está em andamento.
- A validação dos campos obrigatórios antes da conexão e o comportamento atual de reconexão APRS-IS são preservados.
- Remove a redundância visual do antigo indicador separado + botão independente no cabeçalho.
- A aba **Sobre** ganha uma seção **Agradecimentos / Colaboradores** dedicada aos radioamadores que ajudam na evolução do software com sugestões, testes, validações e ajustes.
- Colaboradores incluídos: **PP5AU — Adriano; PY4EI — Allan; PU2MUS — Marco; PP5PK — Daniel Kondlatsch; PT2YW — Ywstter; PT2PAG — Paulo Galvão**.
- A seção de agradecimentos é preparada para receber novos colaboradores futuramente e mantém indicativos em destaque.
- Textos da conexão e dos agradecimentos disponíveis em **PT-BR, EN, ES e FR**.
- Inclui testes de regressão para estados do controle de conexão, eliminação do indicador redundante e presença dos seis colaboradores.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.9 - 2026-10-02

- A checagem automática de nova versão passa a usar **15 minutos como padrão**.
- Adiciona em **Configuração → Atualizações** o campo **Intervalo de verificação (minutos)**, persistido no SQLite e aplicável sem reiniciar o Client.
- O intervalo é limitado entre **5 e 1.440 minutos**; a verificação manual continua independente.
- O agendador de update passa a ser reprogramado imediatamente ao salvar a configuração, sem manter o antigo timer fixo de 30 minutos.
- Objetos APRS passam a armazenar, quando disponíveis, **primeira recepção, altitude máxima observada, velocidade, curso, path, meteorologia, comentário, status e estado ativo/inativo**.
- Novo normalizador de objetos prepara campos amigáveis para **balões/radiossondas, RDZSonDe, estações meteorológicas, AIS/embarcações, repetidores, DMR, D-Star, alertas, itens APRS e outros objetos**.
- Balões/radiossondas podem exibir altitude atual/máxima, subida/descida, velocidade vertical/horizontal, curso, frequência, temperatura, umidade e pressão.
- Objetos WX podem exibir temperatura, umidade, pressão, vento, rajada e chuva quando esses dados estiverem disponíveis.
- AIS pode exibir MMSI, velocidade, curso e destino quando presentes.
- Repetidores e objetos de infraestrutura podem exibir frequência, offset e CTCSS quando detectáveis.
- Todos os popups de objetos passam a ter apresentação amigável e uma seção recolhível **Dados técnicos**, com formato APRS, path e pacote bruto.
- O popup omite campos vazios e não inventa valores ausentes; objetos desconhecidos recebem apresentação genérica organizada.
- Traduções atualizadas para PT-BR, EN, ES e FR.
- Inclui testes de persistência/agendamento do intervalo e regressões de normalização/popup de objetos.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.8 - 2026-10-02

- Otimiza profundamente **Mapa / SQLite** após diagnóstico de saturação do servidor interno e alto uso de CPU.
- `/api/map-data` passa a usar **single-flight global**: somente uma geração pesada do mapa pode executar por vez.
- Chamadas concorrentes recebem imediatamente o **último snapshot válido em cache**, em vez de iniciar novas consultas SQLite iguais.
- Na primeira carga, se outra geração já estiver ocupando o mapa, o backend evita enfileirar vários workers e sinaliza estado ocupado sem substituir o mapa atual.
- Remove os **EXISTS correlacionados por estação** usados para descobrir capacidade/interação em Mapa e Estações.
- A evidência de interação passa a ser calculada em uma consulta consolidada por conjuntos e reutilizada pelas duas telas.
- Adiciona índices SQLite específicos para mensagens recebidas, ACK/REJ enviados e queries APRS respondidas.
- O endpoint de mapa passa a registrar `map_data_build` com duração e quantidade de estações, objetos e pontos de tracklog.
- O refresh completo do mapa passa de **10 s para 15 s**; animações/tráfego continuam em cadência própria.
- O frontend preserva o mapa atual quando o backend sinaliza que a primeira geração ainda está ocupada.
- A descoberta serial automática fica mais leve: **Windows CIM/PowerShell deixa de rodar no polling periódico**.
- O polling serial automático passa a usar fontes leves a cada **30 s**; a varredura CIM/PnP completa fica para abertura/reescan completo.
- A varredura serial completa ganha cache de **60 s**, preservando a identificação avançada de CH9102/CH340 e Radtel da v1.8.7.
- Inclui testes de concorrência que falham se múltiplos builds pesados de `map_data` forem iniciados simultaneamente.
- Inclui regressões para cache stale-while-busy, índices SQLite e polling serial leve.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.7 - 2026-10-02

- Amplia a descoberta de portas seriais do **TNC / RF**, combinando **pyserial**, **Windows CIM/PnP** e o registro **SERIALCOMM**.
- Passa a listar todas as portas COM encontradas por qualquer uma das fontes, inclusive interfaces **CH9102/CH9102F/CH9102X, CH340/CH341, CP210x, FTDI e CDC/ACM**.
- Adiciona a seção **Equipamentos seriais detectados**, mostrando porta, identificação/descrição, interface/chipset, fabricante, VID:PID, número de série/HWID e estado.
- Evita atribuir um modelo de rádio apenas pelo chipset USB; **Radtel RT-950 Pro** só é identificado nominalmente quando os metadados realmente indicam o modelo.
- Adiciona seleção direta do equipamento detectado e preenchimento automático da porta COM.
- A porta serial passa a aceitar **digitação manual**, permitindo usar uma COM mesmo quando a enumeração automática não fornecer metadados completos.
- Adiciona **Reescanear** e atualização periódica da lista de equipamentos enquanto a aba TNC / RF estiver aberta.
- Para interfaces **CH9102**, exibe orientação condicional para o **Radtel RT-950 Pro em TNC UART**; quando o rádio for identificado nominalmente, seleciona **115200 bps** como baud rate.
- A abertura serial passa a apresentar mensagens mais claras para porta inexistente/desconectada e para porta ocupada/acesso negado pelo Windows.
- Cada alteração da lista de portas é registrada no diagnóstico com device, descrição, fabricante, HWID, VID/PID, número de série e fontes de enumeração.
- Inclui regressão específica com **COM6/CH9102 e COM10/CH340 simultâneos**, além dos testes de interface e fallback nativo.
- Mantém integralmente mapas, APRS-IS/RF, mensagens com path individual e demais recursos da série 1.8.x.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.6 - 2026-10-02

- Corrige regressão da **v1.8.5** em que os **itens/camadas do mapa podiam desaparecer**.
- Restaura a geometria global de **header, abas e `main`** usada pelo Leaflet, removendo a compactação global introduzida para telas baixas.
- Mantém a adaptação para **1360×768** restrita à **aba Mensagens** e ao **popup de estação**, sem alterar a altura estrutural do mapa.
- O menu **Mapa → Ver** agora é renderizado imediatamente, antes da primeira resposta de `/api/map-data`.
- Adiciona sincronização de viewport do Leaflet após **resize** e **orientationchange**.
- Adiciona recuperação única para um estado de visibilidade totalmente desabilitado de forma não intencional.
- O comando **Remover tudo** passa a ser marcado explicitamente para que a recuperação automática não desfaça uma escolha deliberada do usuário.
- O menu **Ver** continua disponível mesmo quando ocorre falha temporária ao carregar os dados do mapa.
- Preserva a seleção por mensagem **Automático / APRS-IS / RF direto / RF personalizado** da v1.8.5.
- Novos testes de regressão cobrem categorias do mapa, recuperação de visibilidade e estabilidade da geometria.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

## 1.8.5 - 2026-10-02

- Adiciona **Rota de envio** por mensagem com **Automático, APRS-IS, RF direto e RF personalizado**.
- O modo **Automático** mantém **APRS-IS como prioridade** e usa RF direto apenas quando o APRS-IS não está disponível e o TNC/RF está pronto.
- **RF personalizado** permite informar paths como `WIDE1-1` e `WIDE1-1,WIDE2-1`, com validação de sintaxe/SSID e bloqueio de `*` digitado manualmente.
- Mensagens RF reutilizam o **TNC/KISS existente** e respeitam conexão, pausa de TX, habilitação e confirmação de transmissão.
- O histórico de mensagens passa a armazenar e exibir o **meio efetivo (APRS-IS ou RF)** e o **path transmitido**.
- Retry preserva a rota/path original por padrão; escolher uma rota explícita no compositor permite substituir o transporte do retry.
- Melhora a responsividade para **1360×768 @ 100%** e outras telas de baixa altura.
- O popup da estação recebe proteção adicional de altura, rolagem interna e ações sticky para evitar controles escondidos.
- A aba Mensagens reduz cabeçalho, espaçamentos e compositor em baixa altura, mantendo lista e campo de envio acessíveis.
- Inclui traduções **PT-BR, EN, ES e FR** e novos testes de regressão.
- Release completa para Windows x64/ARM64, Linux x86_64, macOS ARM64/Intel e Manual PDF.

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
