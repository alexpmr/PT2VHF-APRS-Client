## BACKLOG — PT2VHF APRS Client para Android (30/10/2026)

- **Decisão do mantenedor:** app **nativo em Kotlin** (Bluetooth e execução em segundo plano são o núcleo; a interface web empacotada foi descartada).
- **Mockups:** https://claude.ai/artifact/9NFcGxuWKThfVJVx33sWFD — Mapa (botão "Enviar beacon", APRS-IS/TNC/GPS, enlaces, cobertura), Mensagens (meio e ACK por mensagem, respostas rápidas), Estação (distância/direção, grid, PHG, ouvido por RF, Navegar até, Rota RF), Rádio/TNC (KISS Bluetooth, USB-OTG, TCP; monitor e "Escutar 30 s"), Modo tracker (SmartBeaconing em segundo plano, notificação fixa).
- **Primeira versão:** tracker em segundo plano com SmartBeaconing e GPS; TNC KISS por Bluetooth (Mobilinkd, BTECH UV-Pro, RT-950 Pro) e USB-OTG; APRS-IS com passcode; mensagens com notificação e resposta pela notificação; mapa com estações, enlaces RF e mapa de calor; atualização e contagem pelo pt2vhf.com (`update.php?product=…`, aviso de versão nova e "Downloads no site oficial").
- **Depois:** mapa offline por região; "Navegar até" pelo app de mapas; alerta de estação/amigo por perto; modo carro (botões grandes, tela ligada); análise de rotas/recordes RF e Planejamento (enlace entre 2 pontos) do desktop.
- **Diferencial frente ao APRSdroid:** topologia RF (quem ouviu quem), mapa de calor de cobertura e rotas RF.
- **A definir:** repositório próprio (ex.: `PT2VHF-APRS-Android`), nome do produto no site e no `updates.json`, assinatura do APK, versão mínima do Android.

## BACKLOG — Cabeçalho: botão "Enviar beacon" no lugar do ícone (30/10/2026)

- **Pedido:** no menu superior, trocar o ícone 📡 que envia um beacon (`#headerSendBeaconButton`, classe `beacon-icon-button` em `templates/index.html`) por um botão com o texto **"Enviar beacon"**.
- **Manter:** mesmo comportamento atual (envio imediato por todos os meios ativos, APRS-IS e TNC/RF), tooltip, estados de envio/erro e traduções do texto do botão nos idiomas do cliente; conferir o encaixe no cabeçalho em telas estreitas.

## BACKLOG — Mapa de calor: estação via rede DMR (DMR*) contada como cobertura RF (28/10/2026)

- **Relato com captura:** estação PP5PM-9 (APRSdroid no celular), deslocando-se de Belo Horizonte até Aracaju pela BR-116, aparece como trilha no mapa de calor da Cobertura RF, embora não tenha usado RF (envio pela internet/APRS-IS).
- **Esperado:** somente transmissões/recepções RF reais alimentam `rf_coverage_cells`; pacotes que entraram só pela internet (TCPIP*, qAC/qAS, APRSdroid em modo APRS-IS) não contam.
- **Causa provável (captura do popup):** PP5PM-9, path `PP5PM,DMR*,qAR,PP5PM`. `DMR*` é a marca do gateway APRS da rede DMR (ex.: BrandMeister), não um digipeater; o cliente trata todo elemento com `*` como digi e registra "enlace RF" PP5PM-9 → DMR, alimentando `rf_coverage_cells`. O 1º elemento `PP5PM` (o próprio indicativo/gateway) e o `qAR,PP5PM` também não comprovam RF.
- **Correção proposta:** tratar como não-RF (igual a TCPIP/NOGATE) os pseudo-saltos de redes digitais e gateways: `DMR`, `DSTAR`/`D-STAR`, `YSF`, `C4FM`, `NXDN`, `P25`, `M17`, `TETRA`, `ECHOLINK`, `LORA*`/gateways equivalentes; pacote com esses marcadores não gera evento `rf` nem célula do mapa de calor. Limpar eventos/células já gravados com esses pseudo-saltos (migração única, sem apagar pacotes). Regra também em `_is_topology_callsign`/`rf_coverage.record_event_conn`.

## RESOLVIDO (v1.14.60) — Recordes RF: rota sem todos os enlaces desenhados (27/10/2026)

- **Relato com captura:** recorde CERD ↔ PY2OAL-1 (8 hops) mostra a linha só até PY2NV-15; PY2NV-15 → PY2PJA (214,8 km, 21/10) e PY2PJA → PY2OAL-1 (137,4 km, 21/10) sem linha, embora listados no painel.
- **Provável causa:** saltos antigos fora da camada de enlaces do mapa (RF móvel expirado/sem geometria). A v1.14.60 já liga esses saltos pelas posições da análise (`route-fill`, commit e56574f) — confirmar se a captura é anterior à v1.14.60 instalada (publicação no pt2vhf.com pendente) e, se persistir, verificar também o caminho de "Recordes RF" (`focusRfRecordRoute`).

## RESOLVIDO (v1.14.61) — Estatísticas: reaproveitar o último histórico RF/Recordes (27/10/2026)

- **Pedido (roadmap):** ao entrar em Estatísticas, se já houve cálculo antes, mostrar o último histórico/Recordes RF guardado; recalcular só ao clicar em **Recalcular**.
- **Rascunho, não publicado:** branch `claude/v1.14.61-rf-records-cache` (tabela `saved_results`, `?refresh=1`, job de Recordes reaproveita o salvo; falta ajustar `test_v1421_topology_stats_cache_reuses_full_history_result`).

## RESOLVIDO (v1.14.61) — README regravado com links do GitHub pelo build de produção (27/10/2026)

- O passo "Update README direct downloads" de `build-production-current.yml` roda `tools/sync_readme_release_downloads.py` e regravou o README da v1.14.60 com links do GitHub (commit f9a3439), contrariando downloads só em pt2vhf.com; quebra `test_readme_points_only_to_official_distribution_site`. Correção no mesmo branch acima.

## RESOLVIDO (v1.14.62, APRS) — Aviso "Downloads no site oficial" em todas as aplicações do site (27/10/2026)

- **Pedido (roadmap):** usar em todas as aplicações distribuídas por www.PT2VHF.com (APRS Client, Sat Tool, Prop Tool, Mesh Analyzer, venus-8 e demais) a mesma interface do PT2VHF Mesh Analyzer: modal escuro "Downloads no site oficial", texto "A partir de agora, as novas versões e os instaladores do PT2VHF <aplicação> serão distribuídos pelo site oficial.", link **www.PT2VHF.com** e botão **Entendi**; uma vez por instalação.

## RELEASE — v1.14.59 (25/10/2026): anúncio automático de versão e filtros de mensagens

- **Pedido:** TX automática a cada atualização do cliente, com boletim "Estou usando a versão x do APRS Client. Download em …"; manter o envio manual da aba Sobre.
- **Implementado:** `version_announce.py` — BLNA uma vez por versão, só após atualização (nunca instalação nova), APRS-IS verificado, 2 min após abrir, cancelável no aviso e desligável em Automações.
- **Mensagens "sumidas":** era o filtro Ver compartilhado (estações desmarcadas no mapa). Mensagens da própria estação agora sempre visíveis; lista vazia informa as ocultas. `/api/stations` passa a trazer `map_role` (Ver contava 0 digis/iGates) e TOCALL com cache (30×).

## RELEASE — v1.14.58 (24/10/2026): retenção permanente por padrão

- **Pedido (roadmap):** retenção permanente de todos os itens por default.
- **Implementado:** `retention.DEFAULT_DAYS` todo 0; migração única (`v1.14.58-retention-permanent-defaults`) troca para 0 as categorias ainda no padrão antigo, preservando escolhas diferentes; cartão v1.11 e histórico TNC com o mesmo critério.
- **Confirmado na v1.14.57:** enlaces de volta no mapa (Ver: 773 RF fixos, 26 móveis, 34 iGate).

## RELEASE — v1.14.57 (24/10/2026): causa principal dos enlaces sumidos

- **Após a v1.14.56 o menu Ver seguia com 7 RF fixos / 4 iGate** (156 digis, 292 iGates): a correção do vento não era a causa principal.
- **Causa:** `_position_at_event_conn` (v1.14.44) só aceitava ponto de tracklog a ≤ 12 h do evento, e o tracklog só grava ponto novo com deslocamento ≥ 10 m. Estação fixa ouvida há mais de 12 h ficava sem posição em todo enlace novo → fora do mapa. Explica também o Win10 que "voltou" ao apagar o banco.
- **Correção:** aceitar o último ponto quando a posição atual da estação é a mesma (≤ 100 m); backfill único dos eventos sem posição (+ mapa de calor). Aguardando confirmação do mantenedor.

## CORRIGIDO na v1.14.56 (24/10/2026): enlaces RF fixos e móveis não aparecem na v1.14.55

- **Relato:** na última versão as linhas de enlace RF fixo e móvel não aparecem, mesmo marcadas em Ver.
- **Reprodução:** não reproduzido — com pacotes reais (digi, iGate, tracker, estação fixa) a API entrega os enlaces e o mapa desenha as linhas na v1.14.55; Planejamento usa camada própria. `/api/topology` com 120 mil eventos: 0,7 s.
- **Suspeitas no banco real:** pontas sem marcador (estações apagadas pela retenção — tela corrigida na v1.14.53 —, "Limpar tudo" ou posição em quarentena) ocultam RF inferido; estações classificadas como móveis (regra de velocidade da v1.14.50) mostram só o último contato por 3 h.
- **Causa (captura do menu Ver: 5 RF fixos, 2 móveis, 4 iGate com 158 digis/290 iGates):** o aprslib entrega vento `_DDD/SSS` como course/speed; a regra de velocidade da v1.14.50 tornava iGates/digis meteorológicos "móveis". Correção: velocidade só vale com tracklog espalhado ≥ 0,5 km; vento não é gravado como velocidade.
- **Ação:** v1.14.56 adiciona "Enlaces no mapa" ao Verificar banco; pedir o resultado ao mantenedor.

## RELEASE — v1.14.54 (22/10/2026): teste de recepção do TNC e Verificar banco

- **TNC sem bytes (#118):** "Escutar agora" (10–30 s, sem TX) com veredito e dicas (nenhum byte / texto = modo terminal / lixo = velocidade serial / KISS sem AX.25 / OK) e monitor de bytes ao vivo (`/api/tnc/rx-monitor`, `/api/tnc/listen-test`). O teste anterior (`probe_transport`) lia só os bytes disponíveis no instante da abertura. **Aguardando o mantenedor rodar na COM10 (RT-950 Pro).**
- **Enlaces sumidos no Win10:** `db_check.run_check()` aponta colunas de geometria ausentes (com elas faltando, `list_map_edges` devolve lista vazia), eventos sem posição e corrupção; `repair()` recria estrutura e refaz o backfill sem apagar dados. **Na próxima ocorrência, rodar Verificar banco antes de apagar o banco.**
- **Backlog revisto:** #125, #124 e #106 já implementados; títulos atualizados.

## RELEASE — v1.14.53 (22/10/2026): retenção própria do mapa de calor

- **Pedido:** na aba Configurações, especificar o tempo de retenção do mapa de calor, sem depender da retenção de tracklogs, estações, digis etc.
- **Implementado:** tabela `rf_coverage_cells` (célula ~1 km × dia) alimentada na ingestão e por backfill único; categoria de retenção `rf_coverage` (padrão Permanente) com "Limpar tudo" e contagem nas Estatísticas; `/api/topology/rf-coverage` lê dessa tabela.
- **Defeito encontrado e corrigido:** desde a v1.14.44 a tela de retenção não carregava os valores salvos e o botão Salvar falhava (`for…of` sobre `$()`).

## RELEASE — v1.14.52 (21/10/2026): mapa de calor clássico e aviso de nova versão

- **Mapa de calor (pedido com captura de referência):** o anterior era claro e gordo demais. Agora densidade → paleta azul…vermelho, raio geográfico ~1,5 km, sem `mix-blend-mode: screen`, legenda.
- **Popup de nova versão:** além do indicador no cabeçalho, o aviso de atualização abre sozinho perguntando se deseja atualizar; "Depois" adia por 24 h. **Mesmo recurso pedido para Sat Tool, Prop Tool, Mesh Analyzer e venus-8** — tratado em cada repositório.

## RELEASE — v1.14.51 (21/10/2026): Cobertura RF em mapa de calor

- **Pedido:** ao habilitar a visualização de cobertura RF, criar um mapa de calor com os pontos onde houve pelo menos uma vez transmissão ou recepção por RF.
- **Antes:** havia duas opções — "Cobertura RF observada" (só digis móveis, em círculos) e "Cobertura RF" da v1.42 (só pacotes do TNC local; vazia em bancos APRS-IS).
- **Implementado:** `topology_map.list_rf_activity_points` agrega em células de ~1 km as posições de origem (TX) e destino (RX) de todos os eventos RF, com peso logarítmico; `/api/topology/rf-coverage` passa a usá-la e o menu Ver tem uma única opção "Cobertura RF (mapa de calor)", desenhada com o heatmap da v1.42.

## RELEASE — v1.14.50 (21/10/2026): trackers sem enlaces órfãos (#116)

- **Relato com captura:** tracker em Ceilândia com três linhas amarelas (RF fixo) de pontos antigos do trajeto até o digi da Asa Norte. Pedido: mostrar só o enlace mais recente.
- **Causa:** `moving_rf_repeaters` exigia deslocamento ≥ 25 km; o tracker local era tratado como fixo e cada região (bin espacial) gerava um segmento próprio.
- **Correção:** velocidade > 3 km/h em ≥ 2 pontos do tracklog classifica a estação como móvel (RF móvel, último contato, TTL); e, em qualquer caso, um único segmento por origem → destino → tipo, no contato mais recente. Reproduzido com pacotes reais: v1.14.47 → 3 linhas `rf`; v1.14.50 → 1 linha `rf_mobile`.

## RELEASE — v1.14.49 (20/10/2026)

- **Trackers móveis (#116):** relato do mantenedor: "o enlace só é mostrado quando há uma animação, sumindo após isso". Reproduzido com tracker deslocado >25 km e ouvido por digi fixo: `_segments_from_events` descartava todo enlace de móvel que não fosse digi/iGate (regra da #94), embora a animação desenhasse o trecho. Decisão do mantenedor: mostrar o **último contato RF válido** de cada móvel, inclusive trackers, como `rf_mobile`, com TTL e filtro Ver → Enlaces móveis. Testes antigos da regra "tracker oculto" reescritos.
- **Menu Ver:** contagem em Tracklogs, Enlaces RF fixos, Enlaces móveis e Enlaces iGate, com os filtros da visão geral e independente da caixa marcada.
- **EM INVESTIGAÇÃO — computador do mantenedor sem tracklogs e enlaces fixos (RF e iGate) após atualizar para v1.14.48:** outro computador atualizado de v1.14.41 para v1.14.48 exibe tudo normalmente; código de mapa/topologia idêntico à v1.14.46, API e renderização verificadas sem regressão. Suspeitas: caixas do menu Ver desmarcadas (preferências por origem do navegador), pasta de dados diferente ou dados do banco. As novas contagens do menu Ver permitem distinguir. Coletar captura do menu Ver, aba Estatísticas e `diagnostics.log`.

## RELEASE — v1.14.48 (19/10/2026)

- **Motivo:** o CI da v1.14.47 falhou em todas as plataformas por um teste desatualizado (`test_v1429` exigia o prefixo `Web:` removido no #99); a v1.14.47 nunca foi publicada. A v1.14.48 inclui todo o conteúdo da v1.14.47.
- **Mapa offline:** Leaflet 1.9.4 servido localmente com SRI; `.gitattributes` evita CRLF no checkout Windows (que quebraria o SRI nos instaladores).
- **#118 (P0):** diagnóstico de código: TNC/serial sem mudanças entre v1.14.41 e v1.14.43, portanto não é regressão de código. Hipótese: DTR/RTS ativados pelo pyserial acionando PTT/modo de programação no cabo. Implementados controle DTR/RTS e leitura das linhas da porta. **Aberto até teste no RT-950 Pro do PP5AU com RTS/DTR desativadas.**
- **#121:** quarentena reversível das posições antigas contaminadas (stations/tracks), `packets` preservado, `restore_quarantined_positions()`. **Aberto até conferência no banco real do PP5AU.**
- **#103:** helper do Setup verifica a versão em execução (marcador de prontidão), relança pela pasta registrada no Inno Setup e grava `last_update_result.txt`; falso sucesso é exibido ao usuário. **Aberto até teste no Windows 10 afetado.**
- **#86:** ordenação alternável dos Recordes RF (extremidades / percurso total). Pendente apenas validação de campo da busca de caminhos.
- **#116:** sem alteração de geometria nesta versão; a quarentena da #121 remove uma causa confirmada. Restante exige o banco real e capturas com período/extremidades.
- **Demais issues abertas (#128, #125, #124, #109, #107, #106, #99, #98, #96, #95, #94, #93, #87, #85, #84, #83, #82, #81, #80, #79, #78, #77):** já implementadas em versões anteriores segundo este backlog e o código; aguardam validação visual/física do mantenedor para encerramento.
- **Manutenção:** topologia espaço-temporal ligada explicitamente em `database.py` (fim do monkey-patch, ~310 linhas mortas removidas).

## SUBSTITUÍDA PELA v1.14.48 — v1.14.47 (19/10/2026; build falhou, pacotes não publicados)

- **Escopo deste ciclo:** tipografia da versão do cabeçalho igual ao título (#128) e remoção de prefixos visíveis no indicador Web (#99).
- **Preparação:** VERSION, Python, Windows version_info, CHANGELOG e VERSION_NOTES atualizados; testes em `tests/test_v11447_header.py` e validador `tools/apply_release_1_14_47.py`; workflows de compilação atualizados para 1.14.47.
- **Publicação:** commit com prefixo `release:` dispara pipeline `build-production-current.yml` para instaladores completos e portáteis Windows, Linux e macOS e manual PDF. Não confundir código enviado ao GitHub com artefatos já publicados; acompanhar CI e assets antes de marcar como disponível.
- **Bloqueadores não resolvidos:** TNC físico COM10 RT-950 Pro (#118), enlaces órfãos reais (#116) e atualização portátil com erro de DLL (#103/#83), exigindo reprodução em hardware e Windows afetados.


## EM COMPILAÇÃO — v1.14.47: versão com tipografia idêntica ao título (#128, 19/10/2026)

- **Pedido:** exibir a versão `vX.Y.Z` à direita do nome **PT2VHF APRS Client**, com **mesma fonte, tamanho e peso do título** em vez de texto pequeno.
- **Origem:** `index.html` contém `h1` com `span.app-version`. Em `app.css`, o título está a 20px e `.app-version` a 13px; aplicar estilo contextual restrito ao `h1` do cabeçalho, preservando as versões de outras páginas como **Sobre**.
- **Aceite:** responsividade, zoom, legibilidade, temas claro/escuro/cinza; mesma linha sem sobreposição e sem alterar o número de versão ou lógica de atualização.
- **Rastreamento:** [issue #128](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/128). **Status: código implementado na v1.14.47; testes automatizados e publicação multiplataforma em andamento.**

## EM COMPILAÇÃO — v1.14.47: indicador Web somente IP:porta (#99, 19/10/2026)

- **Pedido reiterado com captura:** remover o texto **“Web em uso”** do botão no cabeçalho. Remover igualmente os estados `Web LAN:`, `Web local:` e `Web:`; **mostrar apenas IP:porta**, mantendo destaque laranja quando houver sessão Web remota.
- **Causa:** `app.js::updateWebAccessStatus()` reinjeta prefixos em `#webAccessLabel`; `index.html` traz o valor inicial `Web local:`. Alterar ambos sem permitir reaparição no refresh, mudança de idioma, estado remoto ou reconexão; guardar status textual no tooltip/acessibilidade, fora do botão.
- **Preservar:** destino real do IP/porta, clique para abrir navegador, ativação Web LAN quando necessário com testes de listener, estados remotos e regras de segurança já previstas.
- **Rastreamento:** [issue #99](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/99), atualizada. **Status: remoção dos prefixos implementada na v1.14.47; ainda pendem validações do clique/ativação LAN previstas na issue #99.**

## IMPLEMENTADO — README: Downloads por arquivo da versão corrente (#127, revisão 18/10/2026)

- **Solicitação atual do mantenedor:** manter a seção **Downloads** no início do README com tabela de 14 formatos, e exibir a última coluna **Downloads da versão** como **valor numérico direto**, sem símbolo `≥`.
- **Métrica correta:** consumir `download_count` de **cada asset da release atualmente publicada** via `GET /repos/{owner}/{repo}/releases/latest`; **não somar versões antigas**, snapshots anteriores, tags históricas nem arquivos auxiliares.
- **Zeragem por nova release:** quando uma versão nova for publicada, a tabela e os links passam a refletir **somente os assets da nova versão**; downloads da release anterior não entram no cálculo. Valor `0` é válido quando a API registra zero para um asset existente; asset inexistente ou contagem não fornecida aparece como `—`/Indisponível, nunca como zero fabricado.
- **Categorias:** Windows instalável/portátil x64/ARM64 e Win7 Legacy; Linux AppImage, DEB e TAR.GZ para x86_64/ARM64; macOS DMG Intel/Apple Silicon. Link `Baixar` deve apontar para asset efetivo **da própria versão corrente**, sem fallback de outras versões ou URL antecipada.
- **Totais:** soma de downloads dos pacotes com contador disponível da versão corrente; não conta manuais PDF, checksums, SBOMs, licenças, arquivos de Actions ou instalações/usuários únicos.
- **Automação:** `tools/sync_readme_release_downloads.py` passou a consultar somente a última release; `.github/workflows/update-download-counts.yml` sincroniza diariamente, por demanda e quando o script é alterado; pipeline de publicação chama o sincronizador após disponibilizar todos os pacotes. O histórico `data/release_download_history.json` é legado e **não participa mais** dos números mostrados na tabela.
- **Implementação:** README alterado com sucesso, a coluna passou a exibir números diretos, testes de versão corrente adicionados em `tests/test_download_totals.py`; conferir a release publicada e possíveis atualizações via CI.
- **Rastreamento:** [issue #127](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/127), encerrada. O pedido antigo de acumular downloads desde o início foi **explicitamente substituído** pela solicitação de contabilizar apenas a versão atual.

## EM TESTES — v1.14.46: Automações, LEDs TX/RX unificados e rejeição APRS inválido (#125 #124 #121)

- **Auto-resposta (#125):** aba Automações criada; card retirado de Configurações e migrado sem regravar preferências antigas. Mensagens privadas distintas seguidas são respondidas; controles anti-loop mantidos por conteúdo reconhecido, deduplicação e limite de 12 respostas/janela configurável. Exige teste real entre estações APRS.
- **TX ○ RX ○ (#124):** barra apresenta LEDs independentes de TX/RX para APRS-IS e contadores de bytes reais do TNC. Conexão sem bytes não acende indicador. Tooltip separa meios; precisa teste visual nos temas.
- **Latitude PP5BLU-15 (#121):** APRS DDMM.mm com 77,84 minutos ou valor >=60 é rejeitado antes de gravar nova posição/topologia; raw e pacote continuam íntegros. Na visão geral, eventos históricos com payload bruto malformado são filtrados sem apagar o SQLite. A posição de estação antiga já contaminada precisa saneamento assistido e não foi alterada automaticamente.
- **P0 e P1 não encerrados:** COM10 RT-950 Pro sem bytes RX (#118), demais causas de enlaces órfãos (#116), problemas do portable updater e backlog histórico permanecem até repro/testes físicos.
- **Status:** implementado na branch v1.14.46, aguardando CI e compilação antes de declarar publicado.

## IMPLEMENTADO na v1.14.46 — Aba Automações: primeiro item Auto-resposta, migrar de Configurações (#125, 18/10/2026)

- **Novo menu/aba Automações:** criar aba principal dedicada e iniciar com o card **Auto-resposta** (ligar/desligar, texto personalizado e Salvar). Sem automações adicionais neste pedido; estrutura preparada para futuras funções.
- **Reutilizar o que já existe:** `v111.js::installAutoReply()` insere atualmente um card **Resposta automática** em `#tab-config`; migrar a interface para Automações e retirar a duplicata de Configurações. Preservar chaves SQLite `auto_reply_enabled`, `auto_reply_text`, `auto_reply_cooldown_seconds`, configurações previamente salvas e rota `/api/config`.
- **Regra pedida:** cada **mensagem privada nova** dirigida ao indicativo/SSID exato deve receber o texto configurado, inclusive mensagens seguidas do mesmo remetente. Usar o transporte de recepção sempre que operacional/autorizado (TNC/RF ou APRS-IS), registrando no histórico o envio automático.
- **Proteção:** 1 auto-resposta por mensagem única, sem resposta a duplicata, ACK/REJ, consultas, boletins, grupos, mensagens próprias e auto-respostas de terceiros; proteção contra loops e tempestades de mensagens. O cooldown legado hoje mínimo 30s/padrão 300s impede respostas a mensagens distintas; revisar sem perder a preferência previamente salva de usuários que o personalizaram.
- **Ergonomia:** impedir habilitação sem texto válido; clareza de status ativo, inativo e falhas do transporte; respeitar temas, traduções, versão Web LAN, Setup/Portable e atualização de interface.
- **Aceite:** migração sem perda de preferências; duas mensagens privadas distintas geram duas respostas; repetição da mesma não; cenários RF/APRS-IS, TX bloqueado, conteúdo vazio e anti-loop em testes unitários e visuais.
- **Rastreamento:** [issue #125](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/125). **Apenas backlog; não implementado nesta etapa**.

## IMPLEMENTADO na v1.14.46 — Indicadores compactos TX ○ RX ○ agregando APRS-IS e TNC/RF (#124, 18/10/2026)

- **Referência visual do operador:** substituir o componente de setas ↑/↓ da barra superior por **TX ○  RX ○**, texto fixo e dois LEDs circulares compactos.
- **Requisito:** o LED **TX** acende brevemente em transmissão real para qualquer transporte ativo/autorizado (**APRS-IS e TNC KISS serial/TCP/AGWPE**). **RX** acende ao entrar tráfego APRS-IS ou bytes RX efetivamente recebidos do TNC; bytes brutos e frames válidos devem ser distinguíveis nos diagnósticos.
- **Eventos independentes:** TX e RX podem piscar simultaneamente; cada um com temporizador próprio. Não acender por status conectado, TX liberada, pacote antigo, beacon apenas enfileirado ou atualização da página.
- **Visual:** círculos vazados/discretos em repouso, iluminados durante atividade, com contraste em temas claro/escuro/cinza. Manter dimensões pequenas sem elevar a barra.
- **Tooltip informativo:** separar contadores e horários de **APRS-IS RX/TX** e **TNC/RF RX/TX**, exibindo estágio de recepção TNC quando possível; não confundir entrega de bytes ao TNC com RF efetivamente irradiado.
- **Origem técnica:** `index.html #trafficActivityIndicator` usa setas; `app.js updateTrafficActivityIndicator()` atualmente monitora somente APRS-IS, e `flashTrafficIndicator()` apaga ambos com um único timer; integrar `tnc_service.status()` com RX bytes/frames, TX frames e estados reais, sem polling oneroso.
- **Aceite:** APRS-IS sozinho, TNC sozinho, ambos, beacon multicanal, simultaneidade TX/RX, COM10 aberta com 0 bytes, reconexão e reset de contador, interface Web LAN e variantes do Windows. Ver [issue #124](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/124).
- **Status:** backlog especificado; **ainda não implementado, testado ou incluído na release**.

## EM TESTES — v1.14.45: restauração do contraste e traço RF normal (#122)

- **Bug confirmado na v1.14.44:** arestas RF inferidas ficaram cinza `#9ca3af`, tracejadas `5 6` e de baixíssimo contraste nas capturas de Brasília.
- **Correção candidata:** RF fixo (direto e inferido) usa `topology_rf_color`, `topology_width` e traço contínuo. Internet/iGate continua tracejado com cor própria; enlaces móveis e temporários preservam as características anteriores.
- **Sem mudança de evidência:** inferência permanece declarada no popup e no histórico. A correção visual não resolve sozinha os enlaces órfãos (#116), a coordenada inválida PP5BLU-15 (#121) nem a COM10 sem bytes do PP5AU (#118).
- **Aceite:** testes automatizados e screenshots com temas claro/escuro/cinza e período selecionado. [Issue #122](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/122).

## NOVA CAUSA CONFIRMADA — APRS latitude malformada PP5BLU-15 contamina topologia (#121, 18/10/2026)

- **Evidência PP5AU:** pacote `PP5BLU-15>APBK20,WIDE1-1,WIDE2-1,qAR,PP5APR-10:!2677.84S/04900.03W#...` contém latitude 26°77,84'S (minutos APRS fora do intervalo válido). A indicação de app externo `Location changes too fast (adaptive limit)` não prova processamento no Client.
- **Defeito duplo:** (1) beacon transmitido pelo digipeater tem coordenada incorreta; (2) o APRS Client aceitou e converteu a latitude para -27,297333°, persistindo estações, tracklog e eventos de topologia. O banco de PP5AU contém 13 beacons PP5BLU-15 iguais e enlaces inferidos via iGate PP5APR-10 contaminados.
- **Outro dado:** a estação PP5BLU-14 transmitiu um objeto PP5BLU-15 com posição distinta (~44 km). Não considerar o objeto automaticamente autoritativo nem tentar adivinhar a coordenada correta do beacon.
- **Correção necessária:** validar formato original APRS DDMM.mm/DDDMM.mm **antes** de aceitar posição em APRS-IS ou RF; minutos em [0,60); preservar pacote bruto, indicativo e log para auditoria sem atualizar coordenadas/tracklogs/linhas; sinalizar anomalia e não reutilizar geometria de eventos históricos contaminados. Testar formatos convencionais válidos, objetos, timestamps e Mic-E sem regressão.
- **Release 1.14.44:** seu filtro visual de posição histórica é insuficiente quando o próprio banco contém uma coordenada falsa e coerente com o marcador atual; corrigir no parser/persistência antes de considerar enlaces órfãos solucionados.
- **Classificação:** `medium=APRS-IS`, `evidence_level=inferred` com `qAR` não comprova RX na COM10 de PP5AU. A issue #118 de TNC sem bytes permanece independente.
- **Rastreamento:** [issue #121](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/121) e [issue #116](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/116). **Pendente; não testado nem publicado como correção.**
## EM TESTES — v1.14.44: beacon multicanal, RT-950 Pro e RF inferido (#119, #118, #116)

- **Implementado na PR #120, pendente de CI/release:** clique manual (ícone da barra e Configuração) e beacon automático enviam por cada transporte operacional e autorizado: APRS-IS e TNC/RF. Sem cooldown manual; sucesso/erro independentes por meio; sem cabeçalho TCPIP* no frame AX.25. O TNC coloca o pacote na fila, sem afirmar irradiação RF.
- **Radtel RT-950 Pro (#118):** perfil configurável UART KISS 115200 bps por ação explícita, sem mudar a COM/baud salva em atualizações. A falha PP5AU (COM10 CH340 sem bytes RX) continua **P0 aberta** até validação física com firmware, TNC em RX/Both e captura KISS real.
- **Enlaces órfãos (#116):** a visão geral deixa de representar RF apenas inferido de APRS-IS quando a geometria histórica não corresponde aos marcadores atuais dentro de 5 km. Eventos e evidências continuam na API/SQLite e podem ser examinados em rotas detalhadas. Precisa validação em mapa com base real; **P1 permanece aberto**.
- **Demais pendências:** recursos antigos e bugs não foram automaticamente encerrados. Diferenciar implemen­tação candidata de correção validada em rádio real.
- **Rastreamento:** https://github.com/alexpmr/PT2VHF-APRS-Client/pull/120

## P0 — PP5AU Radtel RT-950 Pro UART KISS / COM10 sem RX (#118, 18/10/2026)

- **Equipamento/relato:** Radtel RT-950 Pro no modo TNC KISS UART, cabo USB-serial CH340 COM10, funcionando em versões anteriores; v1.14.42/.43 portáteis abrem a COM mas permanecem aguardando tráfego e sem bytes RX.
- **Hipótese técnica prioritária:** SQLite registra **9600 bps**, enquanto notas de firmware do RT-950 Pro documentam **115200 bps para TNC UART** e configuração de reporte **RX/Both** (https://linuxslate.com/forum/viewtopic.php?p=190). Confirmar versão exata do firmware e configurações anteriores; não confundir baud da UART com modulação RF.
- **Controle de regressão:** `tnc_service.py` e `tnc.js` sem alterações entre v1.14.34–v1.14.43; investigar persistência/migração da velocidade, edição portátil, modo de reporte UART, firmware, ligação RX e parâmetros seriais.
- **Teste seguro:** operador alterar COM10 para 115200 no Client, salvar e reconectar com transmissão RF não acionada, rádio TNC Reporting RX/Both, e verificar contadores bytes/KISS/AX.25; se continuar 0, comparar monitor serial, cabo/pinagem e firmware com ferramenta que funcionava anteriormente.
- **Status:** P0 aberto, hardware não testado nesta etapa, causa ainda não confirmada. [Issue #118](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/118).
## DIAGNÓSTICO DE CAMPO — data.rar PP5AU, TNC RX zerado e enlaces RF inferidos (18/10/2026)

- **Origem:** archive `data.rar` enviado pelo operador de PP5AU; evidência analisada localmente sem publicar o banco, credenciais, posições ou logs brutos.
- **TNC (#118, P0):** aplicativo portátil v1.14.42 e v1.14.43; COM10 detectada como CH340, conectada a 9600 bps; perfil persistido generic_kiss/protocolo kiss; sessões `transport_open_waiting` com zero bytes RX, zero frames RX/TX; tabelas `tnc_frames` e `tnc_heard` vazias. Banco registra 20.350 pacotes, **todos APRS-IS**. Log de quatro beacons PP5AU-7 veio de programa externo, não confirma RX na COM10.
- **Comparação:** módulo `tnc_service.py` tem SHA idêntico nas tags v1.14.41/.42/.43. Investigar modo KISS real do dispositivo, abertura que não inicia KISS, driver/cabo, dependências portátil, e verificar bytes seriais brutos antes do parser. Não atribuir causa sem teste com hardware.
- **Topologia (#116, P1):** 5.114 eventos RF `inferred` derivados do APRS-IS, 0 RF `direct` local; 2.157 eventos RF sem coordenadas de ambas as pontas, excluídos da renderização normal; 2.957 completos, com 504 tendo ao menos uma ponta histórica >5 km da posição atual da estação e 93 sem marcador atual para alguma ponta. Contagens por evento, não segmentos desenhados.
- **Interpretação:** alguns enlaces podem parecer órfãos porque a linha usa localização histórica e a estação aparece na posição atual. Não tratar inferência APRS-IS como confirmação de RF ouvido no TNC. Este arquivo de PP5AU não substitui a confirmação visual dos enlaces da base de Brasília.
- **Performance:** 743 eventos `sqlite_slow` no diagnóstico; investigar separadamente sem presumir relação causal.
- **Pendências:** simulação do RX KISS, confirmação do modelo do TNC, e correlação dos segmentos visuais/JSON com topologia. Nenhuma correção implementada e validada nesta análise.
## ABERTO — REGRESSÃO P1: enlaces órfãos persistem no mapa real após v1.14.43 (#116, 18/10/2026)

- **Relato de campo:** continuam sendo desenhados enlaces RF órfãos no mapa do PT2VHF APRS Client mesmo após a entrega de v1.14.43/PR #117. A implementação anterior não atingiu o aceite e a [issue #116](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/116) foi reaberta.
- **Regra vigente:** para cada digipeater móvel identificado de forma comprovada, exibir no máximo um enlace RF móvel válido e atual (último contato), usando posição contemporânea e TTL configurável; após a expiração remover visualmente. Não alterar o histórico auditável e preservar enlaces RF fixos legítimos.
- **Diagnóstico pendente:** confrontar cada linha desenhada com exportação JSON/API de topologia, eventos, posição histórica/tracklogs, tipo de camada, filtros, replay e cache do mapa; identificar segmentos legados e casos de classificação incorreta de digis móveis.
- **Testes necessários:** fixture do SQLite/JSON real de Brasília (com dados anonimizados quando cabível), verificar 1h/24h/Completo, refresh, filtros, posições móveis diferentes, timestamps, deduplicação e atualização visual.
- **Status:** **não corrigido; aguardando investigação, reprodução e aceite no banco real**, independentemente dos testes sintéticos aprovados da v1.14.43.
## PENDENTE — Beacon multicanal em todas as conexões ativas (#119, 18/10/2026)

- **Requisito confirmado:** beacons manuais (ícone/cabeçalho), automáticos/periódicos e de qualquer outro gatilho devem disparar **em todos os meios de TX ativos e autorizados ao mesmo tempo: APRS-IS e TNC/RF**, em envios independentes.
- **Manual:** transmitir imediatamente a cada clique, sem cooldown; não esperar o próximo ciclo automático. Proteger apenas contra clique duplicado enquanto uma mesma solicitação está sendo processada.
- **Operação degradada:** se apenas um dos dois transportes estiver habilitado/utilizável, enviar somente por ele; se nenhum, informar claramente. Se um falhar, não bloquear a tentativa no outro; detalhar os resultados e erros por meio.
- **Segurança/protocolo:** TX RF exige autorização já configurada, conexão efetiva, AX.25/KISS e path RF correto (sem TCPIP*); preservar as permissões e evitar echo/loop APRS-IS↔RF. “Aceito pelo TNC” não equivale a “irradiado”.
- **Teste:** matriz TNC+APRS-IS, cada um sozinho, nenhum, falha parcial, dois cliques manuais seguidos, agendamento, simulação KISS COM10 e socket fake, logs/status separados.
- **Rastreamento:** [issue #119](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/119). Apenas especificado; **não implementado ou validado**.
## EM VALIDAÇÃO — v1.14.43: enlaces móveis (#116, 18/10/2026)

- Implementação candidata na branch fix/mobile-latest-link-v1.14.43: somente último enlace RF móvel, TTL configurável (3 h por padrão), cor/espessura próprias e Ver → Enlaces móveis.
- Não confundir com a regra anterior de ocultação geral do #94, agora substituída pelo novo requisito. Contatos históricos permanecem na base e no diagnóstico JSON.
- Critério de aceite pendente: executar suíte CI e inspecionar JSON/SQLite reais da captura de Brasília; somente após validação confirmar ausência dos enlaces órfãos.

## VALIDAÇÃO — v1.14.42 (17/10/2026)

- Atualização portátil Windows com erro de DLL: corrigido isolamento de ambiente PyInstaller e busca de DLLs do helper; teste automatizado incluído. Causa candidata, sem reprodução física do erro relatado. Manter aberto até teste em Windows.
- A lista histórica abaixo inclui requisitos já implementados em v1.14.40/41 (RF temporário, Grid Locator, gauges e apresentação). Não interpretar todos os títulos antigos PENDENTE como situação atual.
- Validação de rádio físico, Web LAN externo, cobertura RF histórica e demais issues abertas não são encerradas por testes sintéticos.

## PENDENTE — Gauges CPU e RAM empilhados no cabeçalho (#109, 16/10/2026)

- **Interface:** na barra superior, apresentar as duas métricas em um bloco vertical estreito, **CPU acima de RAM**, em vez de dois cards lado a lado; reduzir o espaço horizontal consumido sem aumentar desnecessariamente a altura da barra.
- **Manter:** leitura atual CPU (%) e RAM (MB), barras de progresso com escala e cores existentes, alertas de aviso/crítico, tooltip diagnóstico, IDs `headerCpuUsage`/`headerMemoryUsage`, atualização periódica e responsividade. Garantir largura para os valores em ambientes com RAM elevada.
- **Aceite visual:** zoom 100/125/150%, temas claro/escuro, Windows 7/10/11 e navegadores LAN; não deslocar versão, TNC, conexão ou idioma, sem corte/overflow. Alteração CSS isolada; não alterar API nem cálculo das métricas.
- **Rastreamento:** [issue #109](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/109). Ainda não publicado na v1.14.40.

## CAMPO — v1.14.40: atualizador OK; barra do mapa alta; enlaces móveis persistem (16/10/2026)

- **Resultado positivo em uso real:** mantenedor relata que o **Update via app está funcionando bem** nesta nova observação. Registrar sucesso sem extrapolar para todos os sistemas/cenários; as falhas anteriores no Windows 10 (#103) exigem confirmação de que o problema deixou de ocorrer de modo reproduzível antes de fechar a issue.
- **Menu superior/mapa — captura:** segunda barra horizontal ainda ocupa altura e largura excessivas. A busca RF (`Indicativo ↔ Destino RF`) forma um bloco alto de duas linhas com **Limpar** abaixo de Pesquisar/Caminhos possíveis, desalinhado de Histórico, Período, Ver, Camadas e exportações. Requisito final: **linha principal de comandos compacta e alinhada**, campos e botões com alturas consistentes, pesquisa RF de uma linha no desktop, sem botões cair na segunda linha. Considerar **Busca RF recolhível em popover/painel** para janelas estreitas e zoom 125/150%, mantendo acesso completo e estado dos controles, sem aumentar permanentemente a altura da barra nem cortar menus. Validar Windows 7/10/11 e temas/idiomas. Relacionado a #98.
- **Enlaces RF — nova captura de Brasília:** seguem desenhadas linhas amarelas convergentes para a área norte de Brasília, inclusive segmentos que parecem órfãos, na **v1.14.40**. A foto não mostra callsigns de todos os extremos; confirmar pelos eventos/JSON se são repetições móveis ou estações com marcador oculto. Requisito: na topologia principal, renderizar **somente enlaces com origem, destino e intermediários comprovadamente fixos**, inclusive RF sem Internet; contatos que envolveram móvel geram apenas observações RF para o mapa de cobertura, preservando SQLite e evidências. Testar períodos Completo/1h/24h, caminhos selecionados e refresh. Relacionado a #94.
- **Situação técnica:** [PR #105](https://github.com/alexpmr/PT2VHF-APRS-Client/pull/105) já contém correções candidatas para compactação da busca e classificação de digis móveis; [workflow 38840906830](https://github.com/alexpmr/PT2VHF-APRS-Client/actions/runs/38840906830) aprovado, mas PR **ainda aberto e sem merge**. Não estão na v1.14.40 publicada. A exigência adicional de barra ainda menor (eventual recolhimento da pesquisa) precisa de aceite visual. Não declarar bugs resolvidos na versão instalada.

## REGRESSÃO REPRODUZIDA EM 16/10/2026 — Enlaces amarelos órfãos na v1.14.40 (#94)

- **Captura nova, mapa de Brasília:** persistem linhas amarelas radiais e segmentos aparentemente órfãos, convergindo no noroeste do Parque Nacional de Brasília e nas proximidades de Lago Norte, com traçados rumo a Águas Lindas/Ceilândia e outras áreas. Identidade e mobilidade de cada extremidade exigem correlação com o JSON de topologia e o histórico APRS; não classificar automaticamente toda linha sem ícone como enlace espúrio.
- **Regra de aceite:** somente ligações entre entidades comprovadamente fixas no mapa principal, inclusive RF real; ligação com qualquer nó/digi móvel é suprimida visualmente, mas eventos/tracklogs e posições RF contemporâneas são preservados para cobertura observada. Validar Período Completo/1h/24h, rotas em foco, path, posição histórica e filtros de marcadores.
- **Implementação candidata:** [PR #105](https://github.com/alexpmr/PT2VHF-APRS-Client/pull/105), CI [38840906830](https://github.com/alexpmr/PT2VHF-APRS-Client/actions/runs/38840906830) aprovado, mas **sem merge e sem validação no banco real**. A v1.14.40 instalada não contém essa correção. Regressão mantém [issue #94](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/94) aberta.

## IMPLEMENTADO na v1.14.40/41 — Entrada de coordenadas por Grid Locator / Maidenhead (#106, 16/10/2026)

- **Solicitação:** adicionar em **Configuração → Estação → Formato das coordenadas** uma terceira modalidade `Grid Locator (Maidenhead)` ao lado de Decimal e DMS. Issue: [#106](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/106).
- **Entrada:** campo para locator de 4, 6, 8 ou 10 caracteres, normalização de maiúsculas/minúsculas, validação rigorosa conforme segmentos alfanuméricos Maidenhead e mensagem clara em caso de erro. Usar o **centro da célula** para converter o grid em latitude/longitude decimal e informar que a posição é aproximada e qual a resolução espacial do grid; não fingir precisão GPS.
- **Integração:** atualizar os campos `latitude`/`longitude` decimais atualmente persistidos e sincronizar DMS, mapa, beacons APRS e filtros. Também converter decimal → Maidenhead para facilitar conferência do grid correspondente à localização atual; padrão de apresentação de 6 caracteres com seleção de precisão.
- **Sem perda silenciosa de precisão:** entrar ou sair do modo Grid não modifica coordenadas de maior precisão já registradas. Exigir ação explícita **Usar estas coordenadas** para substituir a posição da estação pela localização aproximada do centro de uma célula; mudança do grid inválida ou incompleta não deve corromper os campos originais.
- **Compatibilidade e testes:** persistir preferência `pt2vhf_coordinate_mode`, respeitar geolocalização automática e os campos obrigatórios; verificar limites geográficos, hemisférios, 4/6/8/10 caracteres, ida/volta, formatos inválidos, valores de centro/precisão, preservação ao reiniciar, i18n e Windows 7/10/11/Web LAN. Nenhum campo independente de localização deve divergir da latitude/longitude canônica.
- **Status:** registrado em backlog e issue #106. **Não implementado nem validado na v1.14.40.**

## PENDENTE — Tracklogs como evidência georreferenciada de cobertura RF observada (15/10/2026, #94)

- **Proposta:** aproveitar os pontos de tracklog APRS, inclusive de estações/digipeaters móveis, como candidatos a amostras na camada separada **Ver → Cobertura RF observada**. **Tracklog por si só comprova localização/trajetória, não recepção RF**: um ponto só entra como cobertura quando sua estação+SSID, timestamp e coordenada contemporânea podem ser associados a um pacote efetivamente ouvido/repetido por RF, com proveniência auditável.
- **Motor de correlação:** cruzar `tracks` (indicativo/SSID, latitude, longitude, instante, path/raw, velocidade/curso e eventual qualidade do sinal), `packets` (timestamp, raw, medium) e `topology_events`/caminhos APRS reais (RF direto via TNC, digipeater usado, iGate e classificações). Usar janela temporal curta e explícita/tolerância configurável, identificador ou fingerprint do pacote quando disponível, validação de posições e consistência espacial; **não ligar o ponto ao digi mais próximo ou a um evento sem correspondência**. Nunca substituir GPS histórico pelo último conhecido.
- **Níveis de evidência:** (A) **RF observado diretamente** pelo TNC/interface local, com posição da estação emissora quando válida; (B) **RF inferido/relatado** de path efetivamente usado e/ou ingresso local qAR/qAO, identificados sem afirmá-los como recepção direta da própria estação; (C) **sem comprovação RF** (APRS-IS puro, pacote injetado por Internet/Starlink, importação GPS ou tracklog sem RX verificável), **não entra como cobertura RF confirmada**. Manter filtro de exibição por classe e descrição da proveniência em popup.
- **Significado geográfico:** se a estação móvel **transmitiu** e houve confirmação de RX RF, sua posição histórica mostra um **ponto de acesso/alcance observado à rede** naquele instante; se a coordenada pertence ao **digi receptor móvel**, representa somente **atividade RF observada no local do digi**, não o local do transmissor nem um raio de cobertura. Distinguir explicitamente as duas categorias.
- **Representação:** pontos individuais e células/heatmap de amostras **observadas**, ajustáveis por banda/fonte/período, sem interpolar área não medida; não gerar linhas entre posições do mesmo digi móvel nem enlaces móveis no mapa de topologia principal. Metadados por amostra: origem, indicativo+SSID emissor/repetidor, instante, coordenadas e precisão, RX/TNC/path/qAR, meio real, classe de confiança, contagem primeira/última observação, taxa de duplicidade. Não interpretar densidade de tracklogs sozinha como intensidade de sinal ou porcentagem de cobertura.
- **Persistência, escala e testes:** preservar `tracks`, `packets` e `topology_events` sem exclusão; deduplicar beacons/pacotes repetidos pela rede e agregar células/tempo com consultas eficientes, respeitando retenção e filtros (1h/12h/24h/7d/Completo). Testar: tracklog apenas APRS-IS → zero cobertura RF; tracklog + pacote RF contemporâneo → ponto confirmado; path qAR/qAO → ponto inferido; digi móvel em origem/destino; duplicatas; GPS espúrio; eventos fora da janela temporal; histórico sem recepção; mistura RF/Internet; não reintroduzir linhas móveis (#94). Validar com histórico real de Brasília antes de aprovar.
- **Status:** requisito de produto incluído no backlog e ligado à [issue #94](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/94); **não implementado nem testado como recurso novo nesta etapa**.

## REGRESSÃO REPRODUZIDA NA v1.14.40 — RF de digipeaters móveis continua desenhado no mapa (15/10/2026)

- **Nova captura de campo (15/10/2026, v1.14.40):** mapa de Brasília/DF mostra várias linhas amarelas convergindo na região de Lago Norte/norte de Brasília e prolongando-se em direção a Águas Lindas de Goiás e Ceilândia, entre outras áreas. O operador confirma que enlaces de digipeaters móveis deslocados seguem visíveis. A captura, isoladamente, não identifica os indicativos/SSID dos extremos; validar com popup/exportação topológica para associar cada linha ao histórico correto.
- **Causa técnica provável no código da .40:** `topology_map.py::moving_rf_repeaters()` usa somente `target`/`target_lat`/`target_lon` dos eventos de espécie `rf`, exige dois grupos com pelo menos duas amostras e separados 25 km. `/api/topology` usa janela de tempo e recorte `MAP_EVENT_SCAN_LIMIT=30000`, então mobilidade pode não ser reconhecida em períodos menores ou recortes incompletos. `app.js::loadTopology()` acrescenta arestas de `rfRouteAnalysis` que não constam de `/api/topology` e desenha essas linhas sem reaplicar um filtro de imobilidade comprovada. O filtro das arestas `igate` também não exige extremidades fixas. Estes são riscos confirmados em código, não a prova definitiva da identidade da linha da captura.
- **Regra obrigatória de desenho:** o mapa geral só deve apresentar linhas para caminhos com origem, destino e intermediários conhecidos classificados como **fixos**. Qualquer móvel ou condição indeterminada impede a linha; isso vale para enlace RF legítimo e Internet/iGate, mantendo o estilo de RF fixo sólido. Se a evidência envolveu digi móvel, apresentar apenas pontos/células historicamente observados na camada de cobertura RF, respeitando comprovação versus inferência e sem transformar a posição de um digi em polígono de alcance.
- **Teste de aceitação para próxima correção:** reproduzir a cena de Brasília com banco real, listar cada linha suprimida e motivo por indicativo/SSID; zerar segmentos ligados a estações móveis ou caminhos com digi móvel, sem apagar pacotes nem esconder RF entre fixas. Verificar a situação com e sem rota selecionada, filtros 1 h/24 h/Completo, após refresh, e com GPS histórico falso/ausente; registrar as amostras de RF móvel disponíveis para cobertura.
- **Estado:** reprodução relatada na **v1.14.40**; issue [#94](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/94) permanece aberta. **Nenhuma correção de código/instalador foi implementada para esta reprodução.**

## PENDENTE — Regra definitiva: somente entidades fixas geram linhas no mapa; RF móvel vira cobertura observada (#94, 15/10/2026)

- **Novo requisito e captura (15/10):** ainda aparecem linhas RF originadas por digipeaters móveis ou realizadas por intermédio deles. **No mapa principal, desenhar enlaces apenas entre entidades comprovadamente fixas, inclusive os exclusivamente RF.** Contato RF verdadeiro envolvendo um digi móvel não autoriza reta no mapa; convertê-lo em evidência georreferenciada da camada Cobertura RF observada, sem apagar os pacotes.
- **Regra de visibilidade:** ambas as extremidades devem ser fixas e também os repetidores/intermediários conhecidos que fundamentam o enlace. Se qualquer integrante do caminho observado for móvel, suprimir a linha — mesmo se os dois endpoints aparentarem ser fixos. Status fixo/móvel/indeterminado; se fixidez não for comprovada, não representar enlace como seguramente fixo. Permitir cadastro fixo explícito e auditável, sem presumir fixidez porque o GPS não mudou.
- **Classificação robusta:** avaliar indicativo+SSID, históricos RF/tracklogs e coordenadas contemporâneas tanto na origem quanto no destino, inclusive em caminhos multissalto; detectar movimento fora da janela atual de exibição, sem depender exclusivamente de dois grupos com múltiplas amostras, última posição ou corte dos eventos. Rejeitar GPS espúrio; SSID sozinho não prova mobilidade.
- **Aplicar o filtro a todas as fontes de desenho:** backend /api/topology e topology_map.py, app.js::loadTopology(), overlays e rotas selecionadas, RF confirmado/inferido e demais tipos de enlace (Internet/iGate em sua camada), para impedir reaparecimento por filtro de tempo, atualização, zoom, seleção de rota ou refresh.
- **Cobertura RF:** preservar a evidência RF legítima no SQLite (pacote/path, estação+digi, data/hora, posição histórica válida, classificação RF confirmado/inferido e origem), representada por pontos/células em Ver → Cobertura RF observada, sem linhas móveis. Posição do digi representa o ponto de atividade RF do digi, não cobertura contínua de toda uma região. APRS-IS puro não constitui comprovação RF. Registrar motivo de supressão (mobile_endpoint, mobile_path, fixed_unknown, geometry_unknown) e contadores auditáveis.
- **Aceite:** na amostra ilustrada e no histórico PT2AP/PT2AP-9 Sul → Uberaba → Brasília, zero linhas associadas a digis móveis, zero pontas órfãs e zero trajetos entre posições atuais e antigas; manter linhas sólidas e na cor configurada para RF de entidades fixas mesmo sem Internet. Exercitar Completo/24h/1h, source/target invertidos, path multissalto, posição GPS inválida e classificação temporal. Não apagar os registros nem inflar a análise por rotas não simultâneas.
- **Estado:** regressão prioritária vinculada à issue #94; **registrado, não implementado/validado na v1.14.40**.

## PENDENTE — Menu Histórico contextual, Apresentação alternável e organização da barra (#98, 15/10/2026)

- **Novo relato com captura na v1.14.39:** a barra/menu continua desformatada. **OPÇÃO** deve sair da barra principal e aparecer somente dentro do menu/painel **Histórico** enquanto estiver aberto; ocultar ao fechar e não perder estado dos comandos de replay. Não há controle com texto literal OPÇÃO no HTML estático; identificar o grupo equivalente na execução antes de alterá-lo.
- **Mover Velocidade (0,5×/1×/2×/5×)** exclusivamente da barra para **Configuração → Mapa**; preservar preferência `pt2vhf_traffic_speed`, animação e sincronismo com o painel de Histórico. **Tipo de mapa** também deve sair da barra e continuar no campo existente `map_type` da configuração, sem duplicação ou perda de seleção/fallback OSM.
- **Botão Apresentação toggle:** primeiro clique entra em modo apresentação e fullscreen; **segundo clique no mesmo botão restaura modo normal**, sem Esc. Manter o botão disponível durante apresentação, com estado `aria-pressed`, ação de sair, rótulo acessível, sincronismo com `fullscreenchange` e atualização de tamanho Leaflet. Esc deve continuar funcionando. **Causa confirmada:** `v190.js::installPresentationMode()` configura atualmente o clique principal apenas para entrar, com saída por botão secundário ou Esc.
- **UI:** ordem/layout compacto e responsivo (Histórico, Período, busca RF, Ver, Camadas, Exportações, Apresentação), menus sem cortes, labels alinhados e sem sobreposição em janela reduzida, zoom 125–150%, Windows 7/10/11, claro/escuro e idiomas.
- **Rastreamento:** [issue #98](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/98). **Requisito complementado; não implementado nem validado na v1.14.39.**

## PENDENTE — Cabeçalho Web: IP:porta como botão e ativação LAN antes de abrir navegador (#99, 15/10/2026)

- **Captura de cabeçalho:** atualmente mostra `Web em uso: 192.168.10.61:8080` como etiqueta. Exibir **somente um botão `IP:porta`** (sem “Web em uso”/“Web LAN”/“Web local”, sem protocolo), mantendo sinais de estado e acessibilidade por tooltip/título.
- **Ação:** ao clicar no IP, abrir navegador padrão externo com a URL completa e atual do listener. **Se Web LAN estiver desativado, ativar e esperar servidor no IP LAN responder antes de abrir**. Evitar abrir URL inativa; porta/IP devem vir do runtime, inclusive após fallback ou mudança de interface. Não navegar para um destino arbitrário fornecido pelo frontend.
- **Implementação:** em Windows, o servidor inicia em `127.0.0.1` ou `0.0.0.0` conforme `web_lan_enabled` (`windows_app.py`); `/api/config` marca `restart_required` quando a opção muda. A ativação precisa reconfigurar/reiniciar listener/instância com segurança, preservando TNC/APRS, e checar health antes da abertura. Falhas de firewall/porta devem mostrar erro, não falsa disponibilidade. Em navegador LAN já remoto, abrir nova aba sem tentar reinício indevido da máquina remota.
- **Segurança:** ativação LAN somente por pedido explícito, tratamento de redes públicas/firewall, proteção de endpoints administrativos, feedback 'ativando/abrindo/erro' e evitar múltiplas ativações por duplo clique. Preservar `open_browser_on_start=0`; o clique manual não deve mudar essa preferência.
- **Rastreamento:** [issue #99](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/99), relacionada a #78/#79/#80. **Registrada; não implementada nem validada na v1.14.39.**

## PENDENTE — Formatação do menu do mapa e transferência de Velocidade/Tipo de mapa para Configuração (issue #98, 15/10/2026)

- **Relato na v1.14.39:** o menu/barra de controles do mapa continua com **formatação incorreta**; usuário solicita remover **Velocidade** e **Tipo de mapa** da barra principal e colocá-los em **Configuração → Mapa**.
- **Diagnóstico:** `templates/index.html` possui `#topologySpeed` e `#mapTypeQuick` em `#mapContextBar`. **Tipo de mapa já está presente na seção Configuração → Mapa**, como `select[name="map_type"]`: reutilizar, não duplicar. O novo campo **Velocidade da animação APRS** deve oferecer 0,5×, 1×, 2× e 5× (padrão 1×).
- **Persistência:** conservar `pt2vhf_traffic_speed`, temporizadores, animação de pacotes e sincronismo com o controle da área de replay (`#trafficSpeed`). Conservar `map_type`, provedor selecionado, sincronismo com formulário, fallback OSM em erro de tiles, preferências do usuário e suporte à migração sem perda.
- **Formatação/UX:** barra principal mais limpa mantendo Histórico, Período, busca/rotas RF, Ver, Camadas e Exportar KML/JSON; corrigir rótulos cortados, sobreposição de botões/dropdowns, espaçamentos, alturas e quebras responsivas. Checar menu sem scroll horizontal forçado ou campos fora da área visível, inclusive janela não maximizada, escala 125/150%, 1366×768, Full HD, temas e idiomas.
- **Aceite:** Velocidade e Tipo de mapa **não aparecem mais** na barra, estão em Configuração → Mapa e funcionam após salvar/reiniciar; menu responsivo sem perda de comandos; i18n e testes DOM/JS/visuais. Relacionado ao histórico de correções da barra responsiva v1.14.10.
- **Rastreamento:** [issue #98](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/98). **Registrado, não implementado na v1.14.39.**

## PENDENTE — Regressão v1.14.39: enlaces RF órfãos de digipeaters móveis ainda aparecem (#94, 15/10/2026)

- **Evidência visual enviada pelo mantenedor:** no mapa do noroeste do Paraná, entre Maringá, Mandaguaçu e Faxinal, diversas **linhas amarelas convergem para repetidores e terminam em posições sem estação correspondente visível**. A nova versão v1.14.39 **não suprimiu todos os enlaces gerados por digis móveis**. Importante: ausência de ícone na extremidade, isoladamente, pode decorrer dos filtros de marcadores; identificar se a geometria histórica é válida antes de atribuir causa.
- **Análise do código:** `topology_map.moving_rf_repeaters()` só detecta deslocamento com **dois agrupamentos geográficos de pelo menos duas observações cada**, afastados 25 km; recortes de 30.000 `topology_events`, repetidores no campo `source`, trilhas independentes (`tracks`) e coordenadas pontuais fora dos buckets ficam sem proteção. `app.js::loadTopology()` também injeta rotas da análise RF e pode contornar filtros exclusivos da topologia geral.
- **Tratamento proposto:** classificador temporal de mobilidade por callsign+SSID, usando posições históricas RF e tracklogs com validação contra GPS espúrio; suprimir *somente o desenho* das arestas RF cujo repetidor foi comprovadamente móvel, em todos os caminhos de renderização. Sem comprovação de geometria, **não ligar pontos com linhas**; registrar a razão de supressão no diagnóstico. Preservar `topology_events`, `topology_edges`, `tracks` e `packets` para a camada de **Cobertura RF observada**; RF de repetidores fixos mantém linha contínua configurada.
- **Aceite real:** zerar as “aranhas” e segmentos órfãos do exemplo enviado sem esconder pares RF fixos comprovados; testar com período Completo e janelas menores, posição de repeater invertida source/target, 1 ponto por região com trilha corroborante, GPS falso e análise de rota em foco. Medir número de arestas suprimidas e preservadas por causa.
- **Rastreamento:** [issue #94](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/94), aberta, prioridade alta. **Regression confirmada após publicação de v1.14.39; não resolvida e não testada em nova release.**

## Implementado em código para v1.14.39 — aguarda CI e testes reais (#93, #94, #95, #96)

- **#93 Recordes RF:** job assíncrono sem prazo fixo de 45 s; cancelamento X integrado ao backend, checkpoints de cancelamento durante indexação e expansão de rotas, tempo decorrido e ETA por fase com amostras suficientes. **A medição real em banco grande e tempo de cancelamento durante montagem inicial do grafo ainda não foram validados.** Não considerar resolvido por compilação apenas.
- **#94 Repetidores móveis e cobertura:** suprimiu linhas RF de repetidores com mobilidade confirmada por histórico consistente (ao menos duas observações por região e separação de 25 km); a camada Ver → Cobertura RF observada agrega pontos de RF direto/inferido em células históricas. **Validar com PT2AP real e falsas posições GPS; não há polígonos de cobertura previstos.**
- **#95 Contagens Estatísticas:** resumo independente do job RF por categoria, respeitando período/retidos. **Conferir contagens reais em banco com retenção e diferenças entre estações atuais e histórico de pacotes.**
- **#96 Retenção:** categoria Pacotes já existia; adicionados botões Limpar tudo com prévia e confirmação textual, limpeza em lotes e bloqueio de TX pendente. **Executar testes de integridade SQLite/backups e LAN antes de declarar concluído.**
- **Release:** código pronto para testes; publicação oficial e aceites físicos ainda pendentes.

## PENDENTE — Estatísticas: quantitativos de mensagens, estações, objetos e demais categorias (issue #95, 14/10/2026)

- **Pedido do mantenedor:** adicionar à aba **Estatísticas** um resumo numérico dos dados armazenados/observados: **quantidade de mensagens, estações, objetos APRS etc.** A página hoje exibe período, enlaces, pacotes e eventos, mas falta uma visão clara de contagens por categoria.
- **Bloco proposto “Quantidades por categoria”:** cartões para **estações únicas por indicativo/SSID; mensagens APRS individuais (RX/TX), boletins e grupos; objetos APRS (AIS/radiossondas quando possível distinguir com segurança); pacotes; pontos de tracklog; digipeaters/iGates únicos; enlaces RF e Internet/iGate; eventos de topologia**. Explicitar unidade, contagem distinta e fontes para evitar duplicidades ou misturar eventos com entidades.
- **Tempo/escopo:** respeitar o seletor existente (1 h/12 h/24 h/7 d/Completo e demais opções), diferenciar registros **no período** dos **armazenados no banco** e reconhecer a retenção já aplicada. Em “Completo”, exibir todo histórico **ainda retido**; nunca alegar dados que já foram removidos.
- **Desempenho e resiliência:** carregar cartões por consulta leve/agregada com cache e índices, **independentemente** do processamento dos Recordes RF (#93). Falha ou timeout de qualquer consulta não vira zero falso; conservar último valor válido identificado como desatualizado ou mostrar “Indisponível”. Atualizar após recepção, retenção/limpeza e uso do botão Atualizar estatísticas.
- **Aceite:** números conferidos com registros SQLite, sem contar vários pacotes da mesma estação como várias estações; sem dupla contagem de RX/TX, boletins e grupos; coerência com a exclusão seletiva por categoria (#96); UI responsiva com temas e idiomas suportados.
- **Rastreamento:** [issue #95](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/95). **Registrado; não implementado na v1.14.38.**

## PENDENTE — Configuração: Pacotes e Limpar tudo por categoria do banco (issue #96, 14/10/2026)

- **Solicitação do mantenedor:** em **Configurações → Retenção e tamanho do banco**, deixar **Pacotes** explícito para configurar a retenção e adicionar **“Limpar tudo” ao lado de cada categoria** (Estações, Tracklogs, Mensagens etc.) para excluir toda a categoria do SQLite.
- **Diagnóstico:** **Pacotes já existe** no backend como `retention.DEFAULT_DAYS["packets"] = 30` e em `app.js::retentionCategories` como “Pacotes recebidos”. Corrigir visibilidade/descrição, **não duplicar tabela/política**. `/api/retention/apply` remove apenas **dados expirados** e não implementa a nova função “Limpar tudo”.
- **UI:** linha por categoria com nome, seletor de prazo, contagem e botão **Limpar tudo**; confirmação clara com nome da categoria, registros estimados, impacto/irreversibilidade e sugestão de backup. **Cancelar não altera nada**. Preservar políticas de retenção, inclusive Permanente, mesmo após limpeza manual expressamente confirmada.
- **Segurança e banco:** allowlist estrita por categoria no backend, proteção de operação destrutiva e acesso Web LAN, prevenção de duplo clique, limpeza transacional em lotes para não travar SQLite/recepção APRS, relatório de quantidade removida, tratamento de falhas e atualização de caches/estatísticas.
- **Integridade referencial:** limpar **Estações/Digis/iGates** sem apagar enlaces permanentes; **Tracklogs** sem apagar categorias independentes; **Mensagens/Boletins/Grupos** separadamente e sem destruir inadvertidamente TX/ACK pendente; **Pacotes** sem apagar mensagens/enlaces/eventos de topologia já persistidos; **Enlaces RF/Internet**, **Objetos**, **Log APRS** e **Eventos de topologia** somente nos respectivos conjuntos. Novos dados recebidos podem repovoar as categorias.
- **Testes de aceite:** limpeza por categoria com dados mistos, contagens corretas antes/depois (#95), preservação de outros dados e de preferências, concorrência com ingestão/APRS e rotas RF, confirmação negativa sem exclusão, progressão em banco grande, traduções e Windows 7/10/11.
- **Rastreamento:** [issue #96](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/96). **Registrado; não implementado na v1.14.38.**

## PENDENTE — Digipeaters móveis: remover linhas RF espúrias e criar camada Cobertura RF observada (issue #94, 14/10/2026)

- **Relato real na v1.14.38:** enlaces de estações móveis/repetidoras ficaram ruins; aparecem **várias linhas ligando um digi a lugar nenhum**. Em novo teste, o mantenedor pediu explicitamente: **“Nos casos das estações que repetem e se deslocaram, não deixe enlace na tela mas aproveite esta informação para ser usado em um mapa de cobertura, para mostrar onde essas estações estiveram ao alcance de uma rede RF.”**
- **Nova decisão de produto — prevalece sobre a renderização histórica solicitada anteriormente na #85:** quando **digipeater, iGate ou estação repetidora comprovadamente móvel** mudou de posição, **não renderizar no mapa geral os enlaces RF históricos associados à repetição móvel**, nem linhas para geometrias ausentes. Preservar todas as evidências RF locais verdadeiras, timestamps, paths, SSIDs e posições históricas no banco; ocultação apenas de representação cartográfica, **não exclusão do dado**.
- **Preservar topologia fixa:** enlaces RF de pares com geometria confiável e não envolvidos em repetidor móvel continuam com **linha sólida e cor configurada** (#91); enlaces Internet/iGate conservam seu próprio traçado. Identificar movimento por histórico temporal/posições, nunca por SSID ou callsign isolado. Sem posição histórica válida, classificar `geometria indeterminada`, jamais esticar até último GPS.
- **Nova camada Ver → Cobertura RF observada:** plotar **pontos de posição GPS contemporânea** ou **células/heatmap de densidade** em que houve **recepção/repetição comprovada por RF** ao longo do deslocamento. Se a posição for do *digi móvel* em vez da *estação móvel ouvida*, indicar claramente **ponto em que o digi tinha atividade/contato RF**, não confirmar todo o entorno como coberto. Nada de retas/“aranhas” no mapa de cobertura.
- **Evidência e honestidade cartográfica:** TNC RF direto, path digipeater realmente usado, `qAR/qAO` (inferência RF local) e APRS-IS puro devem ser separados. **APRS-IS/Starlink puro nunca prova cobertura RF**. A camada representa **amostras de cobertura observada**, não predição contínua nem garantia de comunicação nos intervalos sem medições; inferidas devem ter sinalização/filtro próprios.
- **Campos:** indicativo e SSID, digi/rede que ouviu ou repetiu, timestamp, coordenadas contemporâneas/precisão, evidência RF e origem do pacote, primeira/última observação, contagem por célula. Respeitar filtros de período (1 h/12 h/24 h/7 d/Completo), estação, digipeater e evidência; evitar duplicatas e processar milhares de eventos com agrupamento espacial/temporal.
- **Aceite principal:** PT2AP/PT2AP-9 Sul → Uberaba → Brasília **não deixa linhas móveis sem destino na topologia**, inclusive em período Completo; as observações historicamente válidas aparecem como **pontos/células de RF observado**, sem pontes de VHF interestaduais fictícias; dados continuam disponíveis para diagnóstico, exportação e análise auditável de rotas/Recordes. Testar banco real e não inflar ranking por ligações cartograficamente ocultas.
- **Prioridade:** alta, ligada à [#85](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/85) (nova orientação de aceite), à [#86](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/86) (rotas plausíveis) e à [#93](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/93) (custo computacional no período Completo).
- **Rastreamento:** [issue #94](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/94). **Backlog registrado, não implementado e não validado nesta versão.**

## PENDENTE — Recordes RF observados: cálculo excede orçamento interno de 45 s (issue #93, 14/10/2026)

- **Relato de campo na v1.14.38:** em **Estatísticas → Recordes RF observados**, o aplicativo informa **“Cálculo de Recordes RF excedeu o orçamento interno de tempo.”** Não equivale a ausência de enlaces nem a um ranking RF legitimamente vazio. **Período confirmado pelo operador em 14/10/2026: Completo (`hours=0`)**. Não há confirmação de reprodução em 24 h ou 7 dias; manter esses períodos como testes comparativos.
- **Causa imediata verificada:** `pt2vhf_aprs/spacetime_topology.py` define `RF_RECORD_DEFAULT_DEADLINE_SECONDS = 45.0` e lança `TimeoutError` ao atingir o prazo durante a busca por origens. `web.py` também define `deadline_seconds=45.0` para os jobs e endpoint síncrono. O custo inclui montagem do grafo, indexação de eventos e expansão por origem, antes de consolidar top 10. O teste do deadline ocorre **entre origens**; grandes origens podem atrasar progresso e cancelamento.
- **Melhoria prioritária:** instrumentar tempos e contagens por fase/origem; otimizar expansões e representantes RF em bases densas; estudar processamento incremental/checkpoint com retomada para não descartar todo esforço ao atingir orçamento. Não corrigir apenas elevando limite de 45 segundos nem reduzindo silenciosamente hops/histórico.
- **UX/resiliência:** cache/single-flight por período sem bloquear SQLite; preservar ranking anterior válido (rotulado como desatualizado); indicar progresso e erro específico; retry funcional sem tempestade de jobs; eventual ranking parcial deve ser rotulado **não exaustivo** e não pode se passar por recorde global confirmado.
- **Integridade RF:** preservar geometrias históricas PT2AP, evidências de RF real versus APRS-IS, compatibilidade temporal e a separação entre caminho observado e hipótese; não inventar nem eliminar enlaces para acelerar cálculo. Não confundir com alteração da ordenação de ranking pendente na issue #86.
- **Aceite:** cálculo correto e responsivo em 24 h, 7 d e **Completo**, inclusive com >35 mil eventos, sem timeout recorrente; outras estatísticas utilizáveis; resultados anteriores preservados durante falhas; testes reais da estação e regressões automatizadas.
- **Rastreamento:** [issue #93](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/93). **Aberto; correção ainda não implementada.**

### Complemento de 14/10/2026 — X para cancelar, tempo estimado e sem abortar a 4%

- **Nova reprodução confirmada:** no período **Completo** (`hours=0`), o indicador chegou a **aproximadamente 4%** e o job foi interrompido com o erro de **orçamento interno excedido**. O usuário solicita que um cálculo que **continua progredindo não seja abortado só porque passou de 45 segundos**; deverá prosseguir até concluir, receber cancelamento explícito ou encontrar uma falha real diagnosticada.
- **UX:** adicionar botão **X — Cancelar processamento e fechar** ao indicador/janela de “Recalculando Recordes RF”; ao clicar, enviar `DELETE /api/topology/rf-records/jobs/<job_id>`, pedir cancelamento cooperativo real, parar polling e retirar o overlay/spinner. Se clicar antes de existir `job_id`, deferir o cancelamento até obter o identificador. Manter ranking anterior válido; não fechar apenas a tela deixando a thread calcular.
- **Tempo estimado:** mostrar **percentual existente + tempo decorrido + previsão aproximada de tempo restante (ETA)**; quando insuficiente ou instável, mostrar “Calculando estimativa…”/“Tempo restante indeterminado”. Estimar por etapa e vazão efetiva com suavização, sem extrapolar ingenuamente `4%` para o tempo total. Atualizar a previsão durante o processamento.
- **Backend:** substituir deadline total fixo de 45 s do **job assíncrono** por execução prolongável enquanto o worker tem progresso/heartbeat de atividade real; manter controle de interrupção, recursos e detecção honesta de travamentos. Separar timeout de requisição HTTP do tempo total do cálculo; não criar execução infinita sem diagnóstico. Inserir `cancel_check` dentro das expansões e etapas custosas, não somente entre origens. `percent=100` apenas quando ranking estiver concluído. Preservar single-flight, isolamento por período e rejeitar respostas tardias de jobs cancelados.
- **Testar:** histórico grande em Completo que excede 45 s mas evolui e conclui; cancelamento manual com X durante indexação (~0–5%) e busca de rotas; ETA inicial/sob carga; reabrir Estatísticas; manter outros painéis responsivos; nenhuma perda de pacotes RF ou ranking salvo. Relacionado à [issue #93](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/93). **Ainda não implementado.**


- **Complemento funcional de 14/10:** durante Estatísticas, se o popup de Recordes RF observar **progresso real no backend**, mesmo com percentual momentaneamente estável, **não interromper o job por timeout fixo**. Distinguir contadores efetivamente processados de heartbeat ocioso, reiniciar apenas um watchdog de inatividade real, manter polling e ETA; cancelamento pelo X continua imediato. Testar execução por vários minutos com trabalho verdadeiro sem abortar aos 45 s.

## Implementado e validado pelo mantenedor na v1.14.38 — issues #90 e #91 encerradas

- **#91 — RF x Internet:** mapa passa a desenhar todos os enlaces RF exibidos com linha **contínua**, cor e espessura das Configurações. Internet/iGate permanece tracejada. Classificações RF `inferred`, `legacy` e `direct` não mudam e continuam identificadas no popup; bloqueios de salto inferido >250 km e geometria histórica móvel (PT2AP) são preservados. Testes automatizados adicionados. **Mantenedor confirmou em 14/10/2026: “Enlaces na configuração indicada.” Issue #91 encerrada com aceite visual.**
- **#90 — atualizador Windows 10:** consulta GitHub passa a admitir timeout maior, retry controlado, fallback HTTPS via Windows PowerShell/.NET com TLS e certificados nativos (sem desativar verificação) e confirmação limitada de tag pela página oficial quando a API não estiver acessível. Resposta da API e UI agora mostram classe do erro, diagnóstico e última checagem válida em memória quando existir; **Mantenedor confirmou em 14/10/2026: “Cheque de versão funcionando bem, agora.” Issue #90 encerrada com aceite funcional relatado.** Em versões antigas que não conseguem localizar a nova release, primeiro update pode requerer **instalação manual**, preservando dados.
- **Limites:** aceites reportados contemplam funcionamento da checagem de versão e aparência dos enlaces; não comprovam todos os cenários TLS, todas as plataformas nem as questões históricas #83 Portable, #85 geometria móvel e #86 alternância do ranking. Não declarar backlog integralmente concluído.

## RESOLVIDO — Regressão do mapa: enlaces RF na cor configurada e linha contínua (issue #91, 14/10/2026)

- **Relato:** nas versões recentes, os enlaces RF passaram a ser desenhados com tracejado/pontilhado e em cinza em vez da cor escolhida pelo usuário. Pedido explícito do mantenedor: **todos os enlaces RF exibidos devem ser contínuos e seguir a cor/largura definida em Configurações**; apenas Internet/APRS-IS conserva tracejado e sua cor específica.
- **Esclarecimento 14/10:** os enlaces RF estão sendo visualmente apresentados **como se fossem iGate/Internet**. Não usar classe de evidência `inferred` ou `legacy` para atribuir tracejado. O estilo deve depender de `edge.kind` (RF sólido versus iGate tracejado); RF e Internet podem coexistir no mesmo par sem confundir evidências.
- **Causa verificada no código:** `static/js/app.js::loadTopology()` (mudança da v1.14.36 mantida na v1.14.37) aplica `'#94a3b8'` e `style.dashArray='5 7'` para RF inferido, mais `'2 5'` para legado. A v1.14.35 ainda aplicava a cor RF configurada, embora já pontilhasse certos inferidos.
- **Não alterar a semântica:** manter classificação `RF recebido no TNC / RF inferido do path / legado` em popups, tooltips, registros e exportações; **cor e linha contínua não comprovam RF direto**.
- **Não regredir a topologia:** preservar filtros de geometria histórica, prevenção de links artificiais (PT2AP móvel/Starlink) e exclusão de hops longos inferidos sem comprovação no mapa geral.
- **Aceite:** quaisquer enlaces RF apresentados no mapa/foco de rota são contínuos na cor configurada; iGate/Internet é tracejado com cor própria; aplicar alteração de configuração sem reiniciar; testar temas, evidências mistas e vários períodos.
- **Rastreamento:** [issue #91](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/91). **Corrigido no código da v1.14.38 e encerrado após confirmação visual do mantenedor em 14/10/2026.**

## RESOLVIDO — Atualizador: “verificação indisponível” nas duas últimas versões (issue #90, 14/10/2026)

- **Relato:** últimas duas versões testadas não conseguem consultar a última versão publicada e mostram **“verificação indisponível”**. Versionamento a confirmar pelo diagnóstico; GitHub já possui release v1.14.37 publicada.
- **Novo diagnóstico diferencial 14/10:** em **Windows 10 recém-instalado**, o cliente não verifica atualizações; **outro computador com Windows 11** verifica a versão e atualiza normalmente. Investigar instalação/ambiente Win10 (certificados TLS/CA raiz, hora/data, atualizações Windows, IPv4/IPv6, proxy/firewall, DNS, timeout, permissões e pacote PyInstaller), **sem afirmar causa antes de obter erro real**. Confirmar versão, arquitetura, tipo de pacote e equivalência da rede.
- **NTP confirmado 14/10:** relógio do Windows 10 conferido por NTP e correto, porém a mensagem **“verificação indisponível” permanece**. Despriorizar data/hora como causa observada. Próximos testes: resposta e erro do `/api/update-status?force=1`, acesso direto à API no mesmo PC, cadeia TLS/CA, proxy, DNS e timeout; não desligar validação SSL.
- **Ambiente confirmado 14/10:** instalação limpa do **Windows 10 totalmente atualizado**, **sem antivírus de terceiros** e hora/NTP correta. A falha persiste. Despriorizar hora incorreta, falta de atualizações do sistema e bloqueio por antivírus adicional; Microsoft Defender/Firewall nativo pode continuar habilitado. **Falta obter `status/error` do endpoint local** e comparar com o acesso HTTPS à API GitHub; a causa não está confirmada.
- **Diagnóstico reprodutível:** comparar no mesmo ambiente o acesso ao endpoint público de Releases pelo navegador e ao JSON local `/api/update-status?force=1`; capturar `status`, `error`, tipo de exceção e HTTP code. Não contornar falhas TLS desativando verificação de certificados.
- **Aceite de campo prioritário:** Windows 10 recém-instalado deve localizar release e permitir atualização compatível; Windows 11 deve continuar funcionando, com regressões de instalação Setup/Portable.
- **Causa em investigação:** backend consulta apenas `api.github.com/.../releases/latest` com timeout de 5 segundos; frontend faz timeout em 8 segundos e mostra falha genérica.
- **Ações previstas:** diagnosticar erros reais (DNS, TLS, proxy/firewall, HTTP 403/rate limit/404, timeout/JSON); retry/backoff controlado, último status comprovado com data, diferenciação entre falha de consulta e pacote ausente, reconsulta manual e testes Win7/Win10/Win11.
- **Aceite:** estado correto da release quando disponível e erro específico e recuperável quando indisponível, nunca afirmar que a versão está atualizada sem confirmação válida.
- **Rastreamento:** [issue #90](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/90). **Corrigido no código da v1.14.38 e encerrado após confirmação funcional do mantenedor em 14/10/2026.**

## Corrigido no código da v1.14.36 — classificação RF e filtro APRS-IS

- RF inferido pelo path é representado em cinza tracejado; trechos inferidos acima de 250 km ficam fora do mapa geral, preservados na análise selecionada e no histórico. Distância não é prova de impossibilidade física.
- A agregação de eventos RF históricos usa todas as evidências disponíveis, não apenas o primeiro evento.
- O novo filtro APRS-IS padrão para bases novas é `r/4000` com centro nas coordenadas da estação, sem alterar filtros personalizados existentes.
- A interface explica a restrição HTTPS para geolocalização automática pela LAN.
- A validação definitiva ainda exige dados RF reais e checagem de algumas rotas/rankings complexos.

## Implementado no código da v1.14.37 — Busca de caminhos RF possíveis, validação de campo pendente (issue #86)

- **Pedido em 13/10/2026:** a captura de "Análise de rota RF" apresenta `PP1MSC-15 ↔ PY2PJA` com 6 saltos/872,7 km de percurso/809,6 km entre extremidades, porém o mapa geral sugere que pode haver outra cadeia Brasília → Sul. Oferecer **Busca de caminhos possíveis** por origem/destino sem afirmar que um único pacote percorreu todos os saltos.
- **Evidência da exportação diagnóstica v1.14.34 (12/10):** 872 relações, 606 RF, 36.951 eventos e 50 rotas listadas. O grafo histórico contém caminho de `PT2ON-15` a `PP5APR-10`, mas a ligação curta passa por **`PT2AP-9`**, digi móvel em várias localidades. **Não é prova de conectividade contínua:** RF legítimo local de momentos diferentes não pode ser unido como rota operacional no mesmo instante.
- **Classes separadas:** `mesmo pacote/path comprovado`; `alcançabilidade histórica espaço-temporalmente compatível`; `rota potencial/hipótese` para exploração do mapa, com cores/legendas distintas e explicação do que falta comprovar.
- **Geometria:** utilizar posições e horários contemporâneos do pacote. Impedir "ponte" virtual quando o mesmo digi móvel esteve no Sul e perto de Brasília em tempos diferentes; preservar as observações RF verdadeiras; jamais converter backhaul Starlink/APRS-IS em VHF.
- **Ranking #1:** deixar explícito se o critério é **distância direta entre extremidades** ou **soma dos saltos** e permitir alternar a ordenação. Na exportação, o primeiro registro soma ~965 km e o sexto ~1006 km; isso é compatível com ordem pelo alcance direto, mas não com uma tabela identificada somente como "maior extensão percorrida".
- **Aceite:** consulta Brasília ↔ Sul mostra opções plausíveis e seus impedimentos/nível de evidência, sem inserir enlaces inexistentes no banco. Buscar direção origem→destino e não depender de o caminho entrar no top 50 do ranking. Validar com testes sintéticos de múltiplos SSIDs e do PT2AP móvel. Relacionado à #85.
- **Rastreamento:** [issue #86](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/86). **Implementada a busca independente de origem/destino, classes de evidência, bloqueios espaço-temporais e interface não cartográfica para hipóteses.** Ainda pendem testes RF de campo e ordenação alternativa dos recordes por soma de saltos; não considerar a issue integralmente concluída.

## Implementado na v1.14.36 — Filtro APRS-IS padrão de 4.000 km (issue #87)

- **Pedido em 13/10/2026:** Configurações → Filtro APRS-IS com **raio padrão de 4.000 km**, referido informalmente como `/r4000`.
- **Sintaxe correta no aplicativo:** **`r/4000`** (sem barra inicial e com a barra entre `r` e `4000`). `aprs_service.expand_filter()` já reconhece `r/RAIO` e envia ao servidor **`r/<latitude>/<longitude>/4000`**, usando como centro a posição configurada da estação. A string literal `/r4000` não é sintaxe válida APRS-IS.
- **Estado anterior:** `database.BRAZIL_FILTER` usa `p/PP/PQ/PR/PS/PT/PU/PV/PW/PX/PY/ZV/ZW/ZX/ZY/ZZ` e ainda é o default da v1.14.35; não declarar a alteração implementada.
- **Implementação:** alterar default de instalações novas (config, schema, HTML, editor e ajuda, traduções, README/manual/tests), e mostrar prévia da expansão para lat/lon. **Não sobrescrever filtros personalizados já salvos**. Exigir posição válida antes de conectar; erro explicativo se faltar.
- **Atenção:** um raio de 4.000 km pode aumentar bastante o tráfego RX em comparação ao filtro de prefixos brasileiros; monitorar performance/memória/CPU e informar ao usuário.
- **Rastreamento:** [issue #87](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/87). **Implementado na v1.14.36**, mantendo configurações preexistentes; monitorar carga RX.

## Implementado no código da v1.14.35 — PT2AP móvel: geometria RF histórica (issue #85; validação em campo pendente)

- **Esclarecimento expresso do mantenedor:** os contatos do **PT2AP como digipeater no Sul foram verdadeiramente RF**. A falha **não é classificar esses contatos como RF**, mas sim o mapa desenhá-los desde as estações locais do Sul **até a nova posição atual do digi móvel**, como se seus enlaces tivessem sido herdados/esticados durante a viagem a Brasília. **Não apagar, reclassificar como Internet ou desconsiderar esses enlaces reais**: manter sua origem RF e congelar posição/hora/distância de cada evento histórico. Mostrar o marcador atual independentemente das posições históricas e não unir segmentos de Sul/Uberaba/Brasília numa reta interestadual fictícia.
- **Relato visual de 12/10/2026:** o PT2AP operava como **digi RF e iGate com Starlink** durante viagem do Sul do Brasil rumo a Brasília. Enquanto estava no Sul, repetiu estações locais; após deslocar-se, o mapa apresentou inúmeros **enlaces amarelos aparentemente interestaduais** entre o Sul, Uberaba/MG e a posição mais recente do PT2AP. O usuário descreve precisamente que os enlaces ficaram **“esticados”** acompanhando o carro.
- **Causa da regressão na v1.14.34 (corrigida na v1.14.35):** `database.py::list_topology_edges()` (endpoint `GET /api/topology`) busca `source_lat/lon` e `target_lat/lon` por `JOIN stations`, usando a posição **atual/última conhecida** das duas pontas mesmo que `topology_edges` seja histórico. `static/js/app.js::loadTopology()` redesenha `L.polyline` com essas coordenadas atuais. Logo, quando o PT2AP muda de GPS, a geometria dos enlaces RF antigos muda **retroativamente**. O motor `spacetime_topology.py` já possui posições históricas em `topology_events`, mas isso ainda não foi integrado ao desenho geral do mapa.
- **Correção:** usar coordenadas e timestamp **do instante de cada evento** para renderizar enlaces; preservar segmentos históricos locais do PT2AP onde ocorreram, separados por clusters espaço-temporais, enquanto só o marcador atual do digi/iGate se movimenta. **Não transportar** as estações do Sul para Uberaba ou Brasília, nem produzir um enlace RF direto onde apenas o iGate mudou de lugar.
- **Qualidade da evidência:** diferenciar `RF recebido no TNC`, `RF local inferido pelo path APRS`, `Internet/APRS-IS` e `RF → iGate → Starlink`. `qAR/qAO` podem sustentar uma recepção RF **local no ponto do iGate**, mas não confirmam um enlace VHF inter-regional até o observador APRS-IS. Preservar saltos RF locais genuínos sem confundir o backhaul Internet com RF direto.
- **Dados insuficientes:** sem posição histórica contemporânea verificável, **não desenhar a aresta até o GPS atual**. Registrar/enxergar a evidência antiga no banco, ranking/histórico e exportação, mas classificar a **geometria como indeterminada** até que haja evidência espacial confiável.
- **Aceite:** exemplo A↔PT2AP visto no Sul às 08h deve continuar no Sul mesmo após PT2AP atualizar GPS perto de Brasília às 19h. Segundo enlace B↔PT2AP perto de Uberaba fica naquela região/horário, sem A↔B interestadual inventado; seleção de período, topologia geral, análise RF, Recordes, exportação JSON e popup exibem a mesma geometria física e a origem da evidência.
- **Regressão obrigatória:** teste com digi/iGate móvel, repetição RF de estações locais em duas regiões ao longo da viagem, ingresso APRS-IS por Starlink, múltiplos SSIDs, posições históricas indisponíveis e base de dados legada. Não usar apenas limiar de quilômetros para vetar propagação VHF genuinamente anômala.
- **Implementação v1.14.35:** `pt2vhf_aprs/topology_map.py` consulta `topology_events` com latitude/longitude contemporâneas, clusters/IDs por localização e distinção RF/APRS-IS. `/api/topology`, KML, popup e JSON de diagnóstico deixam de usar as coordenadas atuais de `stations` para desenhar enlaces. Linhas sem geometria não são inventadas, e histórico bruto permanece intacto.
- **Status:** [issue #85](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/85). **Código integrado, aguarda suite CI e teste com banco verdadeiro do PT2AP.** Não encerrar apenas com builds.

## Em validação na v1.14.34 — Correções prioritárias das issues #82, #83 e #84

- **#82 — UI de agendamentos:** convertida para modal, com formulário e listas ocultos até ação explícita. Proteger edição não salva e não afetar trabalho agendado em segundo plano. Código alterado; teste visual físico ainda necessário.
- **#83 — Portable v1.14.31 → v1.14.33:** helper do novo cliente passa a repetir backup/renomeação quando o executável está bloqueado; valida presença do novo servidor Web com arquivo `update_ready.flag` e tenta restaurar versão anterior em falha. **A versão 1.14.31 já distribuída continua com helper antigo**; primeira migração pode exigir download manual. Falhas pythonnet/netfx/_MEI do sistema de origem ainda requerem investigação e logs.
- **#84 / #77 — bandeja do Windows:** nova imagem própria, opaca e de alto contraste, com texto APRS grande, sem depender de redimensionar um ICO; ainda requer confirmação em Windows 7/10/11 reais. Menu pystray mantido.
- **#78–81 — LAN/alertas:** preservadas e revalidadas as alterações de código existentes na v1.14.33; feedback real de desempenho e segurança ainda é obrigatório para conclusão.
- **Estado:** código da v1.14.34 **publicado oficialmente em 12/10/2026**, com pipeline completo Windows x64/ARM64/Win7 Legacy, Linux x64/ARM64, macOS Intel/ARM64 e manual PDF aprovado. Validação física/funcional de algumas issues permanece pendente. **Não equivale à resolução integral do backlog histórico** (ex.: console transitório do Win7, dependências .NET/pywebview específicas e assinatura externa). Somente encerrar as issues após builds e aceites em campo.

## Implementado no código da v1.14.34 — BUG da bandeja Windows (issue #84; teste físico pendente)

- **Evidência fotográfica de 12/10/2026:** bandeja de notificações do Windows (seta ^, junto ao relógio) aberta com menu do **PT2VHF APRS Client** funcionando. O ícone correspondente, indicado pelo usuário na **segunda posição da linha superior, da esquerda para a direita**, está praticamente invisível/ilegível. Trata-se da **bandeja/system tray**, não apenas do botão da janela na barra principal de tarefas.
- **Diagnóstico da versão anterior:** `windows_app.py::_create_tray_icon()` instanciava `pystray.Icon`, mas `_make_tray_image()` carregava o ICO de 32 px e o ampliava para 64 px com fallback silencioso. A v1.14.34 agora desenha uma imagem específica da bandeja, registrando falhas e fallback. Falhas de extração, transparência, tamanho útil e fallback devem ser diagnosticadas no **Portable/Setup efetivamente compilado**, sem atribuir causa antes da validação.
- **Correção requerida:** garantir ícone do **APRS bem contrastante, opaco onde necessário e com alta ocupação útil** na bandeja, com variante específica para 16/20/24 px; registrar no diagnóstico qual recurso foi carregado, dimensões e eventuais fallbacks; evitar `except Exception: continue` sem log; manter clique/menu funcionais.
- **Aceite:** visível nos temas claro e escuro, diferentes escalas DPI, Windows 7 Legacy/10/11 (ARM64 quando disponível), bandeja aberta/oculta, após reinício Explorer e atualização; verificar com capturas de executáveis reais, não apenas testes de `.ico` de build. Preservar legibilidade e identidade visual do PT2VHF/APRS no desktop e barra de tarefas.
- **Relacionado:** [#77 — ícone APRS ampliado no Windows](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/77). A v1.14.33 foi **reprovada em campo**; na v1.14.34 foi incluído um ícone próprio, opaco e contrastante, ainda pendente de novo teste visual.
- **Rastreamento:** [issue #84](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/84). **Correção incluída na v1.14.34; manter aberto até confirmação visual em Windows real.**

## Implementado no código da v1.14.34 — Modal de agendamento (issue #82; teste visual pendente)

- **Pedido do mantenedor em 12/10/2026:** tarefas usadas esporadicamente (começando por **agendamento de mensagens**) devem usar uma janela/modal **visível apenas enquanto necessária**, mantendo a tela principal livre de formulários extensos.
- **Situação anterior à v1.14.34:** o botão **Agendadas (N)** em Mensagens abria `#scheduledMessagesPanel` dentro do fluxo da própria aba; o painel exibe ao mesmo tempo formulário `#scheduledMessageForm`, listas de destinatários e tabela `#scheduledMessagesTable`, ocupando espaço precioso do chat e da lista.
- **Novo comportamento:** o botão **Agendadas** abre um popup centralizado e responsivo, com lista/resumo dos agendamentos, botão **Novo**, ações de editar/ativar/desativar/executar/excluir e **formulários exibidos somente na ação Novo/Editar**. A gestão das listas de destinatários também deve aparecer somente quando solicitada.
- **Fechamento:** `Fechar`, `Cancelar` e tecla `Esc`; confirmação ao descartar mudanças não salvas, foco gerenciado e devolvido ao botão de origem, acessibilidade (`role=dialog`, `aria-modal`), temas e traduções. Garantir rolagem interna/altura máxima em telas 1280×720 e Windows 7 Legacy.
- **Persistência/execução:** o modal é somente apresentação: fechar/ocultar não cancela o trabalho agendado, não interrompe a thread/worker de envio, não limpa agendamentos salvos e não dispara envio imediato. O contador e a lista precisam refletir o SQLite.
- **Arquitetura:** criar padrão reutilizável para outras operações eventuais complexas, sem converter controles cotidianos em popups, nem confundir com a janela **nativa intermitente** do Win7 que constitui um bug separado.
- **Critérios de aceite:** a aba Mensagens mantém somente acesso compacto **Agendadas (N)** quando fechado; popup e subformulários aparecem sob demanda; operações de agendamento continuam funcionais; sem perda silenciosa de rascunhos; teste de teclado/responsividade/Windows 7 e 11.
- **Rastreamento:** [issue #82](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/82). **Implementado na v1.14.34; validação em Windows real ainda pendente.**

## Restaurado na v1.14.33 — Configuração: silenciar aviso de estação nova (issue #81)

- **Regressão relatada em 12/10/2026:** sumiu da aba Configuração a opção para silenciar o aviso quando uma nova estação é recebida ou reaparece.
- **Causa encontrada:** o checkbox `station_appeared` ainda existia em `pt2vhf_aprs/static/js/v190.js`, mas seu cartão dinâmico “Backup completo, grupos e alertas” era anexado fora de `#configForm`, após o rodapé Salvar configuração; dificultava a localização.
- **Correção no código-fonte:** recolocar o cartão na grade principal de Configuração, antes de “Retenção e tamanho do banco”, com título **Alertas e notificações de estações** e instrução “Desmarque Estação apareceu para silenciar os avisos de novas estações”. Preservar `station_appeared` e o salvamento imediato/persistente via `/api/v190/alerts/settings`.
- **Teste pendente de validação física:** abrir Configuração nas edições Windows 7/11, desmarcar e confirmar que não aparecem alertas de estação nova/reentrada; reiniciar e validar estado persistido. Sem interferir nos demais alertas.
- **Rastreamento:** [issue #81](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/81). Implementado e publicado na v1.14.33/34; manter aberta até confirmação funcional em campo.

## Implementado no código da v1.14.33, preservado na v1.14.34 — Indicador Web remoto (issue #80)

- **Solicitação do mantenedor em 12/10/2026:** ampliar moderadamente o IP e a porta do endereço Web no cabeçalho, tornando-os mais visíveis; destacar o mesmo bloco com **fundo laranja e letras pretas quando houver alguém utilizando a interface Web pela rede**.
- **Estados:** normal quando não há usuário remoto ativo; **laranja + preto + texto “Web em uso”** quando há sessão remota efetivamente ativa; indicar separadamente se LAN estiver desabilitada/indisponível. Preservar legibilidade em temas claro/escuro, resoluções pequenas e Windows 7 Legacy.
- **Detecção de atividade:** não confundir “houve um acesso remoto há menos de 15 minutos” com “há alguém usando agora”. O antigo `lan_access.py::last_remote_request()` usa janela de 900 s apenas para acesso recente; desde a v1.14.33 há também presença/heartbeat das sessões remotas com expiração curta (~75 s), sem contá-la como último acesso histórico.
- **Implementação:** atualizar `#webAccessStatus`, `#webAccessLabel`, `#webAccessUrl` em `pt2vhf_aprs/templates/index.html`; estilos de `.web-access-status` em `pt2vhf_aprs/static/css/app.css`; atualização dinâmica em `pt2vhf_aprs/static/js/app.js::updateWebAccessStatus()`; fornecer `remote_web_active` e contagem de sessões no diagnóstico da interface Web com atualização periódica e i18n.
- **Aceite:** IP/porta um pouco maiores e sem truncar; cor laranja com texto preto apenas durante uso remoto; retorno automático ao visual normal em no máximo ~2 min após cessar atividade; modo LAN desativado não indica usuários ativos; testes em LAN com múltiplas sessões e navegador local, incluindo Windows 7/11.
- **Relacionado:** [issue #78](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/78) (abertura por IP LAN) e [issue #79](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/79) (padrões de inicialização).
- **Rastreamento:** [issue #80](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/80). **Implementado; validação remota real e DPI pendente.**

## Implementado na v1.14.33, preservado na v1.14.34 — Padrões LAN/navegador (issue #79)

- **Solicitação de 12/10/2026:** a opção **“Permitir acesso Web pela rede local (LAN)”** deve vir **ativada por padrão** (`web_lan_enabled=1`), enquanto a opção **“Abrir também no navegador ao iniciar”** deve permanecer **desativada por padrão** (`open_browser_on_start=0`).
- **Estado corrigido:** `pt2vhf_aprs/database.py::DEFAULT_CONFIG` define `open_browser_on_start=0` e `web_lan_enabled=1`. O schema SQL, migração e texto de ajuda foram ajustados para novas configurações; preferências previamente salvas são preservadas.
- **Persistência:** aplicar o novo default somente a configurações novas, sem sobrescrever a escolha de quem já habilitou ou desabilitou LAN no banco. A inicialização do servidor deve respeitar a configuração efetivamente persistida.
- **Operação:** disponibilizar o backend Web na LAN sem disparar navegador/aba extra automaticamente; manter acesso manual pela bandeja, links e dispositivos na LAN. Preservar o modo app do Windows 7 Legacy, cuja janela baseada em navegador pode ser necessária para exibir a interface principal — não confundir com a opção de abrir uma aba adicional.
- **Segurança:** não habilitar port-forward/UPnP nem acesso WAN; regras de firewall devem permanecer restritas à sub-rede local, sem conceder permissões administrativas silenciosamente. Exibir corretamente IP e porta reais, e permitir desativação simples da LAN.
- **Verificações:** primeira instalação, atualização com preferências salvas, textos de configuração/i18n, Windows 7/10/11 e demais plataformas, testes de defaults e ausência de abertura automática de navegador.
- **Relacionado:** [issue #78](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/78) — quando navegador for aberto explicitamente, preferir o IP LAN utilizável.
- **Rastreamento:** [issue #79](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/79). **Implementado; validar primeira instalação real.**

## Implementado na v1.14.33, preservado na v1.14.34 — Abrir Web pelo IP LAN (issue #78)

- **Pedido em 12/10/2026:** quando o PT2VHF APRS Client abrir a interface no navegador, priorizar o endereço IPv4 **real do computador na rede**, por exemplo `http://192.168.1.25:8080`, e não `http://127.0.0.1:8080`.
- **Escopo:** inicialização com navegador, opção de abrir a interface pela bandeja, reabertura quando já existe instância e modo navegador do Windows 7 Legacy. A porta deve ser a que foi **realmente reservada** pelo backend, não uma constante presumida.
- **Segurança/compatibilidade:** preferir endereço LAN somente se `web_lan_enabled` estiver ativado, o servidor estiver escutando em endereço da rede e o IP/porta forem acessíveis. Não habilitar compartilhamento, firewall nem exposição externa silenciosamente. Se o servidor aceitar apenas loopback ou a interface LAN estiver indisponível, utilizar `127.0.0.1` como fallback para não abrir página inacessível.
- **Infraestrutura corrigida:** `LocalServerHandle.share_url` e `lan_host` em `pt2vhf_aprs/local_server.py` oferecem o caminho compartilhável, e `windows_app.py::_current_url()` / `read_runtime_browser_url()` preferem IP LAN confirmado, preservando localhost como fallback.
- **Multi-interface:** tratamento de Ethernet/Wi-Fi/VPN/adaptadores virtuais; registrar diagnóstico do IP escolhido e do fallback. Preservar `127.0.0.1` para watchdog e verificações internas que não precisam da URL externa.
- **Aceite:** teste em Windows 7 Legacy e Windows 11, com LAN ativada/desativada, porta alternativa e reabertura pela bandeja/segunda instância.
- **Rastreamento:** [issue #78](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/78). **Implementado; testar multirrede e reabertura em Windows real.**

## Implementado no código da v1.14.33/34 — Ícones APRS Windows (issue #77; teste físico pendente)

- **Relato do mantenedor em 12/10/2026:** os ícones usados no Windows parecem minúsculos tanto na Área de Trabalho quanto na barra de tarefas e na área de notificação (bandeja próxima ao relógio).
- **Objetivo:** ícone com ocupação visual maior **dentro dos limites de tamanho impostos pelo próprio Windows**, contraste robusto, a palavra **APRS** em destaque e preservação da identidade visual do PT2VHF. Não modificar a logomarca do aplicativo na interface.
- **Arte/resoluções:** projetar composições específicas para 16/24/32/48/64/128/256 px, evitando grandes margens transparentes e perda de legibilidade ao reduzir a imagem. Priorizar marca e texto APRS legíveis nos tamanhos pequenos; não simplesmente aumentar o canvas.
- **Caminhos técnicos:** revisar `windows/make_icon.py`, `windows/aprs_taskbar_icon.png`, `windows_app.py::_make_tray_image`, `app_icon.ico`, todos os `*.spec` Windows e ícones de atalhos dos instaladores Inno Setup, abrangendo x64, ARM64 e Windows 7 Legacy.
- **Aceite:** conferir visualmente, em máquinas reais, Área de Trabalho, barra de tarefas, bandeja, Alt+Tab e atalhos após instalar/atualizar; verificar transparência, cache de ícones, variações de DPI e ausência de regressão para Win7.
- **Rastreamento:** [issue #77](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/77). **Geração multirresolução e bandeja opaca/contrastante implementadas; aguarda inspeção do usuário.**

## Implementado — README GitHub com downloads diretos de todas as plataformas (12/10/2026)

- A [página principal do projeto](https://github.com/alexpmr/PT2VHF-APRS-Client) voltou a mostrar, no topo, os links diretos de **todas** as opções publicadas na release v1.14.32: Windows x64/ARM64, Windows 7 Legacy, Linux x86_64/ARM64, macOS Intel/ARM64 e Manual PDF.
- Os links foram comparados aos nomes reais dos 15 artefatos baixáveis da GitHub Release, evitando URLs antecipadas e o erro 404 da versão anterior.
- Continuar privilegiando lista completa e visível de downloads no início do README nas releases futuras.

## Aberto — PRIORIDADE ALTA: Windows 11 não atualiza e falha ao iniciar após as versões recentes (PyInstaller _MEI / pythonnet .NET)

- **Reprodução agora confirmada pelo PP5UA:** uso da edição **Windows Portable v1.14.31**, comando **Atualizar para v1.14.33**, download concluído, processo atual fecha e a versão nova **não abre**. Sistema Windows exato ainda não confirmado. Correlacionar com os prints `netfx` e PyInstaller `_MEI`. `updater.py::_write_windows_cmd_helper` aguarda apenas `ping -n 6`, depois aplica `move /Y`; quando `destination=current` (Portable), o laço existente **não repete o move após erro**, deixando uma corrida de bloqueio de arquivo sem tratamento. Corrigir PID/wait, retentativas reais, logs por etapa, healthcheck do novo EXE e rollback; validar atualização a partir da **v1.14.31 já distribuída**, não apenas da versão nova, pois o helper que executa inicialmente é o da versão antiga. [Issue #83](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/83) atualizada. **Diagnóstico ainda não confirmado por logs; evitar afirmar solução.**
- **Novo relato fotográfico — PP5UA, 12/10/2026:** erros ao tentar atualizar, com duas evidências: (1) janela integrada indisponível por `Failed to create a default .NET runtime ... 'netfx'`, com fallback previsto para navegador; (2) erro PyInstaller `Failed to remove temporary directory` em `%LOCALAPPDATA%\\Temp\\_MEI000012282`. Os dois sintomas **não comprovam a mesma causa**; correlacionar com falha pré-existente `pyiboot01_bootstrap` somente após obter `diagnostics.log` e `updates/update_apply.log`. O sistema Windows, versão de origem/destino e edição Setup/Portable deste relato específico ainda requerem confirmação. **Issue de rastreamento:** [#83 — PP5UA: pythonnet/netfx + PyInstaller _MEI](https://github.com/alexpmr/PT2VHF-APRS-Client/issues/83). **Pendente; não declarar solucionado pelo simples sucesso do pipeline CI.**
- **Relato de campo em 12/10/2026:** usuário de **Windows 11** informou que, depois da penúltima atualização, não consegue mais concluir a atualização do PT2VHF APRS Client. Evidência fotográfica de **três erros distintos**. A versão exata de origem/destino e se a instalação é Portable ou Setup precisam ser confirmadas nos logs; não presumir sem prova.
- **Erro 1 — PyInstaller bootstrap:**
  - janela `Unhandled exception in script`;
  - `Failed to execute script 'pyiboot01_bootstrap' due to unhandled exception: [Errno 2] No such file or directory`;
  - caminho transitório `C:\Users\rotor\AppData\Local\Temp\_MEI...\base...` (diretório temporário PyInstaller `_MEI`, sufixo parcialmente visível);
  - `Failed to obtain/convert traceback!`.
- **Erro 2 — cleanup:** janela `Failed to remove temporary directory: C:\Users\rotor\AppData\Local\Temp\_MEI...`, sugerindo arquivo ainda bloqueado, extração interrompida, concorrência de processos, antivírus ou interrupção do bootstrap; diagnóstico necessário antes de definir causa.
- **Erro 3 — WebView/.NET:** `Não foi possível iniciar a janela integrada do PT2VHF APRS Client. A interface será aberta no navegador padrão.` Detalhes: `Failed to create a default .NET runtime, which would have been 'netfx' on this system. Either install a compatible runtime or configure it explicitly via 'set_runtime' or the 'PYTHONNET_*' environment variables`.
- **Classificação:** **regressão impeditiva de atualização/inicialização no Windows 11**. Não confundir o erro de bootstrap `_MEI` com erro de .NET: ambos podem ser independentes e exigem testes separados.
- **Investigar PyInstaller one-file / atualização:**
  - confirmar se o executável afetado é o **Portable (one-file)** ou **Setup/on-directory** e origem/destino da atualização;
  - testar execução direta sem updater e execução após atualização para isolar empacotamento versus instalador;
  - conferir `_MEIPASS`, `sys._MEIPASS`, `sys.executable`, `TEMP/TMP`, extração `_MEI*`, permissões, antivírus/Defender e arquivos ausentes da extração;
  - revisar a sequência do `apply_update.cmd`: helper pronto, solicitação de saída, encerramento integral do processo e filhos WebView/Chromium, arquivo EXE liberado, backup íntegro, substituição atômica e relançamento **uma vez**;
  - evitar iniciar um EXE substituído ainda em extração, concorrência entre duas instâncias e limpeza de `_MEI` pertencente a um processo ativo;
  - conferir integridade da transferência (tamanho, SHA-256, assinatura quando disponível), e não iniciar arquivo parcial/corrompido;
  - quando a atualização falhar ou a nova versão não confirmar inicialização/saúde, fazer rollback seguro para a anterior, **sem apagar `SQLite`, configurações, logs, mensagens ou arquivos do usuário**;
  - registrar no `update_apply.log`/diagnóstico: versão origem/destino, modo Portable/Setup, caminho do EXE, PID origem/helper/destino, etapa, código de saída, caminho TEMP/`_MEI`, hashes e resultado do rollback (sem expor senhas/APRS passcodes).
- **Investigar pywebview/pythonnet/.NET no Windows 11:**
  - verificar runtime `.NET Framework`/compatibilidade com `pythonnet`, WebView2 Runtime e dependências nativas presentes no empacotamento;
  - considerar variáveis `PYTHONNET_*` e seleção `set_runtime` somente após identificar runtime compatível e disponível;
  - tratar falta/incompatibilidade do `.NET` como falha **somente da janela integrada**, mantendo backend e interface acessível no navegador padrão **sem interromper recebimento APRS**;
  - registrar diagnóstico legível ao usuário (runtime encontrado/ausente, GUI selecionada, exceção e orientação), com fallback sem loop de janelas.
- **Plano de testes:** Windows 11 x64 Setup/Portable em instalação limpa e após upgrade de pelo menos duas versões anteriores; atualização com aplicativo e WebView abertos/fechados; concorrência de processo anterior; TEMP com caminho contendo espaços/acentos; interferência de Defender; disco cheio/permissão negada; runtime .NET disponível/ausente; rollback; integridade dos dados APRS.
- **Critério de aceite:** no **Windows 11 real**, um usuário na versão anterior deve conseguir usar **Atualizar pelo aplicativo** e terminar com a versão nova operacional, uma única instância, janela integrada funcional ou fallback previsível, sem popup PyInstaller `_MEI`, erro de cleanup ou exceção não tratada de runtime .NET; caso falhe, recuperar automaticamente a versão anterior e preservar dados.
- **Mitigação até correção:** recomendar download manual do instalador/Portable correto pela página oficial Releases, encerrar o aplicativo inclusive na bandeja antes de iniciar, manter backup de dados e preservar os logs `updates/update_apply.log` e `diagnostics.log`; evitar apagar `AppData` de dados do Client como tentativa de correção.

## Reaberto — Win7 v1.14.30: popup intermitente persiste mesmo após fechar acesso Web

- **Relato em Win7 Legacy:** uma pequena janela/popup aparentemente vazio abre e fecha rapidamente a cada aproximadamente 5 segundos durante o funcionamento normal.
- **Esclarecimento sobre a natureza da janela:** não se trata de modal, toast ou popup HTML dentro da interface do PT2VHF. É **uma janela independente do Windows 7**, visível por um instante **também na barra de tarefas**, antes de desaparecer. Priorizar diagnóstico de criação/encerramento de processos e de janelas nativas; não alterar modal/UI Web com base nesse sintoma.

- **Teste de isolamento confirmado pelo usuário:** com o PT2VHF APRS Client completamente fechado, a janela intermitente também deixa de aparecer. Com o aplicativo aberto, reaparece. Isso estabelece correlação direta com a execução do Client (ou seus processos filhos), mas não identifica ainda o processo que cria a janela.
- **Instrumentação da v1.14.31:** monitor nativo `EnumWindows` ativado apenas no Win7 Legacy durante os primeiros 180 segundos, registrando em `diagnostics.log` novas janelas visíveis pertencentes ao processo ou aos filhos, com PID, nome do processo e título. Não cria janelas ou subprocessos adicionais. Manter o problema aberto até reproduzir e identificar a origem real; correção preventiva do `netsh` em main foi empacotada.
- **Prioridade de diagnóstico:** instrumentar/identificar processo filho ou janela nativa transitória durante a execução Win7 Legacy, considerando explicitamente a shell Chromium `--app`, subprocessos Windows e eventos periódicos. Correlacionar `PID`, `PPID` e horário da janela antes de promover uma correção como definitiva. **Não atribuir causalidade exclusiva ao netsh enquanto não houver evidência**.
- **Observação do código:** o watchdog interno executa sondagens HTTP a cada aproximadamente 3 segundos, mas não inicia subprocessos diretamente; esse intervalo semelhante, por si só, não prova que ele gera a janela.

- **Reprodução reportada:** persiste quando o usuário fecha/desativa o acesso Web; não pressupor que o problema é exclusivo da função Web LAN ou do `netsh`. Reconfirmar em ambiente real após encerrar totalmente a instância e reiniciar, mas investigar também processos independentes do servidor LAN.
- **Diagnóstico obrigatório antes de considerar corrigido:** identificar nome e caminho do executável responsável, PID/PPID, linha de comando, horário e frequência de criação, eventual título/classe da janela e código de saída. Preferir captura de eventos `Process Create/Process Exit` com Process Monitor compatível com Windows 7 (ou ferramenta equivalente), correlacionando com os logs do aplicativo, sem capturar dados pessoais desnecessários.
- **Suspeitos a investigar, sem atribuir causa ainda:** `cmd.exe`, `netsh.exe`, `powershell.exe`, subprocessos de sondagem periódica, launcher `chrome.exe`/`chromium.exe` em modo `--app`, auxiliares do updater, scripts ou tarefas agendadas. Verificar relação pai-filho com o executável PT2VHF antes de atribuir a ele o evento.
- **Aceite:** durante pelo menos 5 minutos com Win7 Legacy em execução, com LAN ligada e desligada (após reinício completo), não deve surgir janela externa transitória na barra de tarefas. Os logs devem permitir identificar eventuais processos auxiliares acionados pelo app.
- **Novo retorno do teste em Win7 real:** o usuário informou que fechou/desativou o acesso Web, mas a janela intermitente **continua aparecendo**. A hipótese `netsh` **não está confirmada** como causa exclusiva. Verificar se a mudança foi feita apenas na interface ou também aplicada após encerrar e reiniciar completamente o processo PT2VHF (o bind/configuração LAN só é lido na inicialização).
- **Reclassificação:** problema **permanece aberto para diagnóstico**. A correção `CREATE_NO_WINDOW` é preventiva e deve ser mantida, porém não autoriza declarar o popup resolvido.
- Se persistir após reinicialização com `web_lan_enabled=0` e `scope=local`, coletar a identificação real da janela/processo (Process Monitor/Process Explorer), hora e periodicidade; verificar se é console nativo, janela do Chromium em modo app, janela do próprio aplicativo ou notificação do Windows.
- Auditar processos auxiliares e atividades periódicas independentemente do servidor LAN, sem mexer na frequência de recepção APRS ou no updater sem evidência.

- **Causa provável identificada no código:** a UI chama `refreshStatus()` a cada 3 segundos; `/api/status` chama `lan_diagnostics()`; com Web LAN habilitada, `windows_firewall_rule_exists()` executava `netsh advfirewall firewall show rule` via `subprocess.run` **sem `CREATE_NO_WINDOW`**. Em Windows 7 com executável PyInstaller sem console isso pode abrir e fechar uma janela `cmd/netsh` em cada sondagem.
- **Correção no main (ainda não publicada em release):**
  - executar `netsh` de diagnóstico com `creationflags=CREATE_NO_WINDOW`, sem abrir console visível;
  - memorizar o resultado da verificação por até **60 segundos**, por porta e caminho de executável, em vez de chamar `netsh` a cada `/api/status`;
  - invalidar cache quando for solicitada nova regra de firewall;
  - não alterar a coleta de status APRS nem a frequência da interface.
- **Testes de regressão:** `tests/test_win7_firewall_popup.py` valida flag de console oculto, reaproveitamento da consulta e invalidação/alteração de porta.
- **Validação ainda necessária:** testar no **Windows 7 real** com Web LAN habilitada, verificando ausência de janelas piscantes após vários minutos. Se persistir, identificar o processo pela ferramenta Process Monitor e auditar outros subprocessos periódicos (sem presumir que toda janela provenha do firewall).
- **Critério de aceite:** nenhuma janela de console ou popup intermitente aparece durante funcionamento normal ou atualização automática de status, independentemente de Web LAN estar ligada ou desligada.

> **v1.14.30 — implementação e validação:** adicionada verificação do socket no IP LAN real e detecção de reinício pendente, além de correção do handoff `exit=0` do Chromium. Os testes automatizados e o empacotamento não substituem o teste em duas máquinas na mesma rede nem uma atualização física do Win7 Portable.

## Validado em campo — Web LAN Windows 11 → Windows 11 (12/10/2026; issue #76 encerrada)

- **Retificação:** a interface Web funciona no computador host via `127.0.0.1` e pelo endereço IPv4 privado `192.168.x.x`.
- **Acesso remoto validado:** segundo computador Windows 11 abriu a interface Web do host também Windows 11 na mesma LAN.
- **Issue #76 encerrada:** falha Web não se reproduz no ambiente efetivamente testado. Não repetir no backlog o relato já retificado.
- **Windows 7:** funcionalidade de Web LAN entre duas máquinas ainda não validada em Win7 real; conservar testes de campo.
- **Segurança:** opt-in, autorização explícita de UAC e regra TCP limitada à sub-rede local; nunca abrir acesso à Internet.
- **v1.14.32:** pipeline executará smoke HTTP da página HTML, asset JavaScript, ping e remote-probe usando Python 3.8 no build Win7 Legacy e builds modernos.
- **Separados:** popup nativo transitório no Windows 7 e falhas PyInstaller/pythonnet no Windows 11 continuam em investigação.

## Em validação na v1.14.30 — Win7 Legacy Portable: relançamento após update

- **Falha confirmada em Windows 7 Portable após atualização integrada:** o aplicativo informa que a atualização foi concluída, por exemplo **v1.14.28 → v1.14.29**, mas durante o relançamento aparece a mensagem:
  - **“Não foi possível iniciar a janela dedicada do Windows 7 Legacy.”**
  - **“Detalhes: Shell encerrou imediatamente (exit=0).”**
- O resultado atual não corresponde ao comportamento esperado: a atualização deve terminar com a nova versão aberta normalmente na janela Legacy, sem cair desnecessariamente para o navegador padrão.
- **Causa provável a validar:** no modo Legacy, Chrome/Chromium/Brave pode aceitar a solicitação `--app=...`, repassar a abertura para um processo já existente e encerrar o processo filho com **exit code 0**. O launcher atual trata qualquer encerramento rápido como erro, mesmo quando `exit=0` representa handoff bem-sucedido.
- Revisar `_launch_legacy_app_window()` em `windows_app.py`:
  - **exit code 0 não deve ser tratado automaticamente como falha**;
  - considerar falha imediata apenas quando houver código de saída diferente de zero ou evidência concreta de que a janela não foi aberta;
  - não depender da permanência do processo filho do navegador para concluir que a janela está ativa;
  - registrar separadamente `process_handoff`, `exit_code`, `browser_path`, `profile_dir` e `url`.
- Quando o navegador já estiver em execução com o mesmo perfil, aceitar o handoff para o processo existente sem exibir alerta falso.
- Não abrir uma segunda instância/fallback no navegador padrão se a janela `--app` já tiver sido aceita por Chrome/Chromium/Brave.
- Revisar o ciclo completo do **updater Portable Win7**:
  1. baixar e validar o novo EXE Legacy;
  2. encerrar a instância PT2VHF anterior;
  3. encerrar/limpar somente a shell Legacy vinculada à instância anterior quando necessário;
  4. substituir o Portable;
  5. relançar **uma única vez** a nova versão;
  6. iniciar a janela Legacy;
  7. confirmar versão nova;
  8. não deixar janela/shell antiga concorrendo com a nova.
- O helper de atualização deve aguardar o encerramento real da instância anterior antes de relançar a nova versão.
- Evitar que o mutex/single-instance da aplicação redirecione o relançamento para uma instância antiga ainda viva.
- Registrar no diagnóstico do updater:
  - PID da instância anterior;
  - PID da nova instância;
  - caminho do executável antes/depois;
  - versão antiga/nova;
  - comando de relançamento;
  - resultado do relançamento;
  - navegador Legacy selecionado;
  - PID do processo de shell quando disponível;
  - exit code do launcher do navegador;
  - se ocorreu handoff para processo já existente.
- Adicionar teste de regressão simulando:
  - navegador `--app` iniciado;
  - processo filho encerra rapidamente com **exit=0**;
  - launcher deve considerar o handoff válido e **não** exibir erro/fallback.
- Adicionar teste separado para:
  - encerramento rápido com código diferente de zero → erro real/fallback controlado;
  - atualização Portable seguida de relançamento único;
  - ausência de instância antiga após update;
  - nova versão aberta e reportando a versão alvo.
- **Critério de aceite:** no Windows 7 Portable, após atualizar pelo próprio aplicativo, a versão nova deve abrir automaticamente e permanecer operacional. Um `exit=0` do processo intermediário Chrome/Chromium/Brave não pode ser tratado como falha se a abertura tiver sido repassada corretamente para o navegador já existente. Não deve surgir alerta falso nem abrir fallback duplicado no navegador padrão.

## Implementado na v1.14.30 — Configuração: retenção independente por tipo de dado no mapa

- Adicionar em **Configuração** uma seção específica de **Retenção de dados do mapa**.
- Permitir configurar por quanto tempo cada categoria permanece disponível para exibição/histórico no mapa e consultas relacionadas.
- A retenção deve ser configurável **independentemente por categoria**, incluindo pelo menos:
  - Estações;
  - Enlaces RF;
  - Enlaces Internet/iGate;
  - Digipeaters;
  - iGates;
  - Objetos APRS;
  - Itens AIS, quando aplicável;
  - Balões/Radiossondas, quando aplicável;
  - Tracklogs/posições históricas;
  - Mensagens APRS;
  - Boletins;
  - Mensagens de grupo/grupos;
  - demais entidades persistentes exibidas no mapa ou armazenadas no histórico.
- Sugestão inicial de períodos:
  - **24 horas**;
  - **1 semana**;
  - **1 mês**;
  - **3 meses**;
  - **6 meses**;
  - **1 ano**;
  - **Permanente / Nunca apagar**.
- Considerar também uma opção curta de **1 hora** ou **6 horas** apenas onde fizer sentido operacional, mas não poluir a interface com períodos excessivos.
- O padrão deve privilegiar histórico útil sem crescimento descontrolado do banco. Sugestão:
  - Estações: **1 mês**;
  - Enlaces RF: **Permanente**;
  - Enlaces Internet/iGate: **1 mês**;
  - Digipeaters: **Permanente**;
  - iGates: **Permanente**;
  - Objetos: **1 mês**;
  - Tracklogs: **1 mês**.
- A política de retenção deve controlar a **persistência no banco**, não apenas ocultar itens antigos da interface.
- **Objetivo principal:** evitar crescimento indefinido do banco SQLite e manter uso previsível de disco, tempo de consulta e desempenho geral da aplicação.
- A aplicação deve acompanhar o **tamanho total do banco** e registrar sua evolução ao longo do tempo.
- Exibir em Configuração/diagnóstico pelo menos:
  - tamanho atual do arquivo SQLite;
  - quantidade aproximada de registros por categoria/tabela relevante;
  - data/hora da última limpeza;
  - quantidade de dados removidos na última manutenção.
- Adicionar alerta quando o banco ultrapassar faixas configuráveis ou predefinidas de tamanho, sem bloquear a aplicação.
- Sugestão de faixas de aviso:
  - atenção: **500 MB**;
  - alto: **1 GB**;
  - crítico: **2 GB**;
  com possibilidade de ajuste futuro.
- A retenção deve ser aplicada também a tabelas auxiliares/históricas relacionadas às categorias, evitando que tabelas secundárias continuem crescendo mesmo quando a entidade principal for removida.
- Após purgas relevantes, avaliar execução segura de manutenção SQLite (`PRAGMA optimize`, checkpoint WAL e, quando apropriado, compactação/VACUUM controlada), sem travar a aplicação durante recepção de tráfego.
- Não executar `VACUUM` agressivamente a cada ciclo; usar somente quando houver ganho significativo de espaço e em momento seguro.
- Prever um resumo do tipo **“Banco: 742 MB · crescimento 18 MB/dia · retenção ativa”** quando houver dados suficientes para estimativa.
- Separar claramente:
  - **Período de visualização** do mapa (ex.: 1 h, 24 h, 7 d);
  - **Período de retenção** no banco.
- Reduzir o período de retenção não deve apagar dados imediatamente sem confirmação quando houver perda irreversível relevante.
- Ao trocar de **Permanente** para um período limitado, informar quantos registros antigos serão elegíveis para limpeza antes de executar a purga, quando tecnicamente viável.
- A limpeza deve ser incremental/segura para evitar:
  - travamento da aplicação;
  - lock prolongado do SQLite;
  - consumo excessivo de CPU;
  - impacto no recebimento APRS.
- Executar manutenção em background ou em lotes pequenos.
- Registrar no diagnóstico:
  - categoria;
  - política configurada;
  - quantidade de registros removidos;
  - duração da limpeza;
  - erro, se houver.
- A retenção deve respeitar o modelo histórico já existente: nós/enlaces que estiverem configurados como **Permanente** não podem desaparecer por timeout visual ou limpeza automática.
- **Enlaces devem ser independentes da retenção dos nós:** apagar/expirar uma estação, digi, iGate ou outro nó **não pode apagar automaticamente os enlaces históricos** em que esse nó participou.
- O histórico de enlaces deve preservar pelo menos:
  - origem/destino ou identificadores dos dois nós;
  - tipo do enlace (RF/Internet/iGate);
  - primeira e última observação;
  - distância, quando conhecida;
  - quantidade de ocorrências;
  - demais métricas necessárias para rankings e estatísticas.
- Se um nó já tiver expirado, o enlace deve continuar podendo aparecer em estatísticas/histórico usando o indicativo/identificador armazenado no próprio registro do enlace.
- Não usar `ON DELETE CASCADE` ou lógica equivalente que elimine enlaces históricos apenas porque o registro atual do nó foi removido.
- A limpeza de nós e a limpeza de enlaces devem obedecer **políticas de retenção distintas**.
- Adicionar retenção específica para:
  - **Mensagens individuais APRS**;
  - **Boletins**;
  - **Mensagens/grupos**.
- Sugestão de padrões:
  - Mensagens individuais: **3 meses**;
  - Boletins: **1 mês**;
  - Grupos: **3 meses**;
  com opção **Permanente** para qualquer categoria.
- A retenção de mensagens deve preservar a integridade de conversas, ACK/REJ, IDs e metadados necessários ao histórico enquanto os registros permanecerem dentro da política configurada.
- A limpeza de boletins/grupos não deve apagar mensagens individuais fora da categoria correspondente.
- Adicionar ação **“Aplicar retenção agora”** para permitir ao usuário executar manualmente a política configurada.
- Adicionar opção **“Restaurar padrões de retenção”** sem alterar outras configurações da aplicação.
- Persistir essas opções na configuração/banco e preservar os valores em atualizações futuras.
- Incluir traduções em todos os idiomas suportados.
- Adicionar testes cobrindo:
  - persistência das políticas;
  - retenção independente por categoria;
  - modo Permanente;
  - mudança de período;
  - limpeza em lotes;
  - preservação de nós/enlaces permanentes;
  - atualização sem perda das configurações anteriores.
- **Critério de aceite:** em Configuração, o usuário deve conseguir definir retenção independente para nós, enlaces, mensagens, boletins, grupos e demais categorias. A expiração de um nó nunca deve apagar seus enlaces históricos; cada categoria deve seguir sua própria política. A aplicação deve impedir crescimento indefinido do SQLite, mostrar o tamanho atual do banco e executar manutenção sem interromper o recebimento APRS. Retenção não pode ser confundida com filtro/período de visualização.

## Implementado na v1.14.29 — Cabeçalho continua em 127.0.0.1: detectar IP LAN independentemente do bind

- **Falha confirmada após a v1.14.28:** o cabeçalho continua mostrando `127.0.0.1` em vez do IPv4 real da máquina na rede, por exemplo `192.168.x.x`.
- **Causa estrutural identificada:** atualmente `LocalServerHandle.lan_host` só chama `detect_lan_ipv4()` quando o servidor está ligado a `0.0.0.0`/modo LAN. Quando o bind está em `127.0.0.1`, `lan_host` fica vazio, `scope` permanece `local` e o frontend recebe apenas o loopback.
- Separar definitivamente dois conceitos:
  1. **endereço de bind** — onde o servidor está escutando;
  2. **endereço do host na LAN** — IPv4 real da máquina, que deve ser detectado independentemente do bind.
- `detect_lan_ipv4()` deve ser executado/publicado mesmo quando o servidor estiver restrito a localhost.
- O runtime deve sempre publicar, quando disponível:
  - `host`: endereço usado para acesso local interno;
  - `bind_host`: endereço real de bind do servidor;
  - `lan_ip`: IPv4 real da máquina na LAN, mesmo se o bind atual for `127.0.0.1`;
  - `display_host`: preferencialmente `lan_ip` quando houver;
  - `url`: URL local interna;
  - `share_url`: URL LAN somente quando o servidor estiver realmente acessível pela LAN;
  - `scope`: refletir acessibilidade (`local` ou `lan`), não a capacidade de detectar o IP.
- O cabeçalho deve mostrar o **IPv4 real da máquina** quando ele existir, independentemente de `scope`.
- Exemplo:
  - bind local: `127.0.0.1:8080`;
  - IP real da máquina: `192.168.10.2`;
  - cabeçalho: **`Web: 192.168.10.2:8080`**.
- Se o servidor ainda estiver restrito a localhost, o diagnóstico/configuração deve deixar claro que o endereço foi detectado, mas o acesso LAN ainda não está habilitado; não usar `127.0.0.1` como identidade de rede do host.
- Se `web_lan_enabled=1`, usar o mesmo `lan_ip` detectado para `share_url` e acessibilidade LAN.
- Em instalações existentes, não depender de recriar o banco/configuração para que o IP real seja detectado.
- Adicionar teste cobrindo explicitamente:
  - bind `127.0.0.1`;
  - `detect_lan_ipv4() -> 192.168.10.2`;
  - runtime com `lan_ip=192.168.10.2`;
  - cabeçalho exibindo `192.168.10.2:8080`, mesmo com `scope=local`.
- Adicionar teste adicional:
  - bind `0.0.0.0`;
  - `lan_ip=192.168.10.2`;
  - `scope=lan`;
  - `share_url=http://192.168.10.2:8080`.
- **Critério de aceite:** em qualquer máquina com IPv4 LAN válido, o cabeçalho não deve usar `127.0.0.1` como endereço principal. O loopback pode continuar sendo usado internamente para a janela local, mas o usuário deve ver o IPv4 real do host.

## Implementado na v1.14.28 — Cabeçalho Web: mostrar IP LAN real, sem botão de copiar e sem `\n` literal

### 1) Endereço exibido continua incorreto

- **Falha confirmada na v1.14.27:** o cabeçalho continua exibindo **`Web local: 127.0.0.1:8080`** em vez do IPv4 real do host que está executando a aplicação.
- Exemplo esperado em uma máquina cujo IPv4 LAN seja `192.168.10.2`:
  - **`Web LAN: 192.168.10.2:8080`**
- Revisar novamente toda a cadeia:
  - `detect_lan_ipv4()`;
  - `LocalServerHandle.lan_host`;
  - `share_url`;
  - `scope`;
  - `runtime_info()`;
  - payload de `/api/status`;
  - `updateWebAccessStatus()` no frontend.
- O frontend não deve priorizar `localInfo.url`/`127.0.0.1` quando existir `share_url` ou `display_host` LAN válido.
- Quando o servidor estiver em modo LAN (`bind_host=0.0.0.0` ou IP LAN), o cabeçalho **nunca** deve mostrar `127.0.0.1` como endereço principal.
- Se o acesso LAN estiver habilitado e o host possuir IPv4 LAN válido, `scope` deve ser `lan` e o endereço exibido deve ser o IPv4 concreto da interface.
- Adicionar diagnóstico no log mostrando simultaneamente:
  - `bind_host`;
  - `host`;
  - `lan_host`;
  - `display_host`;
  - `url`;
  - `share_url`;
  - `scope`.
- Adicionar teste de regressão ponta a ponta simulando:
  - bind `0.0.0.0`;
  - LAN detectada `192.168.10.2`;
  - porta `8080`;
  - payload de `/api/status`;
  - renderização final do cabeçalho como **`Web LAN: 192.168.10.2:8080`**.

### 2) Remover botão de copiar endereço

- **Não deve existir botão de copiar URL** no cabeçalho.
- Remover `webAccessCopyButton` e todo o JavaScript/CSS associado à ação de cópia.
- O endereço Web no cabeçalho deve servir apenas como **indicador do endereço ativo**.
- Não é necessário abrir o navegador ao clicar no endereço.
- A abertura automática no navegador deve continuar sendo controlada exclusivamente pela opção já existente em **Configuração → “Abrir também no navegador ao iniciar”**.
- Quando essa opção estiver habilitada, a aplicação deve abrir também o navegador usando o endereço efetivamente ativo.
- Quando estiver desabilitada, a aplicação não deve abrir navegador automaticamente apenas por exibir o endereço no cabeçalho.

### 3) Texto literal `\n` aparece no cabeçalho

- **Falha visual confirmada:** há um texto literal **`\n`** visível no cabeçalho.
- Isso não é quebra de linha válida; é texto escapado inserido no HTML/template.
- Remover qualquer sequência literal `\n` do markup do cabeçalho.
- Adicionar teste que falhe se o HTML renderizado contiver `\\n` junto aos controles do cabeçalho.

### Critério de aceite geral

Em uma máquina com IPv4 LAN `192.168.10.2` e porta `8080`, com acesso Web LAN habilitado, o cabeçalho deve apresentar apenas algo equivalente a:

**`Web LAN: 192.168.10.2:8080`**

Sem botão de copiar, sem `127.0.0.1`, sem `0.0.0.0` e sem `\n` literal.

A opção **“Abrir também no navegador ao iniciar”** continua sendo a única responsável pela abertura automática da interface em navegador.


## Implementado na v1.14.27 — Windows 7 Legacy v1.14.26: Portable fecha ao iniciar e Setup abre versão anterior

### 1) Portable v1.14.26 inicia e fecha imediatamente

- **Falha observada em Windows 7:** o executável `PT2VHF_APRS_Client_Win7_Legacy_Portable_x64_v1.14.26.exe` começa a carregar e encerra logo em seguida, sem manter a aplicação aberta.
- Tratar como regressão crítica do runtime/shell desktop introduzida na v1.14.26.
- Investigar prioritariamente:
  - compatibilidade real do `pywebview 4.4.1` com Windows 7;
  - compatibilidade do `pythonnet 3.0.3`/CLR/.NET disponível no sistema;
  - renderer selecionado pelo `PT2VHF_WEBVIEW_GUI`;
  - dependências nativas incluídas pelo PyInstaller;
  - DLLs/runtime ausentes no Win7;
  - exceções durante import de `webview`/`clr`;
  - falha na criação da janela integrada;
  - encerramento indevido do backend após falha da shell;
  - comportamento do `console=False`, que pode ocultar a exceção real.
- O build Legacy não deve depender de um renderer ou runtime que apenas funcione no runner do GitHub/Windows Server e falhe no Windows 7 real.
- Adicionar um modo de diagnóstico que grave, antes de qualquer criação de janela:
  - versão do Windows;
  - arquitetura;
  - versão Python embarcada;
  - versão pywebview;
  - versão pythonnet;
  - runtime .NET/CLR detectado;
  - renderer solicitado;
  - renderer efetivamente iniciado;
  - exceção completa/traceback.
- Preservar o processo/backend em caso de falha da shell tempo suficiente para registrar diagnóstico e exibir mensagem compreensível ao usuário; não simplesmente encerrar.
- Avaliar renderer alternativo realmente compatível com Windows 7 caso EdgeChromium/WebView2 não seja suportado nessa plataforma.
- Se não existir shell embutida confiável em Win7 com o stack atual, priorizar uma solução desktop compatível de fato, em vez de manter uma dependência que só funciona no CI.

### 2) Setup v1.14.26 abre uma versão anterior

- **Falha observada:** após instalar a v1.14.26 pelo instalador Legacy, ao abrir o programa é iniciada uma versão anterior do PT2VHF APRS Client.
- Tratar separadamente como falha de empacotamento/instalação/atalho.
- Verificar:
  - qual executável foi realmente incluído dentro do Setup;
  - versão embutida no executável instalado;
  - caminho de instalação utilizado pelo Inno Setup;
  - coexistência de executáveis antigos no diretório;
  - nome do executável instalado;
  - destino do atalho do menu Iniciar/desktop;
  - comportamento do `[Files]` com `DestName`;
  - se o build do Setup está reutilizando um Portable antigo existente em `dist`;
  - ordem do pipeline e possibilidade de artefato obsoleto ser empacotado.
- O pipeline deve validar o executável **antes** de construir o Setup:
  - executar/inspecionar a versão embutida;
  - confirmar que corresponde exatamente à `VERSION`;
  - confirmar hash/mtime do arquivo recém-gerado;
  - impedir uso de artefato residual de build anterior.
- Limpar explicitamente diretórios `dist`, `build` e `dist-win7` antes do build Legacy.
- O instalador deve remover/substituir o executável anterior da instalação e nunca deixar dois binários concorrentes com atalhos diferentes.
- O atalho deve apontar exatamente para o executável v1.14.26 instalado no diretório Legacy.
- Após a instalação, a própria aplicação deve reportar a mesma versão do instalador.

### Testes obrigatórios

- Teste real em Windows 7 SP1 x64 para o Portable:
  - abrir;
  - manter processo ativo;
  - exibir janela;
  - backend permanecer funcional;
  - nenhuma saída prematura.
- Teste real em Windows 7 SP1 x64 para o Setup:
  - instalar sobre versão anterior;
  - abrir pelo atalho;
  - confirmar versão exibida = versão recém-instalada;
  - confirmar caminho do executável;
  - confirmar ausência de binário antigo sendo lançado.
- Adicionar smoke test de empacotamento que falhe se:
  - o executável Legacy produzido não contiver a versão corrente;
  - o Setup incluir binário de versão diferente;
  - o atalho apontar para nome/caminho diferente do executável recém-gerado.
- **Critério de aceite:** no Windows 7 real, tanto o Portable quanto o Setup da próxima release devem abrir e permanecer em execução. O Setup deve iniciar exatamente a versão recém-instalada, nunca uma versão anterior.

## Implementado na v1.14.26 — Windows 7 Legacy Setup: ao abrir, inicia o navegador em vez da aplicação desktop

- **Falha observada:** na versão **Windows 7 Legacy instalada (Setup)**, ao iniciar o PT2VHF APRS Client o executável abre o navegador com a interface Web em vez de abrir a aplicação desktop propriamente dita.
- Tratar como regressão específica do entrypoint/launcher do build Legacy instalado.
- Revisar o fluxo de inicialização entre `windows_legacy_app.py`, `windows_app.py`, PyInstaller spec e instalador Win7.
- A versão **Setup Win7 Legacy** deve abrir a aplicação como aplicativo desktop, com sua janela própria, comportamento equivalente ao cliente Windows normal dentro das limitações do runtime compatível com Windows 7.
- Não forçar `--browser` no entrypoint da versão instalada.
- O modo navegador deve ser utilizado somente quando:
  - o usuário solicitar explicitamente;
  - o ambiente desktop/WebView não estiver disponível e houver fallback documentado;
  - ou existir opção específica de execução em modo Web.
- Separar claramente os modos de inicialização:
  - **Win7 Legacy Setup:** desktop por padrão;
  - **Win7 Legacy Portable:** desktop por padrão;
  - **modo browser:** somente por argumento/configuração explícita ou fallback controlado.
- Se o Windows 7 não suportar o mesmo WebView usado nas versões modernas, implementar uma shell desktop compatível com Win7 ou outro mecanismo embutido compatível, em vez de simplesmente abrir o navegador externo como comportamento padrão.
- O navegador externo pode permanecer como fallback de emergência, mas nesse caso:
  - informar claramente ao usuário que houve fallback;
  - registrar a causa no diagnóstico;
  - não tratar esse comportamento como inicialização normal.
- Revisar atalhos criados pelo instalador para garantir que não incluam parâmetros como `--browser`.
- Revisar o nome/target do executável instalado para garantir que o Setup não esteja apontando para um launcher de teste.
- Adicionar diagnóstico de inicialização contendo:
  - modo detectado;
  - executável/entrypoint;
  - argumentos recebidos;
  - desktop shell disponível;
  - browser fallback acionado ou não;
  - motivo do fallback.
- Adicionar testes de regressão para:
  - Win7 Legacy Setup abrindo em modo desktop;
  - Win7 Legacy Portable abrindo em modo desktop;
  - ausência de `--browser` no atalho/linha de comando padrão;
  - browser somente quando solicitado explicitamente;
  - fallback controlado e diagnosticado quando a shell desktop não puder iniciar.
- **Critério de aceite:** ao iniciar o **PT2VHF APRS Client Win7 Legacy instalado via Setup**, deve abrir a janela da aplicação desktop. O navegador externo não deve ser aberto por padrão.

## Implementado na v1.14.26 — Windows 7 Legacy: atualização pelo próprio programa não funciona

- **Falha observada:** na versão **Windows 7 Legacy**, o mecanismo de atualização integrado não conclui a atualização pelo próprio programa. A falha foi confirmada também na edição **Win7 Legacy Portable**.
- Tratar como regressão específica do fluxo de update do build Legacy, separada do updater das versões Windows atuais.
- Revisar todo o ciclo de atualização no Windows 7:
  - detecção da nova Release;
  - identificação de que a instalação em execução é **Windows 7 Legacy**;
  - seleção do asset correto da Release;
  - download;
  - validação de tamanho/hash/digest;
  - criação e execução do helper de atualização compatível com Windows 7;
  - encerramento da aplicação;
  - substituição/instalação do binário;
  - reabertura automática;
  - limpeza de arquivos temporários;
  - rollback em caso de falha.
- O updater do build Legacy deve selecionar **exclusivamente** artefatos compatíveis com Windows 7, conforme o modo em execução:
  - Portable: `PT2VHF_APRS_Client_Win7_Legacy_Portable_x64_vX.Y.Z.exe`;
  - Setup: `PT2VHF_APRS_Client_Setup_Win7_Legacy_x64_vX.Y.Z.exe`.
- Nunca permitir que o Windows 7 Legacy baixe ou aplique automaticamente:
  - `PT2VHF_APRS_Client_Portable_x64_...`;
  - `PT2VHF_APRS_Client_Setup_x64_...`;
  - qualquer build produzido com runtime incompatível com Windows 7.
- Revisar `current_update_mode()`, `desired_asset_name()`, `select_asset()` e `install_supported()` para o modo Legacy.
- O modo `windows-legacy` não deve ficar permanentemente marcado como **não instalável** quando a atualização automática for oficialmente suportada.
- Implementar helper compatível com Windows 7, evitando dependências de PowerShell/Win32 APIs ausentes nessa plataforma quando houver risco de incompatibilidade.
- **Falha confirmada no Portable:** ao executar a versão `PT2VHF_APRS_Client_Win7_Legacy_Portable_x64`, a atualização pelo próprio aplicativo também não funciona.
- Para **Portable**:
  - baixar o novo executável Legacy;
  - validar;
  - preservar backup/rollback;
  - substituir o executável em uso após encerramento;
  - relançar a nova versão.
- Para **Setup**:
  - baixar o instalador Legacy;
  - validar;
  - executar o instalador em modo adequado;
  - preservar configurações e banco;
  - relançar a aplicação após sucesso.
- Durante o processo, exibir progresso e mensagens de erro reais; não fechar a aplicação silenciosamente se o helper não puder ser iniciado.
- Se não existir asset Legacy correspondente na Release, informar claramente **“Atualização para Windows 7 Legacy indisponível nesta versão”**, sem tentar outro asset.
- Registrar diagnóstico detalhado:
  - versão atual;
  - versão alvo;
  - update mode;
  - asset esperado;
  - asset encontrado;
  - URL;
  - caminho temporário;
  - hash/digest;
  - comando/helper executado;
  - exit code;
  - erro de instalação;
  - resultado do relançamento.
- Adicionar testes específicos para:
  - detecção correta de Windows 7 Legacy Portable;
  - detecção correta de Windows 7 Legacy Setup;
  - seleção exclusiva do asset Legacy;
  - recusa de assets Windows comuns;
  - download e validação;
  - aplicação Portable;
  - aplicação Setup;
  - rollback;
  - ausência de asset Legacy;
  - reabertura automática após atualização.
- **Critério de aceite:** em Windows 7 SP1 x64, tanto no **Setup** quanto no **Portable**, ao detectar uma nova Release que contenha o asset Legacy correspondente, o usuário deve conseguir clicar em atualizar e concluir todo o processo pelo próprio PT2VHF APRS Client, terminando com a nova versão aberta e os dados/configurações preservados. No Portable, o executável deve ser substituído com backup/rollback seguro e relançamento automático.

## Implementado na v1.14.26 — Menu superior/Web LAN: exibe 127.0.0.1 em vez do IPv4 real da rede

- **Falha observada:** o indicador Web no menu/barra superior está exibindo o endereço de loopback `127.0.0.1`, mesmo quando a máquina possui um endereço IPv4 válido na rede local, por exemplo `192.168.10.2`.
- O endereço mostrado ao usuário deve refletir o **IPv4 real da interface LAN utilizável por outros dispositivos da mesma rede**, e não o endereço interno de loopback.
- O endereço exibido no menu/barra superior deve ser **clicável**.
- Ao clicar no IP/URL, abrir o **navegador padrão do sistema operacional** exatamente no endereço e porta atualmente exibidos, por exemplo `http://192.168.10.2:8080`.
- A ação deve usar o URL efetivo publicado pelo runtime, incluindo eventual fallback automático de porta, sem reconstruir manualmente um endereço potencialmente diferente.
- Preservar a ação de copiar o URL, mas separar claramente **abrir no navegador** de **copiar endereço**, evitando comportamento ambíguo.
- Se o navegador não puder ser aberto, exibir erro não bloqueante e manter o URL disponível para cópia manual.
- **Acesso externo à máquina dentro da LAN:** quando o modo Web LAN estiver habilitado, garantir que o serviço esteja realmente acessível por outros dispositivos da mesma rede, e não apenas exibindo um IP correto na interface.
- O backend deve fazer bind em interface compatível com acesso LAN (`0.0.0.0` ou IP LAN selecionado), mantendo o acesso local funcionando.
- No Windows, detectar se a porta/execução está bloqueada pelo **Windows Defender Firewall** e oferecer fluxo controlado para criar a regra de entrada necessária para o executável/porta em uso.
- A regra de firewall deve:
  - ser criada somente com consentimento explícito do usuário;
  - ficar limitada ao perfil de rede adequado, preferencialmente **Privado**;
  - usar somente a porta TCP efetivamente utilizada pelo servidor;
  - evitar abertura ampla e permanente de portas desnecessárias;
  - ser atualizada/removida quando a porta ou configuração mudar, quando tecnicamente seguro.
- Em Linux, detectar firewall comum quando possível (por exemplo UFW/firewalld) e informar objetivamente qual porta TCP precisa ser liberada; não alterar regras sem confirmação explícita.
- Em macOS, detectar bloqueio do firewall/aplicativo quando possível e orientar a autorização correspondente sem desabilitar proteções globais.
- **Antivírus/EDR de terceiros:** não assumir que é possível liberar programaticamente todos os produtos. Detectar falha de acesso quando viável e apresentar diagnóstico indicando que antivírus, EDR ou política corporativa pode estar bloqueando o executável ou a porta.
- Implementar um **teste de acessibilidade LAN** após habilitar o recurso:
  - confirmar bind na interface LAN;
  - confirmar porta em escuta;
  - confirmar URL publicado;
  - informar estado do firewall quando detectável;
  - indicar claramente **“Acessível na LAN”** ou **“Bloqueado/Não confirmado”**.
- O diagnóstico deve diferenciar pelo menos:
  - bind incorreto;
  - porta não escutando;
  - firewall do SO bloqueando;
  - regra ausente;
  - endereço LAN inválido;
  - conflito de porta;
  - bloqueio externo não identificável, incluindo antivírus/EDR.
- Não desabilitar firewall, antivírus, Defender ou qualquer outra proteção de segurança como forma de resolver o acesso.
- Não habilitar automaticamente exposição à Internet/WAN, port forwarding, UPnP ou abertura de roteador. O escopo padrão continua sendo **somente a rede local confiável**.
- Revisar a integração entre `local_server.detect_lan_ipv4()`, o estado/runtime publicado pelo backend e `updateWebAccessStatus()` no frontend para garantir que o campo exibido venha do endereço LAN detectado.
- Diferenciar claramente:
  - **Web local:** `http://127.0.0.1:porta` somente quando o servidor estiver restrito à própria máquina;
  - **Web LAN:** `http://192.168.x.x:porta` quando o acesso pela rede local estiver habilitado.
- Quando o modo LAN estiver habilitado, o servidor deve escutar em interface apropriada (`0.0.0.0` ou interface LAN selecionada), mas o usuário **nunca deve ver `0.0.0.0` como URL**; deve ver o IPv4 concreto da interface.
- A detecção do IPv4 LAN deve ignorar:
  - `127.0.0.0/8`;
  - `0.0.0.0`;
  - interfaces desconectadas;
  - adaptadores virtuais/VPN sem rota LAN útil quando existir uma interface física válida.
- Em hosts com múltiplas interfaces, priorizar o endereço associado à rota padrão/saída efetiva da rede local; se houver mais de um candidato válido, escolher de forma determinística e registrar os candidatos no diagnóstico.
- Se a detecção automática falhar, manter o acesso local funcionando e sinalizar que o endereço LAN não pôde ser determinado, em vez de apresentar `127.0.0.1` como se fosse compartilhável.
- Adicionar diagnóstico contendo `bind_host`, `display_host`, `lan_host`, porta, interface/candidato selecionado e motivo da seleção.
- Adicionar testes de regressão cobrindo:
  - máquina com IP `192.168.10.2` e bind LAN;
  - fallback sem Internet, usando resolução/local interfaces;
  - múltiplos adaptadores;
  - presença de VPN/VirtualBox/Hyper-V;
  - ausência de IPv4 LAN válido;
  - atualização correta do cabeçalho após mudança de modo localhost ↔ LAN.
- **Critério de aceite:** em uma máquina com IPv4 LAN `192.168.10.2` e acesso LAN habilitado, o menu superior deve exibir algo como **Web LAN: http://192.168.10.2:porta**; ao clicar nesse endereço, o navegador padrão deve abrir exatamente esse URL. O serviço deve estar efetivamente em escuta na LAN e, quando necessário e autorizado, a regra de firewall do sistema deve permitir a conexão a partir de outro dispositivo da mesma rede. Se antivírus/EDR ou outra política impedir o acesso, a aplicação deve diagnosticar e informar a causa provável sem desabilitar proteções. O endereço `127.0.0.1` só pode aparecer quando o acesso estiver efetivamente restrito à própria máquina.

## Implementado na v1.14.25 — Windows 7: falha ao iniciar por ausência de `api-ms-win-core-path-l1-1-0.dll`

- **Falha observada em Windows 7:** ao tentar iniciar `PT2VHF_APRS_Client.exe`, o sistema informa que o programa não pode ser iniciado porque está faltando `api-ms-win-core-path-l1-1-0.dll`.
- Tratar o problema como **incompatibilidade de runtime/build com Windows 7**, e não orientar o usuário a baixar/copiar DLL avulsa de sites de terceiros.
- Revisar a cadeia completa de empacotamento do Windows para identificar qual componente passou a exigir APIs não disponíveis no Windows 7:
  - versão do Python usada no build;
  - versão do PyInstaller/Nuitka ou empacotador equivalente;
  - WebView/runtime;
  - bibliotecas nativas e wheels;
  - dependências que tenham abandonado suporte ao Windows 7;
  - instalador e bootstrap/update helper.
- Avaliar duas estratégias e documentar a decisão:
  1. **Build legado dedicado para Windows 7**, congelado em runtime e dependências ainda compatíveis; ou
  2. declarar oficialmente Windows 7 como não suportado e fazer o instalador bloquear a instalação com mensagem clara, antes de copiar/abrir o executável.
- Se a opção for manter suporte ao Windows 7:
  - gerar artefato específico, claramente identificado como **Windows 7 / Legacy**;
  - usar runtime Python compatível com Windows 7 e versões de dependências verificadas;
  - evitar dependência de `api-ms-win-core-path-l1-1-0.dll` ausente no sistema;
  - validar funcionamento do cliente, APRS-IS, mapa/WebView, TNC/KISS, SQLite, atualizador, exportações e demais recursos essenciais;
  - validar tanto **Setup** quanto **Portable**, se ambos forem oferecidos;
  - impedir que o atualizador substitua automaticamente o build legado por um build incompatível.
- Se a opção for não manter suporte:
  - detectar Windows 7 no instalador e no bootstrap;
  - exibir mensagem amigável informando a versão mínima suportada;
  - impedir instalação/execução parcialmente quebrada;
  - documentar claramente os sistemas operacionais suportados na Release, README e Manual.
- Adicionar teste de compatibilidade/CI que impeça regressão acidental na versão mínima do Windows.
- **Critério de aceite:** em Windows 7, o usuário não deve receber o erro genérico de DLL ausente. O aplicativo deve **funcionar em um build legado oficialmente suportado** ou **interromper a instalação de forma controlada e explicar claramente a incompatibilidade**.

## Implementado na v1.14.25 — Internacionalização: auditoria completa de todas as traduções da aplicação

- Revisar **todas as partes da aplicação** nos dez idiomas suportados: **PT-BR, EN, ES, FR, DE, IT, JA, PL, NL e ZH-CN**.
- Corrigir casos em que, após selecionar um idioma diferente de Inglês, partes da interface continuam aparecendo em **Inglês** por fallback indevido, ausência de chave ou tradução incompleta.
- A revisão deve cobrir toda a interface, inclusive conteúdos que hoje podem escapar do catálogo principal:
  - menu/barra superior;
  - Mapa, controles, camadas, filtros, legendas, tooltips e popups;
  - Mensagens, conversas, boletins, grupos e mensagens agendadas;
  - Estações e ações contextuais;
  - Estatísticas, rankings, Recordes RF, indicadores de processamento e mensagens de erro;
  - Configuração, todos os grupos, campos, opções, dicas e validações;
  - TNC/RF, diagnóstico e tráfego bruto;
  - atualização automática, changelog e avisos de nova versão;
  - Ajuda e Sobre;
  - diálogos, modais, confirmações, toasts e mensagens de sucesso/erro;
  - textos produzidos dinamicamente pelo JavaScript;
  - textos retornados pelo backend e exibidos diretamente no frontend;
  - componentes auxiliares em `v190.js`, `v110.js`, `v111.js`, `v142.js`, `v1818.js`, `tnc.js` e demais módulos;
  - textos criados após troca de idioma sem reiniciar a aplicação.
- Não considerar a tradução completa apenas porque o arquivo de idioma possui a mesma **quantidade de entradas** que outro catálogo. A auditoria deve validar **chave por chave e componente por componente**, incluindo strings fora dos catálogos atuais.
- Identificar strings hardcoded em HTML, JavaScript e Python que possam chegar à interface sem passar pelo mecanismo de tradução.
- Eliminar o comportamento atual em que idiomas como Alemão, Italiano, Japonês, Polonês, Holandês ou Chinês podem herdar silenciosamente o texto em **Inglês** quando não existe tradução específica.
- Definir fallback de segurança apenas para situações excepcionais:
  - primeiro, idioma selecionado;
  - depois, uma tradução explicitamente definida como fallback;
  - nunca usar fallback para mascarar uma chave ausente nos testes/auditoria.
- Durante desenvolvimento/teste, uma chave ausente deve ser detectável pela auditoria, mesmo que em produção exista um fallback para evitar campo vazio.
- Revisar também traduções interpoladas, plurais, datas, números, unidades, percentuais e mensagens formadas por concatenação, evitando frases parcialmente traduzidas.
- Preservar sem tradução apenas elementos que tecnicamente devam permanecer invariáveis, como:
  - indicativos;
  - nomes/protocolos APRS, APRS-IS, AX.25, KISS, TNC, RF;
  - ACK/REJ;
  - URLs;
  - nomes oficiais de software/serviços;
  - identificadores técnicos quando sua tradução prejudicar a compreensão.
- Verificar terminologia radioamadora natural em cada idioma, evitando tradução literal inadequada de termos como **digipeater, iGate, beacon, path, heard, tracklog e RF route**.
- Ampliar `tools/i18n_audit.py` para:
  - localizar strings visíveis fora do mecanismo i18n;
  - comparar todas as chaves em todos os dez idiomas;
  - detectar traduções ausentes;
  - detectar entradas vazias;
  - detectar fallback silencioso para Inglês;
  - detectar chaves órfãs/não utilizadas;
  - emitir relatório por idioma e por arquivo/componente;
  - falhar o pipeline em regressões de cobertura.
- Adicionar um teste automatizado de troca de idioma que percorra os principais componentes da interface e confirme que, ao selecionar **DE/IT/JA/PL/NL/ZH-CN**, textos conhecidos não permanecem em Inglês.
- Incluir regressões específicas para textos criados **depois** da troca de idioma, como popups, toasts, rankings, indicadores de processamento e diálogos.
- **Critério de aceite:** ao selecionar qualquer um dos dez idiomas, toda a interface visível deve permanecer coerente com o idioma escolhido, sem blocos residuais em Inglês por ausência de tradução, salvo termos técnicos explicitamente definidos como invariáveis.

## Implementado na v1.14.25 — Barra superior: simplificar controles, Beacon compacto e endereço Web LAN

- Reorganizar a **barra/menu superior** para reduzir poluição visual e liberar espaço para informações operacionais mais úteis.
- **Remover da barra superior o controle de tema Claro/Escuro**.
  - Mover a seleção de tema para **Configuração → Aparência / Aplicação**.
  - Manter as opções atuais de tema e sua persistência.
  - A mudança de tema deve continuar sendo aplicada imediatamente, sem exigir reinício.
- **Substituir o botão textual “Enviar Beacon” por um controle menor e compacto com ícone**.
  - Usar um ícone intuitivo de transmissão/beacon, com tooltip **“Enviar Beacon”**.
  - Preservar exatamente a mesma ação e validações do botão atual.
  - Exibir feedback visual de clique/envio sem ocupar a largura de um botão textual grande.
  - Manter acessibilidade por `aria-label`/tooltip e foco por teclado.
- **Adicionar à barra superior o endereço Web de acesso pela rede**, em posição visível porém compacta.
  - Exemplo: **Web: 192.168.1.50:5000**.
  - Quando o acesso LAN estiver habilitado, mostrar o **IPv4 LAN real** da máquina e a **porta efetivamente usada** pelo servidor.
  - O endereço deve ser clicável e permitir **copiar o URL completo** para a área de transferência.
  - Tooltip sugerido: **“Abrir/copiar endereço para acesso por outro dispositivo da rede”**.
  - Em caso de fallback de porta, atualizar automaticamente o endereço mostrado.
  - Quando o servidor estiver restrito a localhost, deixar isso explícito, por exemplo **Web local: 127.0.0.1:5000**, sem induzir o usuário a acreditar que já está acessível externamente.
  - Com acesso LAN ativo, exibir algo como **Web LAN: http://192.168.x.x:porta**.
- O endereço exibido na barra deve usar o mecanismo definido no backlog de **acesso Web pela rede local**, incluindo suporte a Windows, Linux, macOS e execução em VM.
- Não confundir “acesso externo” com exposição direta à Internet/WAN:
  - por padrão, o recurso deve significar **acesso externo à máquina, dentro da LAN**;
  - exposição à Internet deve permanecer fora do comportamento automático e exigir configuração de segurança específica.
- Revisar o layout da barra superior após essas mudanças para evitar truncamento em resoluções menores e em idiomas com textos mais longos.
- Adicionar testes de regressão garantindo:
  - ausência do controle Claro/Escuro na barra superior;
  - presença e funcionamento do tema em Configuração;
  - Beacon compacto com ícone e mesma ação do botão anterior;
  - endereço Web correto conforme modo localhost/LAN;
  - atualização após mudança de porta;
  - cópia do URL;
  - comportamento responsivo da barra em resoluções menores.
- **Critério de aceite:** a barra superior deve ficar mais compacta, sem o seletor Claro/Escuro, com um **ícone pequeno para Beacon** e com o **endereço Web LAN visível e copiável** quando o acesso pela rede estiver habilitado.

## Implementado na v1.14.25 — Menu superior: exibir endereço de acesso pela rede local

- Incluir no **menu/barra superior** uma indicação clara do endereço Web da aplicação para acesso por outros dispositivos da mesma rede local.
- Exibir o endereço no formato, por exemplo:
  - **Web: http://192.168.1.50:5000**
  - usar automaticamente o **IPv4 LAN real da máquina** e a **porta efetivamente reservada** pelo servidor local.
- O endereço deve ser clicável, com ação para **copiar para a área de transferência** e, quando aplicável, abrir no navegador.
- O indicador deve refletir mudanças de porta decorrentes do fallback automático do servidor.
- Não mostrar apenas `127.0.0.1`/`localhost` como endereço compartilhável, pois esses endereços funcionam somente na própria máquina.
- Para que o endereço exibido seja realmente acessível por outro computador, tablet ou celular da LAN, implementar um modo de **acesso pela rede local**:
  - manter o comportamento atual restrito a localhost como opção segura padrão, ou disponibilizar uma opção explícita em **Configuração → Aplicação/Web** para habilitar acesso LAN;
  - quando habilitado, fazer o servidor escutar em interface apropriada (`0.0.0.0` ou endereço LAN selecionado), preservando o acesso local da janela integrada;
  - detectar e exibir o endereço LAN utilizável, nunca `0.0.0.0` como URL para o usuário.
- Mostrar o estado no menu superior, por exemplo:
  - **Web local: 127.0.0.1:5000** quando restrito à própria máquina;
  - **Web LAN: 192.168.1.50:5000** quando o compartilhamento em rede estiver habilitado.
- Adicionar tooltip/ajuda curta explicando que o endereço LAN pode ser aberto em outro dispositivo conectado à mesma rede.
- Prever aviso de firewall do sistema operacional quando necessário e explicar que a porta precisa estar liberada para conexões de entrada.
- Segurança:
  - o acesso LAN deve ser **opt-in**, não habilitado silenciosamente;
  - não expor automaticamente a aplicação à Internet/WAN;
  - deixar claro que o recurso é destinado à **rede local confiável**;
  - avaliar autenticação/token de acesso antes de permitir exposição além da LAN.
- O recurso deve funcionar em **Windows, Linux e macOS**, inclusive quando o cliente estiver executando em máquina virtual.
- Adicionar testes para:
  - detecção do IPv4 LAN;
  - uso da porta real após fallback;
  - persistência da opção de acesso LAN;
  - bind localhost × LAN;
  - atualização do endereço exibido no menu;
  - cópia do URL;
  - comportamento sem interface de rede válida.
- **Critério de aceite:** com o acesso LAN habilitado, o usuário deve enxergar no menu superior um URL como **http://192.168.x.x:porta** e conseguir abrir esse endereço em outro dispositivo da mesma rede sem precisar descobrir manualmente IP e porta.

## Implementado na v1.14.25 — Sobre: adicionar PY2FDG / Fábio aos colaboradores

- Adicionar **PY2FDG — Fábio** à seção **Colaboradores** da aba **Sobre**.
- Exibir o indicativo em destaque e o nome ao lado, seguindo o padrão visual já usado para os demais colaboradores.
- Registrar sua contribuição ao projeto, especialmente pelas sugestões relacionadas a **mensagens agendadas/programadas** e melhorias de usabilidade na interface de Mensagens.
- Manter a lista de colaboradores organizada e legível nos idiomas suportados.
- **Critério de aceite:** ao abrir a aba **Sobre**, a seção **Colaboradores** deve incluir **PY2FDG — Fábio**.

## Implementado na v1.14.24 — Estatísticas: indicador de processamento com barra de progresso real de 0 a 100%

- Na aba **Estatísticas**, durante operações pesadas de indexação, reconstrução da topologia e cálculo de **Recordes/Enlaces RF**, substituir o simples indicador indefinido por um feedback mais completo:
  - manter o **relógio/spinner animado**;
  - adicionar uma **barra de progresso de 0% a 100%**;
  - exibir o percentual numérico e a etapa atual do processamento.
- O progresso deve representar **trabalho efetivamente concluído**, e não uma animação baseada apenas em tempo.
- Dividir o cálculo em fases mensuráveis, por exemplo:
  1. **Preparando dados / indexando histórico**;
  2. **Carregando nós e enlaces**;
  3. **Validando evidências e coordenadas históricas**;
  4. **Calculando alcançabilidade multi-hop**;
  5. **Ordenando e consolidando Recordes RF**;
  6. **Atualizando a interface**.
- Cada fase deve informar ao frontend pelo menos:
  - nome/descrição da etapa;
  - quantidade concluída;
  - quantidade total conhecida;
  - percentual global;
  - tempo decorrido;
  - quando viável, quantidade de nós, enlaces ou candidatos já processados.
- Exemplo visual:
  - **Calculando enlaces RF… 42%**
  - `████████░░░░░░░░░░░░ 42%`
  - **Validando 183 de 436 enlaces**
- Para o cálculo de Recordes RF, usar como unidades reais de progresso os lotes/itens efetivamente processados pelo algoritmo, como:
  - nós de origem concluídos;
  - arestas/hops indexados;
  - candidatos de rota avaliados;
  - pares de extremidades consolidados.
- Quando o total ainda não for conhecido, iniciar em modo **indeterminado** com spinner. Assim que o backend conhecer o universo de trabalho, converter para progresso determinado de 0 a 100%.
- O percentual não pode retroceder durante uma mesma execução, exceto quando uma nova execução for explicitamente iniciada.
- Não deixar a barra parada em **100%** enquanto ainda houver trabalho importante pendente; 100% deve significar resultado pronto para ser aplicado na interface.
- Se houver cache válido:
  - indicar algo como **“Carregando resultado em cache…”**;
  - concluir rapidamente até 100%;
  - não simular etapas de cálculo que não ocorreram.
- Se o cálculo ultrapassar o tempo esperado, a interface deve continuar mostrando progresso real e a etapa atual, em vez de simplesmente parecer travada.
- Em caso de erro:
  - interromper a barra;
  - mostrar a etapa em que ocorreu a falha;
  - preservar o último ranking válido quando existir;
  - permitir **Tentar novamente**.
- Em caso de cancelamento/troca de período:
  - cancelar ou invalidar a execução anterior;
  - zerar/iniciar uma nova barra para a nova solicitação;
  - impedir que progresso antigo atualize a tela da nova execução.
- Evitar polling agressivo. Preferir um mecanismo de progresso dedicado e leve, por exemplo:
  - job de processamento com `job_id`;
  - endpoint de status/progresso;
  - SSE/WebSocket quando apropriado;
  - ou polling moderado do status do job.
- O backend deve manter estado de progresso separado por execução/período, evitando misturar progresso de **24 h**, **7 dias** e **Completo**.
- Integrar o progresso ao mecanismo global de processamento já existente, mas a aba Estatísticas deve poder mostrar também uma **barra contextual próxima de “Recordes RF observados — maiores distâncias”**.
- A barra deve funcionar também no período **Completo**, inclusive com banco grande e cálculo multi-hop histórico.
- Adicionar regressões garantindo:
  - início em 0% ou modo indeterminado;
  - atualização monotônica;
  - transição de fases;
  - conclusão em 100%;
  - cancelamento ao mudar período;
  - recuperação após erro;
  - cache concluindo rapidamente;
  - duas execuções concorrentes sem mistura de progresso.
- **Critério de aceite:** ao atualizar Estatísticas e iniciar a reconstrução/cálculo dos enlaces, o usuário deve ver claramente que o aplicativo continua trabalhando, qual etapa está sendo executada e um progresso real de **0% a 100%** até a conclusão do ranking.

## Implementado na v1.14.24 — Estatísticas: ranking de Recordes RF fica indisponível

- **Regressão observada na v1.14.23:** a seção **“Recordes RF observados — maiores distâncias”** pode deixar de exibir o ranking e apresentar apenas a mensagem **“Recordes RF temporariamente indisponíveis; as demais estatísticas continuam válidas.”**
- Tratar a indisponibilidade como falha do cálculo/carregamento dos Recordes RF, não como ausência legítima de dados quando existem enlaces/rotas históricos no banco.
- Investigar separadamente as etapas:
  - chamada do endpoint dedicado de Recordes RF;
  - timeout do frontend e do backend;
  - construção do grafo RF histórico;
  - cache/single-flight introduzidos nas versões recentes;
  - exceções durante cálculo de alcançabilidade multi-hop;
  - serialização do payload;
  - fallback para o último resultado válido.
- Registrar no log de diagnóstico a causa real da indisponibilidade, incluindo exceção, duração do cálculo, período solicitado, quantidade de nós/arestas/eventos considerados e se houve timeout.
- A interface não deve permanecer indefinidamente em **“temporariamente indisponíveis”** após uma falha transitória:
  - se existir um último resultado válido para o mesmo período, mantê-lo visível e sinalizar que está desatualizado;
  - se não existir cache válido, permitir nova tentativa automática e também nova tentativa ao clicar em **Atualizar estatísticas**;
  - quando o cálculo subsequente funcionar, substituir automaticamente o estado de erro pelo ranking.
- O endpoint de Recordes RF deve retornar erro estruturado e diagnóstico suficiente quando falhar, sem converter exceção em lista vazia nem em zeros.
- Garantir que o período **Completo** continue capaz de calcular o ranking mesmo com banco grande; otimização não pode eliminar rotas multi-hop históricas nem tornar o cálculo permanentemente indisponível.
- Adicionar regressões para:
  - primeira carga com ranking válido;
  - timeout seguido de recuperação;
  - exceção seguida de recuperação;
  - reutilização do último resultado válido;
  - cálculo no período Completo com grande quantidade de eventos;
  - atualização concorrente sem deadlock ou starvation do single-flight/cache.
- **Critério de aceite:** havendo dados RF válidos no banco, a seção **Recordes RF observados — maiores distâncias** deve voltar a exibir o ranking; uma falha transitória pode gerar aviso, mas não deve apagar o último resultado válido nem deixar o ranking permanentemente indisponível.

## Implementado na v1.14.23 — Idiomas: adicionar Alemão, Italiano, Japonês, Polonês, Holandês e Chinês

- Expandir os idiomas disponíveis do PT2VHF APRS Client além de **Português, Inglês, Espanhol e Francês**.
- Adicionar:
  - **Alemão (de-DE)**;
  - **Italiano (it-IT)**;
  - **Japonês (ja-JP)**;
  - **Polonês (pl-PL)**;
  - **Holandês (nl-NL)**;
  - **Chinês simplificado (zh-CN)**.
- Prioridade sugerida para os três idiomas adicionais:
  - **Japonês** — comunidade radioamadora muito relevante e uso amplo de APRS/JAPRS;
  - **Polonês** — forte presença de radioamadores e infraestrutura APRS na Europa Central;
  - **Holandês** — comunidade ativa e boa cobertura APRS nos Países Baixos/Benelux.
- Incluir todos os novos idiomas no seletor de idioma da barra superior, mantendo o padrão atual de nome/bandeira.
- Traduzir integralmente:
  - menus e abas;
  - botões e tooltips;
  - mensagens de status;
  - diálogos e confirmações;
  - erros e avisos;
  - configurações;
  - Estatísticas;
  - análise de rotas RF;
  - Mapa e camadas;
  - TNC/RF;
  - atualização automática/changelog;
  - Ajuda/Sobre;
  - mensagens do indicador global de processamento.
- Não deixar textos residuais em Português/Inglês quando um dos novos idiomas estiver selecionado, exceto termos técnicos/indicativos que devam permanecer invariáveis.
- Preservar termos técnicos de radioamadorismo quando a tradução literal piorar a compreensão; usar terminologia comum da comunidade local para APRS, digipeater, iGate, beacon, path, TNC, RF, ACK/REJ etc.
- Atualizar o mecanismo de auditoria de traduções para considerar **de-DE, it-IT, ja-JP, pl-PL, nl-NL e zh-CN** como idiomas suportados.
- Adicionar testes de cobertura garantindo que:
  - todas as chaves existentes tenham tradução nos dez idiomas;
  - não existam chaves órfãs;
  - não haja fallback silencioso para Português/Inglês em componentes principais;
  - troca de idioma continue funcionando sem reiniciar o aplicativo quando já suportado;
  - caracteres Unicode do Japonês e do Chinês sejam renderizados corretamente.
- Revisar layout para textos mais longos em Alemão e para fontes/caracteres CJK em Japonês e Chinês, evitando truncamento de botões, menus e painéis.
- **Critério de aceite:** o aplicativo deve operar integralmente nos dez idiomas — PT, EN, ES, FR, DE, IT, JA, PL, NL e ZH-CN — com cobertura equivalente às traduções atuais.

## Implementado na v1.14.23 — Análise de rota RF: desenhar também os hops inferidos até o destino final

- **Regressão observada na v1.14.22:** a análise textual da rota inclui o destino final **PY4RC-15**, porém o destaque amarelo no mapa não chega até ele.
- Caso de referência da captura:
  - origem: **PP1GEC-10**;
  - destino: **PY4RC-15**;
  - rota exibida: **PP1GEC-10 → CERD → PP1MSC-15 → PU1PZP-15 → PY1EU-10 → PY1MRG-15 → PY4RC-15**;
  - último hop: **PY1MRG-15 → PY4RC-15**, classificado como **RF inferido do path**, aproximadamente **203,1 km**;
  - o painel lateral contabiliza o hop e inclui PY4RC-15 como destino, mas a linha destacada no mapa termina antes dele.
- A visualização da rota deve ser consistente com a rota calculada: **todo hop presente em `route.edges` deve ser desenhado**, inclusive hops com `evidence_level = inferred`, desde que tenham sido aceitos pelo motor como parte válida da rota.
- Não confundir a regra de “não mostrar hop inferido longo sem cadeia sustentada” com a renderização de um hop inferido que **já foi aceito e incluído explicitamente na rota calculada**.
- O mapa deve destacar o segmento **PY1MRG-15 → PY4RC-15** usando as coordenadas históricas associadas à evidência selecionada para esse hop.
- O nó de destino final deve permanecer visualmente incluído no foco da rota, mesmo quando:
  - o último hop é inferido;
  - o marcador da estação está oculto por filtro;
  - a posição atual difere da posição histórica usada pela evidência;
  - a rota foi reconstruída por alcançabilidade histórica.
- Revisar especialmente:
  - `rfRouteAllowedPairs()`;
  - `routeEvidenceByPair`;
  - filtros de `eligible_edges`;
  - exclusão de hops inferidos por distância;
  - criação/atualização das `topologyLines`;
  - geometria escolhida entre aresta agregada e `route.edges`;
  - `fitRfRouteBounds()` e os marcadores exclusivos da rota.
- Quando a rota ativa estiver em modo de análise/foco, a geometria de `route.edges` deve prevalecer sobre filtros genéricos da topologia para garantir que **a rota exibida no painel e a rota desenhada no mapa sejam idênticas**.
- Adicionar regressão específica com o caso:
  - rota com 6 hops;
  - último hop inferido;
  - destino final PY4RC-15;
  - verificar que o mapa contém o segmento final e que o bounding/foco inclui o destino.
- **Critério de aceite:** se o painel mostrar `... → PY1MRG-15 → PY4RC-15`, o mapa deve obrigatoriamente desenhar também **PY1MRG-15 → PY4RC-15** e incluir PY4RC-15 no destaque da rota.

## Implementado na v1.14.23 — Estatísticas: remover a barra de rolagem interna remanescente

- **Regressão confirmada na v1.14.22:** a aba **Estatísticas** ainda exibe um bloco interno com **barra de rolagem vertical própria**, apesar da correção anterior da v1.14.21.
- A captura de tela mostra claramente uma segunda barra de rolagem dentro da área de conteúdo da aba, à direita dos cartões/rankings, além da rolagem principal da janela.
- Remover qualquer contêiner interno da aba Estatísticas que esteja impondo `height`, `max-height`, `overflow-y: auto`, `overflow-y: scroll`, `overflow: auto` ou regra equivalente.
- A aba inteira deve funcionar como **um único fluxo vertical**, usando **somente a barra de rolagem principal da aplicação/janela**.
- O conteúdo de **Recordes RF**, atividade/interações, rankings, software/dispositivos, anomalias, digipeaters, iGates e demais seções deve expandir naturalmente no documento.
- Verificar também wrappers herdados ou estilos responsivos que possam reintroduzir scroll interno apenas em determinadas resoluções/alturas de tela.
- Não mascarar o problema apenas ocultando a scrollbar com CSS; o contêiner deve deixar de ser uma área de scroll independente.
- Preservar o indicador global **“Calculando recordes RF…”** e o carregamento assíncrono sem criar um viewport interno.
- Adicionar regressão de frontend/CSS que garanta que os contêineres principais de Estatísticas não tenham rolagem vertical independente.
- **Critério de aceite:** na aba Estatísticas, independentemente do tamanho da janela, deve existir apenas uma barra vertical de rolagem para percorrer todo o conteúdo da página.

## Implementado na v1.14.22 — Mapa: filtros de entidades não ocultam enlaces

- Ao desmarcar estações, objetos, digipeaters, iGates ou subtipos no menu **Ver**, ocultar apenas os respectivos marcadores/entidades.
- Manter os enlaces RF e APRS-IS visíveis mesmo quando uma ou ambas as extremidades estiverem ocultas.
- A linha só deve desaparecer quando a própria camada **Enlaces RF** ou **Enlaces iGate / APRS-IS** for desativada, ou quando o período selecionado excluir a evidência.
- Filtros visuais não podem alterar o grafo, o ranking, os Recordes RF nem a contagem histórica.

## Implementado na v1.14.22 — Windows: usar a arte APRS como ícone da barra de tarefas

- Usar a imagem APRS fornecida pelo usuário como fonte do ícone do aplicativo no Windows.
- Gerar o `.ico` em múltiplas resoluções a partir da arte adaptada.
- Aplicar ao executável, Portable, instalador, barra de tarefas, Alt+Tab e tray quando aplicável.
- Definir AppUserModelID próprio para melhorar a associação do ícone e o agrupamento da janela no Windows.

## Implementado na v1.14.22 — Ranking de enlaces: voltar a considerar rotas de alcançabilidade com múltiplos hops

- Corrigir regressão do ranking/Recordes RF: atualmente estão predominando ou aparecendo apenas **enlaces únicos (1 hop)**, enquanto rotas compostas com **múltiplos hops** deixaram de aparecer como deveriam.
- O objetivo do ranking é medir **alcançabilidade RF entre as extremidades**, não apenas listar arestas físicas individuais.
- Uma cadeia historicamente válida como **A → B → C → D** deve poder gerar um registro/ranking de **A ↔ D via B/C**, mesmo que cada hop tenha sido observado em momentos diferentes, respeitando as regras espaço-temporais já definidas.
- Manter explicitamente os intermediários da rota no resultado; nunca colapsar a cadeia em um falso enlace RF direto A ↔ D.
- Ordenar o ranking pela **distância geográfica entre as estações extremas** quando o objetivo for “maiores alcances”, mantendo como informação complementar:
  - quantidade de hops;
  - sequência completa dos nós;
  - soma das distâncias dos hops;
  - evidência/timestamp de cada hop;
  - classificação da rota como observada no mesmo pacote, contemporânea ou alcançabilidade histórica.
- Deduplicar por par de extremidades, mas permitir abrir/ver as alternativas de rota para o mesmo par quando existirem.
- O algoritmo de ranking deve explorar a conectividade multi-hop do grafo até o limite configurado e não encerrar a análise apenas nas arestas adjacentes ao nó de origem.
- Garantir que a otimização/caching introduzida para Estatísticas não transforme o ranking em simples lista de arestas.
- Adicionar regressões com rotas de 2, 3, 4 e mais hops, incluindo malhas com caminhos alternativos e nós móveis.

## Implementado na v1.14.22 — Topologia histórica: enlaces já observados não podem desaparecer no período Completo

- Investigar e corrigir enlaces históricos que existiam anteriormente e deixaram de aparecer após as mudanças recentes de topologia/rotas.
- Caso de referência informado: havia um enlace/rota ligando a região de **Goiânia a Caldas Novas** e ele deixou de aparecer.
- No período **Completo**, todo enlace RF válido já observado deve continuar disponível enquanto os dados correspondentes existirem no banco e a retenção configurada não os tiver removido.
- Nó offline ou sem transmissão recente não deve remover automaticamente seu enlace histórico.
- Separar claramente:
  - **enlace histórico conhecido**;
  - **enlace ativo/recente**;
  - **enlace atualmente visível pelo filtro de período**.
- O estado ativo/inativo deve alterar a aparência, não apagar o fato histórico.
- Verificar especialmente se a perda ocorre por:
  - ausência de coordenada histórica após migração;
  - filtros de `topology_events`;
  - descarte de eventos antigos na construção do grafo espaço-temporal;
  - retenção de banco;
  - deduplicação;
  - cache;
  - regras para hops inferidos;
  - limite de hops/expansões;
  - ranking progressivo de Recordes RF.
- Quando houver `topology_edges` histórico válido mas eventos detalhados incompletos/legados, preservar o enlace como evidência histórica legada em vez de simplesmente descartá-lo, deixando explícita a qualidade da evidência.
- Adicionar regressão específica com um enlace antigo válido que permanece no ranking/topologia após os nós ficarem offline e após reiniciar/atualizar o aplicativo.
- **Critério de aceite:** com período Completo, um enlace válido anteriormente armazenado continua disponível para análise até que o usuário efetivamente apague ou retenha esses dados.

## Implementado na v1.14.22 — Mapa: exportar diagnóstico completo da topologia em JSON

- Na aba **Mapa**, adicionar um botão **Exportar JSON**, próximo às ferramentas de exportação/KML.
- Objetivo: gerar um arquivo de diagnóstico que o usuário possa enviar para análise técnica, permitindo reproduzir problemas de enlaces, rotas, estações, iGates, digipeaters, tracklogs e filtros sem precisar compartilhar o banco SQLite inteiro.
- O JSON deve usar formato versionado, por exemplo `schema_version`, e incluir no topo:
  - versão do PT2VHF APRS Client;
  - data/hora da exportação em UTC;
  - período selecionado;
  - filtros/camadas relevantes do mapa;
  - versão/schema do banco;
  - configurações de retenção relacionadas ao histórico/topologia;
  - parâmetros do motor de rotas relevantes, como limite de hops e critérios espaço-temporais.
- Exportar **estações** com, quando disponível:
  - indicativo;
  - latitude/longitude atual;
  - último pacote/última escuta;
  - símbolo/tipo/role;
  - software/dispositivo identificado;
  - indicação de móvel/fixo quando inferível.
- Exportar **digipeaters e iGates** com classificação, coordenadas, primeira/última observação, contagens e estado recente/histórico.
- Exportar **enlaces/topologia** com:
  - origem e destino;
  - tipo RF/APRS-IS;
  - evidência direta/inferida/legada;
  - contagem de observações;
  - primeira e última observação;
  - coordenadas históricas usadas;
  - distância;
  - indicação de ativo/inativo;
  - dados necessários para entender por que o enlace entrou ou não no grafo.
- Exportar **eventos históricos de topologia** necessários para reconstrução, incluindo timestamp e coordenadas das duas extremidades no instante do contato.
- Incluir amostras de **raw/path APRS** associadas às evidências quando disponíveis e tecnicamente úteis, de forma limitada para não gerar arquivo gigantesco.
- Exportar **rotas/Recordes RF calculados**, incluindo:
  - extremidades;
  - sequência completa de nós;
  - hops;
  - distância direta das extremidades;
  - distância acumulada;
  - classe de alcançabilidade;
  - evidência selecionada por hop;
  - motivo de exclusão quando uma rota/enlace candidato não entrou no ranking, quando disponível.
- Exportar **tracklogs** segmentados com timestamp e coordenadas, preservando as quebras por descontinuidade temporal introduzidas na v1.14.20.
- Oferecer pelo menos duas opções:
  - **Período atual** — respeita o período/filtros selecionados;
  - **Diagnóstico completo** — inclui todo o histórico disponível necessário para investigar desaparecimento de enlaces e reconstrução de rotas.
- O modo completo deve incluir um resumo de tabelas/contagens e flags de truncamento caso algum conjunto seja limitado.
- Não exportar senhas, tokens, credenciais, cookies, chaves QRZ/API nem outros segredos de configuração.
- Gerar o arquivo com nome semelhante a `PT2VHF_APRS_Diagnostico_YYYYMMDD_HHMMSS.json`.
- Integrar a geração ao **indicador global de processamento**, exibindo algo como **“Gerando diagnóstico JSON…”**.
- Adicionar testes de schema e regressão garantindo que o JSON seja válido e contenha dados suficientes para reconstruir casos como:
  - rota multi-hop ausente no ranking;
  - enlace histórico que desapareceu;
  - tracker móvel usado em posições diferentes;
  - enlace inferido longo sem intermediários comprovados.
- **Critério de aceite:** ao receber esse JSON, deve ser possível analisar externamente por que determinado enlace/rota aparece, não aparece ou foi descartado, sem depender do banco SQLite original.

## Implementado na v1.14.21 — Estatísticas: unificar conteúdo em um único bloco sem rolagem interna

- Na aba **Estatísticas**, apresentar todo o conteúdo em **um único fluxo/bloco vertical**, utilizando somente a rolagem principal da aba/página.
- Remover barras de rolagem internas dos blocos de estatísticas.
- Problema observado: o ranking de **Software / dispositivos APRS** está atualmente dentro de um contêiner com altura limitada e **barra de rolagem própria**, criando uma segunda área de navegação dentro da aba.
- O ranking de aplicativos/dispositivos deve crescer verticalmente conforme a quantidade de itens, exatamente como os demais blocos da aba.
- Remover do bloco de Software / dispositivos APRS qualquer `max-height`, `height` fixa, `overflow-y: auto`, `overflow: scroll` ou regra equivalente que gere rolagem interna.
- Aplicar o mesmo princípio aos demais componentes da aba Estatísticas: rankings, anomalias, digipeaters, iGates, Recordes RF, problemas, melhorias e demais seções devem compartilhar a **mesma rolagem principal**.
- Preservar cabeçalhos, filtros e controles existentes, mas evitar painéis aninhados com scroll independente.
- Em listas extensas, preferir renderização normal no fluxo da página; se futuramente for necessário reduzir altura visual, utilizar paginação, “mostrar mais” ou recolhimento explícito, e não uma barra de rolagem interna.
- Garantir comportamento consistente nos temas claro/escuro e em telas menores.
- **Critério de aceite:** ao abrir Estatísticas, o usuário deve poder percorrer todo o conteúdo usando uma única barra de rolagem; o bloco **Software / dispositivos APRS** não pode possuir scroll interno próprio.

## Implementado na v1.14.21 — Estatísticas/Topologia: evitar timeout no período Completo

- **Diagnóstico confirmado com log da v1.14.20 (10/10/2026):** o problema não é apenas visual; existem operações de topologia que excedem o timeout do frontend e saturam o pool de workers.
- No log analisado, `/api/topology/stats` teve **11 respostas concluídas**, com mediana aproximada de **9,6 s**, média de **9,4 s** e pico de **12,2 s**; pelo menos **4 chamadas ultrapassaram 10 s**, embora o backend tenha terminado depois com HTTP 200.
- Isso explica a tela mostrar **“O backend local não respondeu em 10 segundos”** mesmo quando o cálculo termina pouco depois: o frontend aborta antes do backend.
- Foi identificado um segundo gargalo ainda mais severo em `/api/topology/rf-origins`: houve chamadas de aproximadamente **36,8 s** e **40,9 s**.
- Durante esse episódio, até **7 workers Waitress** ficaram simultaneamente presos em `list_rf_route_origins() → _route_graph()`, enquanto o oitavo worker atendia outras requisições. O watchdog registrou falhas consecutivas de health probe e o servidor chegou a ficar com **8 requisições ativas**.
- O thread dump confirma um problema de **thundering herd**: várias chamadas concorrentes de `rf-origins` iniciam a construção do mesmo grafo ao mesmo tempo.
- O cache atual de `_route_graph()` não impede esse cenário porque verifica o cache sob lock, libera o lock durante a construção pesada e só grava o resultado ao final; múltiplos misses simultâneos executam o mesmo trabalho em paralelo.
- Corrigir com mecanismo **single-flight por chave de cache**: quando um grafo para o mesmo período já estiver sendo calculado, as demais chamadas devem aguardar/reutilizar o mesmo resultado, e não reconstruí-lo em paralelo.
- No frontend, `refreshRfRouteOrigins()` também deve cancelar/ignorar requisições obsoletas. O debounce atual de aproximadamente **140 ms** pode disparar novas consultas enquanto uma anterior ainda está em andamento. Usar `AbortController`, generation token ou mecanismo equivalente.
- Evitar recalcular todo o grafo a cada tecla digitada no campo de origem. Preferir carregar/cachear a lista base uma vez por período e filtrar localmente quando possível.
- `topology_stats()` inclui cálculo de **Recordes/Rotas RF**, portanto a reconstrução cara de `_route_graph()` pode afetar diretamente o tempo da aba Estatísticas. Separar/cachar esse componente para não bloquear os demais indicadores.
- O log também mostrou `/api/map-data` chegando a aproximadamente **9,5 s** em situação de contenção, com 10.000 pontos de tracklog carregados; considerar o efeito combinado de consultas pesadas concorrentes sobre SQLite.
- Corrigir o timeout observado na aba **Estatísticas** ao selecionar/permanecer no período **Completo**, com a mensagem: **“O backend local não respondeu em 10 segundos (/api/topology/stats?hours=0)”**.
- O endpoint `/api/topology/stats?hours=0` não pode bloquear a interface por mais de 10 segundos nem fazer a tela parecer vazia quando existem dados no banco.
- O problema atual é agravado porque `topology_stats(0)` executa, em uma única chamada, várias consultas/agregações potencialmente pesadas sobre todo o histórico, incluindo rankings, anomalias, sugestões, rotas RF, identificação de software/dispositivos, comparação histórica e estatísticas de recepção.
- **Não mostrar 0 como se fosse dado real quando a consulta falhar ou expirar.** Enquanto o resultado não estiver disponível, os cartões devem exibir estado de **Carregando…/Processando…** ou **Indisponível**, preservando o último valor válido quando existir.
- Integrar esta operação ao **indicador global de processamento**: ao abrir Estatísticas ou trocar para **Completo**, mostrar o spinner/relógio central com texto como **“Calculando estatísticas do histórico…”**.
- Otimizar o backend para que o período completo seja utilizável mesmo com banco grande. Priorizar:
  - índices adequados para `packets.timestamp`, `packets.from_call`, `topology_events.timestamp`, `topology_edges.last_seen` e demais campos usados nos agrupamentos;
  - evitar varreduras repetidas da mesma tabela dentro da mesma atualização;
  - reutilizar resultados intermediários entre blocos da tela;
  - cachear agregações do período completo e invalidar o cache somente quando novos dados relevantes forem gravados;
  - pré-agregar métricas pesadas quando isso trouxer ganho mensurável.
- Avaliar separar `/api/topology/stats` em blocos independentes/assíncronos, para que uma seção pesada — por exemplo **rotas RF/Recordes RF** — não impeça que contadores, rankings e software/dispositivos apareçam.
- Se uma subseção exceder o tempo de cálculo, retornar as demais normalmente e marcar apenas aquela subseção como **processando/indisponível**, em vez de invalidar toda a tela.
- O frontend deve suportar resposta parcial e atualizar os blocos progressivamente conforme os resultados ficarem disponíveis.
- Não resolver apenas aumentando indiscriminadamente o timeout global de 10 segundos. O objetivo é **reduzir o custo da consulta e melhorar a experiência assíncrona**, mantendo proteção contra backend travado.
- Registrar no diagnóstico o tempo gasto por cada componente de `topology_stats`, por exemplo:
  - ranking de estações;
  - digipeaters/iGates;
  - anomalias;
  - sugestões;
  - rotas/recordes RF;
  - software/dispositivos;
  - recepção RF × APRS-IS.
- Quando qualquer bloco ultrapassar um limiar, registrar `duration_ms` no log para identificar regressões de performance.
- Adicionar testes com base de histórico volumosa garantindo que:
  - o período Completo não retorna falsos zeros por timeout;
  - o frontend mantém o último resultado válido durante recálculo;
  - falha de uma subseção não derruba as demais;
  - cache do histórico completo é reutilizado quando o banco não mudou;
  - inserção de novos pacotes invalida somente o necessário;
  - o indicador global de processamento aparece enquanto a análise pesada estiver em andamento e desaparece ao concluir ou falhar.
- **Critério de aceite:** ao abrir Estatísticas com **Período = Completo**, a interface deve continuar responsiva, mostrar claramente que está processando, apresentar resultados reais assim que disponíveis e não exibir cartões zerados apenas porque `/api/topology/stats?hours=0` demorou mais de 10 segundos.

## Implementado na v1.14.21 — Indicador global de processamento em primeiro plano

- Sempre que o aplicativo estiver executando uma operação que possa levar tempo perceptível ao usuário, exibir um **indicador visual centralizado sobre a interface**, deixando claro que existe processamento em andamento.
- Reutilizar e ampliar o mecanismo de **global processing overlay** já existente, evitando criar um segundo sistema paralelo de estado/overlay.
- O indicador deve aparecer **no centro da tela**, sobre o conteúdo atual, com aparência discreta porém inequívoca.
- Usar um elemento animado de atividade, preferencialmente **spinner/relógio girando**, acompanhado de mensagem curta quando o tipo de operação for conhecido.
- Exemplos de texto:
  - **Processando…**
  - **Carregando dados…**
  - **Analisando rotas RF…**
  - **Gerando backup…**
  - **Exportando KML…**
  - **Aplicando configurações…**
- O overlay deve ser utilizado principalmente quando uma operação:
  - bloquear temporariamente outra ação;
  - executar cálculo/análise relevante no backend;
  - carregar grande quantidade de dados;
  - gerar/exportar arquivo;
  - importar/restaurar dados;
  - executar atualização/migração;
  - realizar busca ou reconstrução de topologia/rotas que não seja praticamente instantânea.
- Evitar piscar o overlay em operações muito rápidas. Adotar um pequeno **delay de exibição**, por exemplo **250–400 ms**, para que ações concluídas imediatamente não provoquem ruído visual.
- Se a operação continuar após esse delay, mostrar o indicador e mantê-lo visível até a conclusão real.
- O indicador deve desaparecer obrigatoriamente em **sucesso, erro, cancelamento ou timeout**, inclusive quando ocorrer exceção.
- Operações assíncronas concorrentes não podem fazer o overlay desaparecer enquanto outra operação ainda estiver ativa. Implementar **contador/token de processamento** ou mecanismo equivalente.
- Quando várias tarefas estiverem simultaneamente ativas, priorizar a mensagem da operação mais recente/relevante sem perder a referência das demais.
- O overlay não deve congelar a animação: mesmo quando o backend estiver ocupado, a interface deve continuar renderizando o spinner sempre que tecnicamente possível.
- Quando a operação não exigir bloqueio total da interface, permitir modo **não bloqueante**, mantendo o indicador de atividade visível mas sem impedir navegação desnecessariamente.
- Para operações destrutivas ou que não podem ser interrompidas, manter o modo bloqueante existente.
- Garantir contraste adequado nos temas claro e escuro e funcionamento em diferentes resoluções.
- Adicionar acessibilidade com **role/status**, **aria-live** e texto equivalente para leitores de tela.
- Centralizar esse comportamento em funções reutilizáveis, por exemplo `showProcessing()`, `updateProcessing()`, `hideProcessing()` e/ou `withProcessing()`, em vez de implementar spinners isolados em cada funcionalidade.
- Revisar as principais operações já existentes e conectar ao indicador global onde ainda não houver feedback visual de processamento.
- Adicionar regressões garantindo:
  - exibição após o delay configurado;
  - ausência de flicker para operação rápida;
  - ocultação em sucesso e erro;
  - manutenção do overlay quando existem duas operações simultâneas;
  - atualização do texto durante etapas diferentes da mesma operação;
  - nenhum overlay residual após exceção.
- **Critério de aceite:** se o usuário iniciar uma ação que demore perceptivelmente, deve existir no centro da tela um sinal animado de atividade indicando que o aplicativo continua trabalhando, sem deixar a impressão de travamento.

## Implementado na v1.14.20 — Rotas RF: inferir alcançabilidade histórica por composição de enlaces observados

- **Princípio funcional:** o objetivo desta análise de rotas é mostrar a **alcançabilidade RF conhecida/potencial da rede**, e não provar que um único pacote percorreu toda a rota de origem a destino de uma só vez.
- A rota representa um **caminho topológico possível**, composto por enlaces RF que já foram observados individualmente e podem ter ocorrido em momentos diferentes.
- Portanto, não exigir contemporaneidade entre todos os hops para formar uma rota de alcançabilidade. A contemporaneidade serve para classificar a força da evidência, não para eliminar uma cadeia histórica válida.
- Exemplo: A → B observado hoje e B → C observado ontem podem sustentar **A → C via B** como alcançabilidade histórica, desde que B represente o mesmo contexto físico/topológico compatível.
- Permitir que o motor reconheça **alcançabilidade RF potencial** mesmo quando os hops que formam a cadeia não tenham sido observados no mesmo pacote.
- Exemplo: se em um momento foi observado **A → B** e, em outro momento, foi observado **B → C**, o sistema pode concluir que existe uma **rota RF historicamente plausível A → B → C** e, portanto, que **A pode alcançar C via B**, desde que os enlaces individuais sejam válidos e compatíveis.
- Essa inferência **não transforma A → C em enlace RF direto**. O resultado deve ser representado como **alcançabilidade/rota composta via intermediário**, preservando explicitamente B.
- O mesmo princípio vale para cadeias maiores: A → B, B → C e C → D, observados em eventos distintos, podem sustentar uma rota histórica plausível A → B → C → D.
- Separar semanticamente três classes:
  - **Rota RF observada no mesmo evento/pacote** — evidência mais forte;
  - **Rota RF reconstruída por eventos contemporâneos** — hops observados em eventos distintos, porém próximos no tempo e espacialmente coerentes;
  - **Rota RF histórica/plausível** — hops observados em momentos diferentes, usados para inferir alcançabilidade potencial da rede.
- A classe histórica/plausível deve ser permitida para análise de cobertura, malha e alcance potencial, mas **não deve ser apresentada como se tivesse ocorrido de ponta a ponta em um único evento**.
- Para nós fixos, a composição histórica pode usar enlaces observados em momentos diferentes, desde que não exista evidência de mudança relevante de posição, configuração ou função.
- Para nós móveis/tracker/digi móvel, a composição histórica só pode usar dois hops através do mesmo nó se as posições históricas daquele nó forem compatíveis com ambos os enlaces. Um tracker que esteve em Goiás e horas depois no Sul não pode unir essas duas redes em uma única rota.
- **Regra de coordenadas para nós móveis:** cada hop deve usar a **posição do nó no instante em que aquele contato/enlace foi observado**, nunca a posição atual nem uma posição registrada em outro momento.
- Se um tracker móvel serviu como elo em diferentes regiões ao longo de uma viagem, cada participação dele no grafo deve ser tratada como um **estado espaço-temporal distinto** do mesmo indicativo.
- Exemplo: se B estava em Brasília quando ocorreu A → B e depois estava em Formosa quando ocorreu B → C, o motor não pode usar a posição de Formosa para reinterpretar A → B, nem usar a posição de Brasília para reinterpretar B → C.
- Para compor uma rota histórica através de um nó móvel, comparar as coordenadas históricas associadas aos hops envolvidos. A composição só é válida quando essas posições representam um contexto físico compatível para o papel de elo.
- O cálculo da distância de cada hop deve sempre usar as coordenadas históricas correspondentes ao próprio evento de evidência.
- Quando não houver coordenada histórica confiável para um nó móvel no instante do enlace, o hop pode permanecer como evidência topológica, mas sua distância deve ser marcada como indeterminada e ele não deve ser usado para criar uma composição espacialmente afirmativa.
- Para cada nó intermediário, verificar:
  - posição histórica compatível;
  - ausência de deslocamento incompatível entre os eventos usados;
  - frequência/banda/canal compatíveis quando essa informação existir;
  - função de digipeater/relay válida no contexto;
  - direção do enlace, quando a evidência não for bidirecional.
- O motor deve guardar e exibir a origem da evidência de cada hop, com timestamp próprio. Não resumir toda a cadeia com um único timestamp.
- A interface deve mostrar algo como:
  - **A → B** — observado às 10:12;
  - **B → C** — observado às 11:03;
  - resultado: **A → C via B — alcançabilidade histórica plausível**.
- O usuário deve conseguir distinguir claramente **“observado”** de **“possível pela topologia histórica”**.
- Rotas históricas/plausíveis podem participar de análises de conectividade e cobertura, mas devem ter ranking/identificação próprios e não contam como recorde de enlace RF direto.
- O cálculo de distância deve continuar sendo feito por hop, usando as posições válidas no instante de cada observação; nunca usar uma única posição atual para toda a cadeia.
- Não exigir que todos os hops pertençam ao mesmo pacote para inferir alcançabilidade potencial; exigir apenas que cada hop tenha evidência própria e que a composição seja fisicamente/topologicamente coerente.
- Adicionar regressões para:
  - A → B e B → C em pacotes diferentes, formando alcançabilidade A → C via B;
  - A → B, B → C e C → D em momentos distintos, formando A → D via B/C;
  - nó intermediário móvel em posições incompatíveis, bloqueando a composição;
  - cadeia histórica válida que não seja confundida com enlace direto;
  - exibição separada dos timestamps/evidências de cada hop.
- **Critério de aceite:** o sistema deve reconhecer que uma sequência de enlaces RF reais observados em momentos diferentes pode demonstrar **alcançabilidade técnica entre as extremidades**, sem afirmar falsamente que houve um pacote único de ponta a ponta nem colapsar a cadeia em um enlace direto inexistente.

## Implementado na v1.14.20 — Rotas RF: não exibir hop inferido longo como enlace direto quando faltam intermediários

- Corrigir o caso em que a análise de rota apresenta um único hop RF inferido muito longo, mesmo informando **“intermediários não identificados”**.
- Exemplo observado: **LU9DCE → PU2XTC-4**, aproximadamente **1694,9 km**, aparece como 1 hop, RF inferido do path e é desenhado como uma reta única Buenos Aires → São Paulo.
- Esse comportamento é inconsistente: se a própria aplicação reconhece que o trecho é **inferido** e que existem intermediários não identificados, ele **não pode ser desenhado nem contabilizado como um único enlace RF físico entre as extremidades**.
- A reconstrução deve trabalhar primeiro com a **evidência do evento/pacote que originou o enlace**, e não apenas com o grafo agregado por pares de indicativos.
- Para cada evento RF inferido, analisar o raw/header APRS correspondente e reconstruir, na ordem real, todos os nós explicitamente presentes no path:
  - origem;
  - digipeaters efetivamente usados (*);
  - aliases resolvidos quando houver evidência objetiva;
  - iGate/q-construct aplicável;
  - destino/capturador da evidência.
- Preservar a sequência original do pacote. Se o mesmo frame mostra A → B → C → D, registrar/renderizar **A → B → C → D**, e não colapsar em A → D.
- Usar os eventos históricos e posições **no mesmo intervalo temporal do pacote**, respeitando o modelo espaço-temporal introduzido na v1.14.19.
- Ao procurar intermediários adicionais no grafo histórico, **não exigir que todos tenham sido observados no mesmo instante ou no mesmo pacote**. A finalidade é reconstruir a alcançabilidade da malha a partir de enlaces RF reais observados individualmente.
- Usar o tempo como metadado de evidência e como proteção contra combinações fisicamente inválidas, especialmente para nós móveis; para nós fixos, enlaces observados em momentos distintos podem compor a mesma rota histórica.
- A busca de intermediários deve poder ultrapassar o limite atual de poucos hops quando o path real do pacote trouxer uma cadeia maior. O limite de segurança deve impedir explosão combinatória, não truncar um path explicitamente observado.
- **Não inventar intermediários por proximidade geográfica.** Estações no caminho visual entre origem e destino só podem entrar na rota se houver evidência APRS/RF que as relacione àquele evento/corredor.
- Se não houver evidência suficiente para decompor o trecho:
  - manter o evento no histórico como **“RF inferido — cadeia incompleta”**;
  - não contabilizá-lo como 1 hop RF direto;
  - não desenhar uma linha contínua única entre as extremidades;
  - não incluí-lo em **Recordes RF diretos**;
  - no mapa, representar no máximo uma indicação de corredor/inferência incompleta, visualmente diferente de um enlace físico confirmado.
- O painel deve diferenciar claramente:
  - **hop RF direto observado**;
  - **cadeia RF reconstruída com intermediários observados**;
  - **trecho RF inferido com cadeia incompleta**.
- Quando houver intermediários conhecidos, exibir todos eles no painel e no mapa, com suas posições históricas correspondentes ao evento.
- O cálculo de distância da rota deve ser a soma dos segmentos realmente reconstruídos; a distância em linha reta entre as extremidades deve permanecer apenas como informação auxiliar.
- Adicionar regressão específica para **LU9DCE → PU2XTC-4**: um trecho inferido de ~1694,9 km sem cadeia comprovada não pode continuar aparecendo como um único hop RF físico.
- Adicionar testes para:
  - path com vários digipeaters explicitamente usados;
  - path com qAR/qAO após digipeaters;
  - evento inferido sem intermediários suficientes;
  - cadeia reconstruída somente com evidências contemporâneas;
  - não colapsar cadeia multi-hop em aresta origem→iGate;
  - não inserir nós apenas porque estão geograficamente entre as extremidades.
- **Critério de aceite:** se os pontos/nós intermediários forem conhecidos, a rota deve passar por eles; se não forem conhecidos, o sistema deve declarar a cadeia incompleta e jamais transformar a lacuna em uma reta RF direta de milhares de quilômetros.

## Implementado na v1.14.20 — Tracklog: quebrar o trajeto após longos períodos sem posição

- **Validação em campo:** ajuste confirmado pelo usuário como correto na v1.14.20; o tracklog passou a interromper adequadamente a linha após longos períodos sem posição, eliminando as retas artificiais entre trechos desconectados.
- **Não ligar automaticamente dois pontos de tracklog quando existir um intervalo temporal grande entre eles.**
- Problema observado: o tracker registrou um ponto no Aeroporto de Brasília, foi desligado e voltou a transmitir somente em Formosa. A interface ligou os dois pontos com uma linha reta, criando um deslocamento que nunca foi efetivamente registrado.
- Tratar o tracklog como uma sequência de **segmentos temporalmente contínuos**, e não como uma única polyline por indicativo.
- Ao ultrapassar o limite de continuidade temporal, encerrar o segmento atual e iniciar outro no próximo ponto.
- Usar como referência inicial um limite padrão de **30 minutos sem nova posição**, mantendo o valor tecnicamente configurável para ajuste futuro.
- O corte por tempo deve atuar **independentemente da distância**: mesmo que dois pontos estejam relativamente próximos, um intervalo longo não comprova o caminho percorrido entre eles.
- Preservar os dois pontos históricos no banco e no mapa; apenas **não desenhar a linha entre eles**.
- Não apagar nem invalidar posições legítimas por causa do intervalo. O objetivo é impedir a interpolação visual de um trajeto inexistente.
- Manter também as proteções atuais contra saltos geográficos/velocidades implausíveis; a nova regra temporal é complementar.
- Aplicar a mesma segmentação em:
  - mapa principal;
  - acompanhamento/seleção de tracklog;
  - histórico completo e períodos filtrados;
  - exportação KML;
  - qualquer cálculo futuro de distância percorrida baseado no tracklog.
- Quando um tracker voltar a transmitir após o intervalo, o primeiro ponto recebido deve aparecer como **início de um novo segmento**, sem linha de ligação com o segmento anterior.
- A lógica deve considerar o timestamp real de cada ponto e ordenar os pontos cronologicamente antes de formar os segmentos.
- Adicionar regressões para:
  - dois pontos separados por várias horas e grande distância, sem linha entre eles;
  - dois pontos separados por várias horas mesmo com pequena distância, também sem linha;
  - pontos sucessivos dentro da janela temporal, mantendo o tracklog normal;
  - combinação de corte temporal com a proteção já existente contra saltos geográficos.
- **Critério de aceite:** no exemplo Brasília → Formosa, se o tracker ficou desligado durante o deslocamento, o mapa deve mostrar o fim do tracklog em Brasília e um novo segmento começando em Formosa, sem a reta artificial entre as duas cidades.

## Implementado na v1.14.19 — Topologia RF espaço-temporal para digis/trackers móveis

- Corrigido o erro estrutural em que um indicativo móvel era tratado como um único vértice fixo durante todo o histórico.
- Cada observação nova de topologia passa a registrar a posição histórica de origem e destino no instante do evento.
- Bancos existentes recebem migração automática dos eventos legados usando o ponto de tracklog temporalmente mais próximo, quando disponível.
- Rotas RF observadas só são aceitas quando todos os hops cabem em uma janela de **30 minutos**.
- O nó compartilhado entre hops também precisa manter continuidade espacial compatível no mesmo período.
- Enlaces verdadeiros de um digi/tracker móvel continuam preservados em cada local por onde ele passou, mas não podem mais formar uma ponte artificial entre regiões visitadas em horários diferentes.
- Distâncias históricas e Recordes RF deixam de usar a posição atual/mais recente de uma estação móvel.
- O refinamento de enlaces inferidos reduz a janela temporal de 36 horas para **30 minutos**.
- Regressão baseada no caso real do **PT2AP-10**: PP2ITG-15 → PT2AP-10 observado na região de Itumbiara não pode ser unido a PT2AP-10 → PY5CTV-13 observado muitas horas depois no Sul.
- Critério de aceite: a posição atual de um tracker não altera retroativamente a distância de um enlace antigo, e rotas compostas por eventos de épocas/localizações incompatíveis deixam de aparecer como rota RF observada.

## Implementado na v1.14.18 — Mapa: acompanhar estação em tempo real pelo popup

- No **popup/balão da estação** aberto ao clicar sobre o marcador no mapa, adicionar uma ação explícita chamada **Acompanhar Estação** junto das demais opções existentes.
- Ao clicar em **Acompanhar Estação**:
  - fechar automaticamente o popup da estação;
  - centralizar imediatamente a estação no mapa;
  - ativar o modo de acompanhamento em tempo real;
  - manter a estação **sempre centralizada** enquanto novas posições forem recebidas;
  - atualizar suavemente o marcador/tracklog conforme a estação se deslocar.
- Durante o acompanhamento, exibir sobre o mapa um **painel flutuante compacto**, sem reabrir o popup e sem cobrir desnecessariamente o trajeto.
- Esse painel deve mostrar, no mínimo:
  - **indicativo** da estação acompanhada;
  - **velocidade** mais recente, quando disponível;
  - **curso/direção** mais recente, quando disponível;
  - **tempo desde o último pacote recebido**, atualizado dinamicamente, por exemplo: “agora”, “há 1 min”, “há 2 min”.
- O tempo desde o último pacote deve continuar aumentando mesmo sem novas transmissões, permitindo perceber rapidamente que a estação deixou de atualizar.
- Quando não houver velocidade ou curso válidos no último pacote, exibir estado neutro como **“—”** ou **“não informado”**, sem estimar dados inexistentes.
- O painel deve permanecer visível somente enquanto o modo **Acompanhar Estação** estiver ativo e desaparecer ao encerrar o acompanhamento.
- O acompanhamento deve usar as posições novas já recebidas pelo pipeline normal da estação/tracklog, sem criar uma fonte paralela de dados.
- Preservar o **nível de zoom atual escolhido pelo usuário** durante o acompanhamento; não executar `fitBounds` ou alterar o zoom a cada atualização.
- Se o usuário alterar apenas o zoom, continuar acompanhando a estação e recentralizá-la no novo nível.
- Encerrar o acompanhamento quando houver intenção clara de sair do modo, por exemplo:
  - arrastar/pan manualmente o mapa;
  - clicar em **Parar acompanhamento**, se essa ação estiver disponível;
  - selecionar e iniciar acompanhamento de outra estação.
- Ao iniciar acompanhamento de outra estação, transferir o foco para ela e cancelar o acompanhamento anterior.
- Se a estação deixar de transmitir, manter sua última posição conhecida centralizada, sem extrapolar movimento artificialmente, enquanto o painel evidencia há quanto tempo o último pacote foi recebido.
- O recurso deve funcionar para estações móveis com tracklog, como carros, HTs ou trackers, e também para qualquer estação que passe a enviar novas coordenadas.
- Reutilizar/refatorar o mecanismo de **seguir tracklog** já implementado na v1.14.16, evitando dois estados concorrentes de acompanhamento.
- Critério de aceite: ao clicar em **Acompanhar Estação**, o popup fecha, a estação fica centralizada e o painel flutuante mostra velocidade, curso e idade do último pacote; a cada nova posição recebida, o marcador continua no centro do mapa e os dados do painel são atualizados.

## Implementado na v1.14.18 — Mensagens APRS: evitar duplicação por retry/ACK

- Corrigida a causa estrutural dos retries: uma retransmissão passa a usar **o mesmo message ID APRS** e atualizar a mesma mensagem lógica no banco.
- Removida a criação de uma nova linha/novo ID a cada retry automático.
- **ACK e REJ são terminais**: estados de TX ou retry que terminem depois não podem voltar a mensagem para Enviada/Reenviada.
- A correlação continua por **destinatário + message ID**, com normalização de indicativo/SSID.
- Mensagens recebidas repetidamente com o mesmo remetente, destino, ID e texto são deduplicadas no histórico dentro da janela operacional de retry.
- A deduplicação não impede ACK: cada repetição aplicável pode provocar nova confirmação.
- Mensagens pessoais recebidas via **TNC/RF** passam a gerar **ACK por RF** quando o TX automático estiver habilitado e confirmado.
- Se um frame RF idêntico for recebido novamente e for suprimido pela janela anti-duplicação do TNC, o cliente ainda tenta reenviar o ACK, cobrindo perda do ACK anterior no ar.
- ACK recebido durante um retry prevalece; a atualização posterior do retry não ressuscita a mensagem.
- Diagnóstico registra ACK/REJ recebidos, retries, duplicatas suprimidas e falhas de ACK RF.
- Regressões cobrem terminalidade de ACK, retry com ID estável, uma única mensagem lógica no banco, deduplicação de RX e ACK RF.
- Critério de aceite: após ACK válido, **nenhuma nova retransmissão automática da mesma mensagem ocorre**, e repetições RF por ACK perdido não criam mensagens duplicadas no histórico.

## Encerrado como sintoma de dados legados — PP5AU-7 não aparecia no mapa

- O relato de que a própria estação **PP5AU-7**, recebida via TNC/RF, não aparecia no mapa foi **resolvido em campo ao apagar o banco de dados e iniciar com banco limpo**.
- Portanto, não tratar mais esse caso como evidência de bug ativo no pipeline RF→mapa.
- A evidência atual aponta para **estado legado/cache/migração de banco**.
- Manter apenas como pista para futura auditoria de compatibilidade/migração de bancos antigos, caso o sintoma volte a ocorrer.
- Não alterar filtros de `own callsign`, ingestão RF ou renderização do mapa com base somente nesse caso já resolvido.
- Se o problema reaparecer, coletar o banco antigo antes de apagá-lo para identificar exatamente qual registro/estado legado causa a supressão.

## Implementado na v1.14.17 — Configuração sem barras de rolagem internas

- A aba **Configuração** deve funcionar como uma página única e contínua.
- Usar somente a **rolagem vertical principal da aba Configuração**.
- Nenhum card, subbloco, lista, grupo de filtros ou seção inserida dinamicamente deve criar barra de rolagem vertical própria.
- Remover limites de altura e `overflow: auto/scroll` internos dos blocos da Configuração.
- Manter cards e subgrupos expandidos pela altura real do conteúdo.
- O comportamento deve valer também para blocos adicionados por módulos versionados, como integrações externas, saúde/retenção do banco, resposta automática, backup/grupos/alertas e futuros componentes.
- Preservar responsividade em telas menores: a aba pode ficar longa, mas deve continuar usando um único scroll vertical.
- Evitar barras horizontais internas sempre que o layout puder quebrar/reorganizar o conteúdo responsivamente.
- Adicionar regressão de CSS para impedir o retorno de viewports internos na Configuração.

## Implementado na v1.14.17 — Backup completo e indicador global de processamento

- Corrigir o botão **Criar backup completo**, que podia parecer inerte na janela integrada.
- Trocar o link simples por um fluxo explícito de geração, tratamento de erro e salvamento.
- Na janela desktop integrada, usar diálogo nativo de salvamento para Windows, Linux e macOS.
- No navegador, usar fallback por `fetch → Blob → download`.
- O backend do backup deve devolver erro JSON explícito quando a geração falhar e impedir cache do ZIP.
- Implementar um **overlay global de processamento** central, com indicador visual tipo relógio, título e mensagem contextual.
- O overlay deve bloquear cliques enquanto uma operação crítica estiver em andamento e ser removido automaticamente ao concluir ou falhar.
- Disponibilizar API reutilizável `show/update/hide/withProcessing` para outras operações longas.
- Aplicar o indicador ao backup completo, restauração de backup e geração de KML.
- Operações que já possuem progresso dedicado, como a atualização automática, podem manter o componente específico existente.
- Ao concluir, apresentar feedback explícito de sucesso ou erro ao usuário.
- Criar regressões para fluxo de download, ponte nativa, overlay e tratamento de falhas.

## Implementado na v1.14.17 — Rotas RF: decompor enlaces inferidos longos em nós intermediários conhecidos

- Ao analisar uma rota RF, **não tratar automaticamente um enlace `RF inferido do path` como um único hop físico** quando houver evidência topológica de nós intermediários entre as duas extremidades.
- Exemplo observado: `PP2RDB-15 → PT2AP-10` apareceu como um único trecho inferido de aproximadamente **796 km**. Esse tipo de aresta deve ser refinado antes de ser apresentado como hop único.
- A distância, isoladamente, **não deve invalidar** o enlace, pois enlaces RF longos reais podem existir. Ela deve apenas atuar como gatilho para procurar uma decomposição mais plausível quando a evidência for apenas inferida.
- Para cada aresta com `evidence_level=inferred`:
  - procurar no grafo RF conhecido um caminho alternativo entre origem e destino **excluindo a própria aresta inferida**;
  - priorizar arestas com evidência `RF direto observado`;
  - em seguida, aceitar arestas inferidas com múltiplas observações;
  - preferir menor número de hops e maior quantidade/recência de evidências;
  - limitar a busca para evitar explosão combinatória.
- Se existir um caminho intermediário melhor sustentado, **expandir a aresta no painel e no mapa**, por exemplo:
  - em vez de `A → D`;
  - mostrar `A → B → C → D`.
- Os nós inseridos pela reconstrução devem ser identificados como **intermediários reconstruídos/prováveis**, sem apresentá-los como se tivessem sido explicitamente observados no mesmo pacote.
- Sempre que possível, usar o histórico temporal próximo da observação original do enlace para evitar montar uma rota artificial combinando evidências de épocas muito diferentes.
- Se não houver evidência suficiente para identificar os intermediários:
  - manter o trecho;
  - continuar exibindo-o tracejado como RF inferido;
  - indicar no painel **“intermediários não identificados”**;
  - não inventar estações.
- Enlaces com `RF direto observado` continuam podendo ser longos e **não devem ser quebrados apenas pela distância**.
- Adicionar regressões com:
  - enlace inferido longo com cadeia intermediária conhecida;
  - enlace inferido longo sem cadeia conhecida;
  - enlace direto longo legítimo, que deve permanecer intacto;
  - preferência por cadeia com evidência direta em vez de cadeia apenas inferida.

## Implementado na v1.14.16 — Mapa: exibir todos os nós envolvidos na rota analisada

- Ao abrir no mapa uma rota a partir de **Estatísticas > Ranking** ou da análise manual entre duas estações, garantir que **todos os nós listados no popup/painel da rota também apareçam visualmente no mapa**.
- A representação do mapa deve ser coerente com a sequência exibida no painel: se a rota mostra `A → B → C → D`, os quatro nós precisam estar visíveis no mapa.
- Não depender exclusivamente dos marcadores normais de estação para representar os nós da rota.
- Se um nó da rota estiver:
  - oculto por filtros;
  - fora do conjunto normal de marcadores carregados;
  - sem marcador persistente naquele momento;
  - ou não puder ser exibido pelo mecanismo padrão;
  criar um **marcador temporário de rota** para garantir sua visualização.
- Origem, destino e nós intermediários devem ser representados de forma consistente e permanecer visíveis enquanto a análise da rota estiver ativa.
- Os marcadores temporários da rota devem usar as coordenadas presentes nos dados da própria rota/enlace.
- Evitar duplicidade visual: se o marcador normal da estação já estiver visível, não criar outro por cima.
- Ao trocar de rota, atualizar o conjunto de marcadores temporários para refletir apenas os nós da nova rota/corredor analisado.
- Ao fechar a análise de rota, remover os marcadores temporários sem afetar os marcadores normais do mapa.
- O `fitBounds` da rota deve considerar também esses nós temporários, garantindo que todos permaneçam dentro da área visível.

## Implementado na v1.14.16 — Estatísticas > Ranking: enquadramento automático do trajeto no mapa

- Ao abrir no mapa uma rota/trajeto a partir de **Estatísticas > Ranking**, ajustar automaticamente o enquadramento para o **zoom mais próximo possível** que ainda mantenha **todo o trajeto e todas as estações envolvidas visíveis**.
- Calcular o `fitBounds` usando o conjunto completo de coordenadas dos nós e enlaces da rota selecionada.
- Aplicar apenas uma pequena margem visual (`padding`) para evitar que marcadores, labels ou extremidades do trajeto encostem nas bordas do mapa.
- Não usar um `maxZoom` artificialmente baixo quando o trajeto couber em um nível de zoom maior.
- Para rotas curtas ou com estações próximas, aproximar significativamente o mapa em vez de manter uma visão regional ampla.
- Para rotas longas, reduzir o zoom somente o necessário para que nenhuma estação ou trecho fique fora da área visível.
- Considerar no cálculo todos os nós intermediários da rota, não apenas origem e destino.
- Recalcular o enquadramento ao selecionar outra rota do ranking.
- Preservar a possibilidade de o usuário alterar manualmente o zoom após o enquadramento automático.

## Implementado na v1.14.16 — Mapa: seguir tracklog selecionado

- Ao clicar em um **tracklog** no mapa, ativar um modo de acompanhamento automático.
- Enquanto o tracklog/estação continuar recebendo novas posições, manter sua posição **centralizada no mapa** durante o deslocamento.
- O mapa deve acompanhar suavemente a atualização das coordenadas, evitando saltos visuais desnecessários.
- O acompanhamento deve cessar quando:
  - o usuário fechar/desselecionar o tracklog;
  - selecionar outra estação/tracklog;
  - ou realizar uma ação manual de navegação que indique intenção de sair do modo de acompanhamento, como arrastar o mapa.
- Zoom manual deve ser preservado durante o acompanhamento; não reajustar o nível de zoom a cada nova posição.
- Se o tracklog deixar de receber novas posições, manter a última posição exibida sem movimentações artificiais.
- Reutilizar o mesmo estado de seleção já usado pelo mapa para evitar criar um segundo mecanismo paralelo de foco.

## Implementado na v1.14.15 — rotas RF: não perder enlaces válidos em malhas densas

- Remover o encerramento prematuro da pesquisa após `route_limit * 4` caminhos encontrados.
- Separar claramente **grafo RF observado**, **cálculo de caminhos** e **limite de apresentação**.
- Fazer `max_routes` limitar somente quantas rotas aparecem no painel, não quais enlaces podem ser considerados pelo motor.
- Usar busca best-first sobre caminhos simples, priorizando evidência RF direta e menor custo topológico.
- Não usar distância absoluta como filtro de exclusão.
- Classificar cada trecho como RF direto observado, RF inferido do path ou RF observado legado.
- Exibir no painel quantos trechos da rota são diretos, inferidos ou legados.
- Calcular e retornar o **corredor completo de enlaces RF elegíveis** entre origem e destino dentro do horizonte de hops.
- Durante a análise, mostrar no mapa todo esse corredor; ao selecionar uma rota, destacar seus enlaces e deixar os demais elegíveis em segundo plano.
- Ampliar o horizonte padrão da pesquisa manual de 8 para 12 hops.
- Manter um limite alto de expansões apenas como proteção contra explosão combinatória e informar explicitamente quando ele for atingido.
- Preservar APRS-IS/Internet fora do grafo de rotas RF.
- Criar regressões para malha densa, alternativas de rota, evidência direta versus inferida e enlaces longos observados.

## Consolidado na v1.14.14 — consistência do modelo RF observado

- Uniformizar a terminologia da interface após a reversão da heurística da v1.14.12.
- Usar **RF observado** em painel de rotas, mensagens e autocomplete.
- Remover do painel qualquer campo de confiança/plausibilidade que possa sugerir que distância ou quantidade mínima de observações ainda bloqueiam enlaces.
- Mostrar a origem real da classificação do trecho quando disponível.
- Preservar foco exclusivo da pesquisa de duas estações, Recordes RF, distinção RF × Internet e Estatísticas sem scroll vertical interno.
- Adicionar regressão para impedir retorno dos rótulos “RF confirmado”/“confirmed RF” na análise de rotas.

## Implementado na v1.14.13 — Topologia/Recordes RF: restaurar algoritmo RF anterior à v1.14.12

- **Reverter a lógica excessivamente restritiva introduzida na v1.14.12 para validar “100% RF”.**
- Voltar ao algoritmo usado antes da v1.14.12 para formar o grafo, pesquisar rotas e alimentar os **Recordes RF**.
- A classificação deve voltar a priorizar a **evidência APRS/RF observada**, sem eliminar enlaces apenas por serem longos ou por possuírem poucos nós intermediários.
- Operadores confirmaram que alguns dos enlaces longos anteriormente exibidos eram tecnicamente possíveis e realmente observados; portanto, esses caminhos não devem ser descartados por uma heurística de plausibilidade física.
- Não usar distância absoluta, número de hops ou combinação entre ambos como filtro de exclusão automática de um enlace RF.
- Não exigir uma quantidade mínima arbitrária de observações para manter um enlace RF já identificado pela lógica anterior.
- Preservar como regra objetiva:
  - enlace explicitamente APRS-IS/Internet **não** pode completar uma rota 100% RF;
  - evidência RF direta deve permanecer RF;
  - evidência RF válida extraída do path APRS deve continuar sendo considerada conforme o algoritmo anterior;
  - RF e APRS-IS do mesmo par devem permanecer como evidências independentes.
- O ranking de Recordes RF deve voltar a enxergar os mesmos enlaces que eram apresentados antes da v1.14.12, respeitando o período selecionado e a distinção RF × Internet.
- A distância pode continuar sendo exibida e usada para ordenar os recordes, mas **não para decidir se o enlace é válido ou inválido**.
- Caso se mantenha algum indicador de plausibilidade/confiança, ele deve ser apenas informativo e não alterar o grafo nem ocultar enlaces.
- Remover/reverter os thresholds de plausibilidade física introduzidos na v1.14.12 (250 km, 600 km, 1.000 km ou equivalentes) como critérios de inclusão.
- Reavaliar o comportamento de autocomplete, pesquisa de rotas e Recordes RF para garantir que todos usem novamente o mesmo grafo RF permissivo anterior.
- Criar testes de regressão garantindo que:
  - enlace RF longo observado continue aparecendo;
  - rota longa com poucos hops continue elegível quando a evidência RF existir;
  - APRS-IS continue sem completar rota RF;
  - rotas curtas e multi-hop continuem funcionando;
  - o algoritmo restaurado produza o mesmo conjunto de enlaces RF das versões anteriores à v1.14.12 para os mesmos dados de entrada.


## Implementado na v1.14.11 — Menu superior: simplificar textos de status

- No indicador de versão do menu superior, trocar o texto **“Versão atualizada”** por apenas **“Atualizada”**.
- No status do TNC:
  - remover os textos **“TNC offline”**, **“TNC online”** ou equivalentes;
  - exibir apenas **“TNC”**;
  - manter o LED como indicador visual do estado;
  - LED **verde** quando o TNC estiver conectado/operacional;
  - LED **vermelho** quando estiver desconectado/offline.
- Aplicar o mesmo padrão ao status do **APRS-IS**:
  - exibir apenas **“APRS-IS”**;
  - LED **verde** quando conectado;
  - LED **vermelho** quando desconectado;
  - remover textos longos como “Conectado”, “Desconectado” ou equivalentes ao lado do nome.
- Preservar tooltip/title com detalhes adicionais do estado, quando útil, sem poluir visualmente a barra superior.
- Manter consistência visual entre os indicadores **TNC** e **APRS-IS**, incluindo tamanho do LED, espaçamento, tipografia e comportamento de cores.

## Ajustado até a v1.14.12 — Estatísticas: recordes RF por distância entre estações

- Ao abrir no mapa uma rota/recorde RF selecionado, tornar o **popup/painel lateral de análise de rota arrastável**.
- Permitir mover o painel livremente dentro da área do mapa por **drag-and-drop**, preferencialmente arrastando pelo cabeçalho **“ANÁLISE DE ROTA RF”**.
- O painel não deve ficar preso ao canto superior direito quando estiver cobrindo estações, hops ou trechos importantes da rota.
- Manter os botões, seleção de rotas, rolagem interna e demais interações funcionando normalmente após mover o painel.
- Limitar o deslocamento para que o painel não possa ser arrastado completamente para fora da área visível do mapa.
- Preservar a posição enquanto a mesma análise/recorde permanecer aberto.
- Ao fechar e abrir uma nova análise, pode restaurar a posição padrão, salvo se futuramente for implementada persistência da posição.
- Exibir cursor/feedback visual adequado no cabeçalho para indicar que o painel pode ser movido.
- Garantir funcionamento com mouse e, quando aplicável, toque/pointer events.
- Criar regressão de interface para o comportamento de arrastar, limites da área do mapa e fechamento/restauração do painel.


- Ao selecionar/clicar em um item do ranking de **Recordes RF**, abrir imediatamente a rota correspondente no mapa em **modo de foco exclusivo**.
- Nesse modo, exibir somente:
  - a rota RF selecionada;
  - as estações de origem e destino;
  - todos os digipeaters/estações intermediárias envolvidos;
  - os enlaces/trechos que compõem aquele caminho.
- Ocultar temporariamente do mapa:
  - demais estações;
  - demais enlaces RF;
  - enlaces APRS-IS/Internet;
  - objetos/camadas que possam poluir visualmente a leitura da rota, quando não forem necessários para o contexto.
- Ajustar automaticamente o zoom/enquadramento para mostrar o trajeto completo com boa margem visual.
- Destacar a sequência da rota de forma clara, preservando a ordem dos hops.
- Mostrar no mapa/painel de apoio:
  - sequência completa dos indicativos;
  - distância de cada trecho;
  - distância total da rota;
  - quantidade de hops;
  - evidência/horário da rota.
- Reutilizar o mesmo **modo de foco de rotas RF** já existente na pesquisa por dois indicativos, evitando uma implementação paralela.
- Incluir ação clara de **Voltar/Limpar foco**, restaurando exatamente a visualização anterior do mapa.
- Ao selecionar outro item do ranking, substituir o foco atual pela nova rota, sem exigir limpeza manual prévia.
- Garantir que o mapa não mostre simultaneamente toda a topologia geral enquanto um recorde estiver selecionado, para que o trajeto fique **claro e nítido**.
- Criar teste/regressão para seleção no ranking, foco exclusivo, enquadramento, troca de recorde e restauração do estado anterior do mapa.

- Adicionar na aba **Estatísticas** um bloco de **Recordes RF** com ranking dos pares de estações interligados por uma rota RF completa, usando como referência principal a **distância geográfica direta entre as duas estações extremas**.
- Exibir em formato de ranking, por exemplo:
  - `1 — PT2VHF → PP2AX → PY2ASD — 182 km`
  - `2 — ...`
- Considerar somente caminhos compostos por **enlaces RF reais observados**, sem usar APRS-IS/Internet para completar a rota.
- Para cada recorde, mostrar pelo menos:
  - posição no ranking;
  - estação de origem;
  - estação de destino;
  - **distância direta entre origem e destino**, que define a posição no ranking;
  - sequência completa dos hops/intermediários;
  - quantidade de hops;
  - distância de cada trecho;
  - **distância total da rota RF**;
  - data/hora da evidência mais recente da rota;
  - quantidade de observações/evidências disponíveis, quando houver.
- Ordenar da **maior para a menor distância direta entre a estação de origem e a estação de destino**, desde que exista rota RF completa entre elas. A distância total percorrida pelos hops deve permanecer visível apenas como informação complementar e não como critério principal do ranking.
- Respeitar o período selecionado na aba Estatísticas; quando o período for alterado, recalcular o ranking.
- Evitar duplicidade da mesma rota em sentido inverso quando representar o mesmo caminho observado; tratar `A → B → C` e `C → B → A` como o mesmo recorde, salvo quando houver evidência direcional relevante que justifique separação.
- Quando houver múltiplas rotas entre o mesmo par de estações, o **par origem/destino deve ocupar uma única posição no ranking pela distância direta entre as extremidades**. As diferentes sequências de hops podem ser mostradas como alternativas/detalhes desse mesmo recorde.
- Permitir clicar em um recorde para abrir/localizar a rota correspondente no mapa, reutilizando o modo de análise de rotas RF já existente.
- Reutilizar o mesmo grafo/topologia RF do recurso de pesquisa de rotas para manter coerência de classificação e cálculo de distância.
- Criar testes para ranking por distância direta entre as estações extremas, cálculo da distância total da rota como dado complementar, múltiplos hops, múltiplas rotas do mesmo par, deduplicação de sentido inverso, exclusão de Internet/APRS-IS e filtro por período.

## Reforçado na v1.14.13 — Estatísticas: exibir blocos completos sem rolagem interna

- Corrigir especificamente o bloco de **ranking de software/aplicações**, que ainda aparece como uma área separada com barra de rolagem vertical própria.
- O ranking de software deve ficar **contínuo com os demais blocos abaixo**, fazendo parte do mesmo fluxo vertical da aba Estatísticas.
- Remover qualquer `height`, `max-height`, `overflow-y: auto`, `overflow-y: scroll` ou combinação de flex/layout que crie uma viewport vertical independente nesse bloco.
- O conteúdo do ranking deve crescer naturalmente conforme o número de linhas exibidas.
- A seção seguinte, como **Saúde e comparação da rede**, deve aparecer imediatamente após o término real do ranking, sem uma “janela rolável” intermediária.
- A única barra de rolagem vertical deve ser a da **aba/página de Estatísticas como um todo**.
- Manter apenas rolagem horizontal se a tabela ficar larga demais.
- Garantir que o container pai da aba não esteja impondo altura fixa que force o ranking a rolar internamente.
- Revisar também `.analysis-content`, `.analysis-client-version-panel`, `.client-version-stats-content` e wrappers da tabela para garantir fluxo contínuo.
- Validar visualmente com ranking de 20 ou mais softwares, confirmando que todas as linhas ficam expostas na página e que os blocos seguintes permanecem logo abaixo.


- Reforçar a regra para que **todos os blocos/cards da aba Estatísticas fiquem integralmente na página**, sem barra de rolagem vertical própria.
- Aplicar explicitamente essa regra ao bloco de **ranking de uso de software/aplicações**, que ainda pode apresentar rolagem vertical interna.
- Remover `max-height`, alturas fixas e `overflow-y: auto/scroll` de qualquer bloco da aba Estatísticas que ainda limite verticalmente o conteúdo.
- A aba deve usar **uma única rolagem vertical principal**, correspondente à própria página/área de conteúdo da aba.
- Tabelas, rankings, listas de software, estações, iGates, digipeaters, Recordes RF e demais painéis devem crescer verticalmente conforme a quantidade de registros exibidos.
- Preservar apenas rolagem **horizontal** quando necessária para tabelas largas, sem introduzir scroll vertical interno.
- Garantir que cabeçalhos, ordenação, filtros e cliques permaneçam funcionais após a remoção dos limites de altura.
- Validar que nenhum bloco fique cortado em notebook, Full HD, escala ampliada do Windows ou janela não maximizada.
- Criar regressão visual/CSS que detecte a reintrodução de `max-height` ou `overflow-y` vertical nos principais blocos de Estatísticas.


- Remover, sempre que possível, as **barras de rolagem internas** dos blocos/cards da aba **Estatísticas**.
- Os painéis devem crescer verticalmente conforme a quantidade de conteúdo, exibindo tabelas, rankings e demais informações **por inteiro**.
- Priorizar uma única rolagem vertical da página/aba de Estatísticas, evitando a experiência de “rolagem dentro da rolagem”.
- Remover alturas fixas, `max-height` ou `overflow-y: auto/scroll` que estejam limitando artificialmente cards como **Estações — atividade e interações** e outros blocos semelhantes.
- Aplicar o mesmo princípio a **todos os blocos da aba Estatísticas**, mantendo cada seção inteira sempre que tecnicamente viável.
- Preservar cabeçalhos, colunas e alinhamento das tabelas.
- Para tabelas muito largas, manter comportamento horizontal responsivo sem cortar informações; a solicitação de remover rolagem refere-se principalmente à **rolagem vertical interna**.
- Garantir que o aumento da altura dos cards não cause sobreposição entre blocos nem quebra do layout em resoluções menores.
- Validar em notebook, tela Full HD, escala ampliada do Windows e janela não maximizada.
- Criar regressão visual/layout para impedir o retorno de alturas internas fixas desnecessárias.

## Implementado na v1.14.10 — Mapa: barra superior responsiva e compacta

- Reduzir a largura dos campos de **indicativo de origem e destino**, deixando-os apenas com o espaço necessário para um indicativo APRS válido e pequena folga visual.
- Tornar também os demais campos, selects e botões da barra **mais justos/compactos**, evitando larguras mínimas excessivas.
- Priorizar dimensionamento por conteúdo (`fit-content`/largura intrínseca quando aplicável), mantendo somente o espaço necessário para texto, ícone e área confortável de clique.
- Evitar campos vazios largos quando o conteúdo máximo previsível é curto.
- Preservar legibilidade, acessibilidade e área mínima de interação, sem deixar os controles visualmente apertados demais.
- Em telas largas, não expandir os controles desnecessariamente; usar o espaço extra principalmente para o mapa.
- Em telas menores, combinar essa compactação com a quebra responsiva em linhas prevista nesta mesma correção.

- Corrigir a faixa de controles imediatamente acima do mapa, que ficou **espremida e recortada** após a inclusão da pesquisa de indicativos/Rotas RF.
- Na largura mostrada na interface, alguns controles deixam de ficar totalmente visíveis e a barra passa a exigir espaço horizontal maior do que o disponível.
- Evitar comprimir excessivamente campos, selects e botões a ponto de prejudicar leitura ou operação.
- Reorganizar a barra de forma **responsiva**, preservando todos os comandos atuais, incluindo Histórico, Período, pesquisa de indicativos, Rotas RF, Limpar, Ver, Velocidade, Tipo de mapa e demais controles existentes.
- Em larguras menores, permitir quebra organizada em **duas linhas** ou outra disposição adaptativa, em vez de simplesmente ocultar/recortar controles.
- Manter alinhamento visual e espaçamento consistente entre grupos de controles.
- Não reduzir o mapa desnecessariamente; a barra deve ocupar apenas a altura necessária.
- Evitar rolagem horizontal como comportamento principal; se for usada como fallback extremo, não deve esconder controles essenciais.
- Garantir funcionamento em notebooks, telas com escala do Windows ampliada e janelas não maximizadas.
- Validar nos principais breakpoints e com zoom/escala de interface maiores.
- Criar teste visual/regressão de layout para impedir que novos controles voltem a ultrapassar a largura disponível.

## Implementado na v1.14.13 — Mapa: pesquisa por indicativo e rota RF entre duas estações

- Ao pesquisar **duas estações** pela barra superior do mapa e exibir as rotas entre elas, usar o **mesmo modo visual aplicado ao clicar em um Recorde RF no ranking**.
- Depois de selecionar origem e destino e clicar em **Pesquisar**:
  - esconder temporariamente as demais estações;
  - esconder os demais enlaces RF que não façam parte das rotas encontradas;
  - esconder enlaces APRS-IS/Internet alheios ao resultado;
  - esconder objetos, tracklogs e outras camadas que possam poluir a leitura, quando não forem necessárias para o contexto.
- Manter visíveis somente:
  - estação de origem;
  - estação de destino;
  - todos os digipeaters/estações intermediárias das rotas válidas;
  - os enlaces que efetivamente compõem essas rotas.
- Reutilizar exatamente o mesmo **modo de foco exclusivo** já usado pelo ranking de Recordes RF, evitando duas implementações diferentes.
- Se houver mais de uma rota válida entre as duas estações:
  - mostrar todas as alternativas no painel lateral;
  - manter no mapa somente os enlaces pertencentes ao conjunto dessas rotas;
  - permitir selecionar uma alternativa e destacá-la, deixando as demais em segundo plano.
- Ajustar automaticamente o zoom para enquadrar o conjunto completo das rotas encontradas.
- O painel lateral deve usar o mesmo estilo e comportamento do ranking, incluindo o painel arrastável quando essa funcionalidade estiver disponível.
- Ao limpar a pesquisa ou fechar a análise, restaurar exatamente a visualização anterior do mapa.
- Criar regressão garantindo que **pesquisa manual entre dois indicativos** e **clique em Recorde RF** usem o mesmo mecanismo de foco, filtragem e restauração do mapa.


- Na barra do mapa, renomear o botão **“Rotas RF”** para **“Pesquisar”**, mantendo a mesma ação de consultar/analisar as rotas RF entre os indicativos informados.

- Tornar os campos de **indicativo inicial** e **indicativo final** autocompletáveis desde os primeiros caracteres digitados.
- No campo de **origem/início**, sugerir indicativos já conhecidos pelo cliente no período/base atual, priorizando estações com posição válida e participação em enlaces RF observados.
- À medida que o usuário digitar, reduzir dinamicamente a lista de sugestões por correspondência de prefixo/trecho do indicativo.
- Após selecionar ou preencher o primeiro indicativo, o campo de **destino/fim** deve passar a sugerir somente indicativos para os quais exista **rota RF completa observada/possível no grafo atual**, respeitando o período selecionado.
- Não sugerir no segundo campo estações cujo caminho dependa de APRS-IS/Internet, trecho ausente ou rota RF incompleta.
- Pré-preencher/sugerir os indicativos conhecidos de forma progressiva, sem exigir que o usuário memorize ou digite o indicativo completo.
- Se houver apenas uma correspondência válida para o texto digitado, permitir completar automaticamente o indicativo quando isso não gerar ambiguidade.
- Ordenar as sugestões considerando, quando disponível:
  - melhor correspondência textual;
  - rota RF completa mais recente;
  - maior quantidade de observações/evidências;
  - menor quantidade de hops.
- Atualizar imediatamente as sugestões caso o usuário altere o período do mapa, a origem ou os filtros que mudem o grafo RF disponível.
- Reutilizar a mesma base de indicativos/topologia usada pela análise de rotas para evitar sugestões que depois não possam ser efetivamente calculadas.

- Após selecionar/preencher o **primeiro indicativo**, o campo do **segundo indicativo** deve ser filtrado dinamicamente.
- Ao começar a digitar o segundo indicativo, exibir como sugestões apenas estações para as quais exista **rota RF completa observada** a partir do primeiro indicativo, dentro do período atualmente selecionado no mapa.
- Não listar como candidato do segundo campo uma estação cujo caminho dependa de trecho APRS-IS/Internet, de salto ausente ou de evidência RF incompleta.
- A lista deve funcionar como busca/autocomplete, reduzindo as opções conforme o usuário digita.
- Se não existir nenhuma estação com rota RF completa a partir do primeiro indicativo, informar isso no próprio campo/resultado, sem sugerir estações inválidas.
- Ao trocar o primeiro indicativo ou o período do mapa, recalcular imediatamente a lista de candidatos válidos para o segundo campo.
- Se o segundo indicativo já selecionado deixar de possuir rota RF completa após mudança de período/filtros, invalidar a seleção e informar o motivo.
- Priorizar na ordenação dos candidatos, quando possível:
  - rota RF mais recente;
  - maior quantidade de evidências/observações;
  - menor quantidade de hops;
  - correspondência textual com o que estiver sendo digitado.
- O filtro do segundo campo deve reutilizar o mesmo grafo/evidência usado para calcular e desenhar a rota, evitando divergência entre autocomplete e resultado final.
- Quando o usuário selecionar os dois indicativos e aplicar a análise de rota, o mapa deve entrar em um **modo de foco de rotas**:
  - esconder temporariamente todos os demais enlaces/rotas que não façam parte de algum caminho RF válido entre os dois indicativos selecionados;
  - manter visíveis apenas as rotas RF encontradas para aquele par;
  - preservar as estações/nós intermediários necessários para compreender cada caminho.
- Se houver **mais de uma rota RF possível**, exibir todas as alternativas válidas no mapa, mas ocultando qualquer enlace alheio ao filtro para evitar poluição visual.
- Abrir um **painel/popup lateral** dedicado à análise, listando separadamente cada rota possível com base exclusivamente nos enlaces registrados.
- Para cada rota alternativa, mostrar pelo menos:
  - identificação da rota (ex.: Rota 1, Rota 2, Rota 3);
  - sequência completa de indicativos/hops;
  - quantidade de hops;
  - distância de cada trecho;
  - distância total da rota;
  - distância direta entre origem e destino;
  - data/hora da evidência mais recente da rota;
  - quantidade de observações/evidências disponíveis por trecho, quando houver.
- Permitir clicar em uma rota no painel lateral para **destacá-la** no mapa e reduzir visualmente a ênfase das demais alternativas.
- Quando houver apenas uma rota válida, mostrar somente ela no mapa e o painel lateral deve indicar claramente que existe **1 rota RF completa observada**.
- Incluir uma ação de **limpar/fechar análise de rota**, restaurando imediatamente os enlaces e camadas que estavam visíveis antes da aplicação do filtro.
- O painel lateral e o mapa devem sempre usar o mesmo conjunto de enlaces filtrados pelo período atual; não listar uma rota no painel se algum trecho dela não estiver efetivamente disponível no grafo RF daquele período.
- Não misturar rotas parciais com rotas completas: caminhos incompletos podem ser informados separadamente como diagnóstico, mas nunca devem aparecer entre as rotas RF completas disponíveis.

- Adicionar no mapa um campo de **pesquisa por indicativo** para localizar rapidamente uma estação e centralizar/realçar sua posição.
- Permitir informar um **segundo indicativo** em campo separado para analisar a conectividade RF entre as duas estações.
- Quando houver evidência de um caminho RF completo entre origem e destino, listar e desenhar no mapa **toda a rota RF observada**, incluindo todos os nós/hops intermediários.
- Exibir, para cada trecho da rota:
  - estação/nó de origem e destino;
  - tipo do trecho, obrigatoriamente baseado em **evidência RF real**;
  - distância do trecho;
  - horário/última evidência observada, quando disponível;
  - quantidade de observações/pacotes, quando disponível.
- Exibir também:
  - distância geográfica direta entre os dois indicativos;
  - **distância total percorrida pela rota RF** (soma dos trechos);
  - quantidade total de hops;
  - sequência completa da rota em ordem, por exemplo: `PT2AAA → DIGI1 → DIGI2 → PT2BBB`.
- Destacar visualmente no mapa a rota completa entre os dois indicativos, sem ocultar os demais elementos do mapa.
- Se houver mais de uma rota RF possível, priorizar a rota mais recente/consistente e permitir visualizar alternativas quando tecnicamente viável.
- **Não considerar APRS-IS/Internet como trecho RF.** Um caminho só deve ser declarado como rota RF completa quando todos os saltos necessários possuírem evidência RF observada.
- Se não houver caminho RF completo de ponta a ponta, informar claramente que **não existe rota RF completa observada** entre as duas estações no período selecionado.
- A análise deve respeitar o **período/filtro atual do mapa**, evitando usar enlaces históricos fora da janela selecionada sem indicação explícita.
- Reutilizar, sempre que possível, os dados e a lógica de **Topologia/Enlaces** já existentes para manter a classificação RF/APRS-IS coerente em toda a aplicação.
- Criar testes para localização por indicativo, rota RF simples, rota multi-hop, múltiplas rotas, ausência de caminho completo, mistura RF/APRS-IS e cálculo das distâncias.

## Implementado na v1.14.9 — Mapa: comprimento do enlace no hover

- Ao posicionar o mouse sobre um **enlace** no mapa, exibir também o **comprimento/distância total do enlace**.
- Calcular a distância entre os dois pontos/extremidades do enlace usando as coordenadas já disponíveis.
- Mostrar a distância em formato amigável, preferencialmente em **km** e, para enlaces muito curtos, em **m**.
- Reutilizar o mesmo painel/tooltip de hover já existente para informações do enlace, sem exigir clique.
- Manter o valor coerente independentemente do tipo de enlace (**RF** ou **Internet/APRS-IS**) e dos filtros/zoom do mapa.

# Backlog

## Implementado na v1.14.8 — Mensagens: resposta automática customizável

- Adicionar opção de **Resposta automática** para mensagens APRS recebidas.
- Permitir habilitar/desabilitar o recurso globalmente.
- Permitir configurar livremente o **texto da resposta automática**.
- Reutilizar o mesmo pipeline da aba **Mensagens**, incluindo validação de destino, fila de envio, roteamento, ACK/REJ, retries, persistência e logs.
- Responder somente a mensagens direcionadas à própria estação/SSID configurado, evitando responder a boletins, grupos, objetos, telemetria ou tráfego que não seja uma mensagem direta válida.
- Implementar proteção contra **loop de autoresposta**, impedindo duas estações com resposta automática de ficarem respondendo indefinidamente entre si.
- Aplicar cooldown por remetente e deduplicação por mensagem recebida.
- Permitir configurar um intervalo mínimo entre respostas automáticas ao mesmo remetente.
- Registrar no histórico/log que a mensagem foi enviada automaticamente.
- Exibir no histórico o texto original recebido e a resposta automática disparada.
- Respeitar o estado da conexão APRS-IS/TNC e as mesmas regras de segurança já existentes para TX.
- Persistir a configuração após reinício.
- Incluir testes de regressão para mensagem direta, mensagens duplicadas, ACK/REJ, cooldown, loop entre autorespostas e recurso desabilitado.


## Implementado na v1.14.8 — Configuração: retenção granular do banco

- Revisar o bloco **Saúde e retenção do banco** da aba **Configuração** para facilitar o controle do tamanho do SQLite.
- Permitir configurar separadamente a retenção de:
  - **Mensagens**;
  - **Tracklogs/posições**;
  - **Enlaces/Topologia**;
  - **Log APRS**;
  - **Frames TNC**;
  - **Decisões TNC**;
  - **Notificações**;
  - demais históricos persistentes relevantes que contribuam para o crescimento do banco.
- Para cada categoria, oferecer presets simples:
  - **Não apagar**;
  - **1 dia**;
  - **1 semana**;
  - **1 mês**.
- Preservar a possibilidade de políticas diferentes por categoria; não aplicar uma retenção global obrigatória.
- **Não alterar automaticamente** os valores existentes do usuário ao atualizar de versão.
- Executar a limpeza de forma incremental/segura, sem bloquear recepção APRS, TNC, mapa ou salvamento da Configuração.
- Manter a ação **Aplicar limpeza agora**, exibindo antes/depois a quantidade de registros removidos e, quando possível, o espaço recuperável/recuperado.
- A opção **Não apagar** deve desativar expurgo automático apenas daquela categoria.
- A retenção de **Enlaces/Topologia** deve preservar a coerência entre arestas, eventos e evidências RF/APRS-IS, sem deixar referências órfãs ou alterar a classificação dos enlaces atuais.
- Exibir uma explicação curta no bloco: retenções menores mantêm o banco mais leve; retenções longas preservam mais histórico.
- A política deve ser persistida no SQLite/configuração e reaplicada após reinício.
- Criar testes de regressão para cada preset e para migração de instalações que já possuam valores de retenção configurados.


## Implementado na v1.14.7

- Hardening do backend SQLite para bancos crescentes.
- Schema TNC inicializado uma vez por banco, em vez de repetido nos pollings.
- Snapshot pesado do mapa coalescido por 30 segundos sob RX APRS contínuo.
- Índices adicionais para packets e topologia; ajustes conservadores de cache e WAL.
- Política de retenção preservada sem redução automática para 5 dias.


## Concluído na v1.14.6

- **SAT/ISS:** removido integralmente do PT2VHF APRS Client.
- Removidos do build: backend orbital, rotas SAT, TLE/SGP4, cálculo de passagens, agenda, alarmes, mapa/footprint/trajetórias, seleção/favoritos, estações/mensagens SAT e beacon satelital.
- Removidos também assets JS/CSS, dependência `sgp4`, hooks de visibilidade, menu/aba SAT e pipeline TNC exclusivo de beacon satelital.
- **Direção arquitetural:** o cliente principal permanece focado em APRS terrestre; APRS via satélite fica reservado para uma futura aplicação dedicada.
- **Enlaces iGate/Internet:** corrigida a regressão da v1.14.5 em que evidência APRS-IS podia desaparecer quando o mesmo par também possuía evidência RF histórica.
- **Classificação:** RF e APRS-IS são preservados como observações independentes; RF real nunca é convertido em Internet apenas pelo papel de iGate.
- **Renderização:** enlace APRS-IS confirmado permanece tracejado e visível, inclusive em pares com evidência mista.
- **Testes/CI:** suites históricas deixaram de exigir o módulo SAT; adicionada regressão específica v1.14.6 e novo validador de produção.

## Pendência externa não bloqueante

- **SignPath Foundation (#1):** concluir onboarding, autorização do GitHub App, configuração da policy e assinatura Authenticode. Depende de aprovação/autorização externas e não bloqueia releases sem assinatura oficial.
- **Kenwood TM-D700:** validação física encerrada administrativamente em 07/10/2026. Não declarar RX/TX físico validado.

## Concluído na v1.14.5

- **#45 — Configuração:** corrigidos botão inferior Salvar, Salvar e sair, Descartar alterações e sair e Continuar na Configuração.
- O detector de alterações compara o formulário atual com um baseline persistido e não depende apenas de eventos anteriores.
- Respostas lentas de `GET /api/config` preservam campos editados enquanto a leitura estava pendente.
- **Descartar** é local e funciona sem backend; **Continuar** preserva a edição; **Salvar** exibe erro real quando o backend rejeita.
- O POST de Configuração envia apenas campos alterados; valores legados em campos não tocados não bloqueiam uma alteração independente.
- **#52 — SAT:** corrigido `$().forEach` nos serviços monitorados e isolada falha de renderização de detalhes da mensagem de erro orbital.
- **Regressão:** pytest e Playwright cobrem banco migrado, GET lento, botão inferior, erro real, descarte offline e serviços SAT.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.14.4

- **PU2MUS #48 — Alertas:** corrigido o erro `$(...).forEach is not a function`; autosave e botão Salvar alertas usam `querySelectorAll()`.
- **PU2MUS #49 — Backend/banco:** abertura da Configuração deixa de executar verificação profunda e contagens integrais do SQLite; a saúde rápida evita scans desnecessários em bancos maiores. O padrão de retenção **não foi reduzido para 5 dias**.
- **PU2MUS #50 — Mapa:** incluídos **15 min** e **30 min**, com suporte fracionário real no backend para topologia, RF ouvido, KML e Cobertura RF.
- **PU2MUS #51 — SAT:** layout responsivo reforçado, nomes podem quebrar linha, sidebar não é comprimida a poucos caracteres e o mapa orbital recalcula o tamanho após mudança da grade.
- **Configuração:** modal de saída com alterações pendentes corrigido, incluindo Salvar e sair, Descartar e sair, Cancelar, feedback e proteção contra duplo clique.
- **Estações:** clique direito em linha abre o compositor de Mensagem rápida e preenche o indicativo sem mudar de aba.
- **Mapa:** linhas Internet/APRS-IS observadas passam a respeitar apenas o toggle de Enlaces iGate/APRS-IS e não desaparecem pela ocultação independente de ícones/marcadores.
- **Topologia:** caminhos RF reais não são convertidos em Internet; qAR e qAr e evidência mista permanecem diferenciados.
- **Ícones do sistema:** desenho compacto com alto contraste aplicado aos builds Windows, Linux e macOS; logomarca oficial preservada na interface e no Manual PDF.
- **Regressão:** pytest e automação Playwright para os três botões de saída, botão direito e enlace Internet.

## Concluído na v1.14.3

- **Barra principal superior:** botão **Enviar Beacon** adicionado para disparo manual rápido.
- **Reuso seguro:** o novo botão e o botão da Configuração usam a mesma rotina `/api/beacon`, sem criar uma segunda lógica de transmissão.
- **Anti-duplo clique:** ambos os botões ficam temporariamente bloqueados enquanto o envio está em andamento.
- **Classificação de estações:** o frame bruto/path deixa de participar da decisão que bloqueia Mensagem/queries.
- **WIDE não é função:** usar `WIDE1-1`, `WIDE2-1` ou outro path de repetição não classifica a estação de origem como digipeater.
- **Evidência real de infraestrutura:** digipeater/iGate passa a ser reforçado por observação como hop intermediário utilizado ou iGate de q-construct.
- **Compatibilidade:** objetos/itens permanecem não interativos e infraestrutura comprovada continua protegida quando não há evidência de comunicação bidirecional.
- **Regressão:** testes cobrem estação comum/HT com WIDE e digipeater efetivamente observado.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

## Concluído na v1.14.2

- **Cobertura RF — heatmap:** nova camada Canvas sem dependência externa, usando somente estações/pontos com evidência RF persistida.
- **Qualidade RF:** quando disponíveis, RSSI/SNR influenciam a intensidade; quando não há qualidade, a densidade de recepções RF é usada como fallback.
- **Zoom adaptativo:** o raio visual do heatmap varia com o nível de zoom, mesclando mais em visão ampla e revelando maior detalhe ao aproximar.
- **Período:** a camada respeita o período selecionado no Mapa e é recarregada ao alterar esse filtro.
- **Mapa → Ver:** Cobertura RF passa a ser uma opção própria e acompanha **Selecionar tudo / Remover tudo**.
- **Segurança:** a camada é exclusivamente analítica e não gera tráfego APRS/RF adicional.
- **AIS — popup amigável:** ampliado com nome, MMSI, IMO, indicativo, tipo de embarcação, status de navegação, SOG, COG, proa, destino, ETA, calado, dimensões e fonte quando disponíveis.
- **AIS — códigos legíveis:** códigos numéricos comuns de tipo de embarcação e status de navegação passam a ser convertidos para descrições amigáveis.
- **AIS — imagem:** preservado o provedor externo configurável/cache por MMSI/IMO; quando houver correspondência confiável, a foto real é usada.
- **AIS — fallback:** sem foto real, o popup pode mostrar uma representação vetorial explicitamente identificada como **imagem ilustrativa do tipo**, sem sugerir que seja a embarcação exata.
- **AIS — robustez:** enriquecimento externo é assíncrono; falha ou ausência de imagem não bloqueia o popup textual.
- **Zoom do mapa:** o backlog antigo de passos intermediários é encerrado como obsoleto, pois o step já é configurável desde a v1.8.17.
- **Regressão:** suíte v1.14.2 cobre API de cobertura RF, qualidade/densidade, parser AIS, heatmap por zoom e fallback visual.
- **Produção:** release completa Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.


## Concluído na v1.14.1

- **Mapa SAT:** satélites selecionados, incluindo ISS/NORAD 25544, são desenhados imediatamente sem aguardar polling periódico.
- **Renderização progressiva:** posição atual primeiro; footprint/trajetórias em seguida, com fila limitada e deduplicação por NORAD.
- **Seleção padrão:** somente ISS em instalação nova; seleções persistidas, inclusive lista vazia, são preservadas.
- **Layout SAT:** mapa, estações recebidas e mensagens permanecem visíveis; detalhes, alertas, TLE, filtros, beacon e agenda ficam recolhidos por padrão.
- **Passagem:** contador à esquerda, grande e amarelo, identificando satélite e alternando para LOS durante passagem ativa.
- **Menu superior:** rótulo da aba alterado para **SAT**.
- **Notificações:** sino removido da barra superior; Centro de notificações mantido em Configuração.
- **Alertas:** opção “Estação apareceu” passa a respeitar imediatamente o estado desmarcado e a persistência no backend.
- **CI:** eliminada a corrida de publicação entre os workflows Full e Production.

## Concluído na v1.14.0

- **Satélites / ISS — operação APRS integrada:** estações recebidas, detalhes e envio de mensagens na própria aba.
- **Mensagens:** reutilização integral do mesmo motor da aba Mensagens, com rota, path, histórico, ACK/REJ, retries e persistência.
- **Estações:** filtros por contexto de satélites, passagem ativa, período, RF e presença de mensagens.
- **Seleção compacta:** painel recolhível, resumo de selecionados/favoritos e persistência do estado.
- **Pesquisa rápida:** nome, indicativo/designação e NORAD; ações Marcar tudo/Desmarcar tudo respeitam o resultado filtrado.
- **Contador de passagem:** movido para a barra operacional da aba, fonte maior em amarelo e universo restrito a selecionados/favoritos elegíveis.
- **Despertador:** usa o mesmo universo de satélites selecionados/favoritos do contador.
- **Beacon Satélite / curto:** perfil separado do terrestre, path específico, comentário curto, intervalo, elevação mínima, cobertura e parada no LOS.
- **Preview/histórico:** tamanho estimado do frame e registro de satélite, frequência, path, payload e resultado de TX.
- **Segurança do beacon:** consentimento explícito e reaproveitamento de todas as guardas do TNC/RF.
- **Saúde operacional do TNC:** componente restrito exclusivamente à aba TNC / RF.

## Concluído na v1.13.0

- **Satélites APRS:** catálogo padrão restrito a APRS confirmado; Packet/AX.25, GFSK e telemetria genérica permanecem categorias distintas.
- **Filtros avançados:** Somente APRS, APRS + Packet/AX.25 e todos os digitais.
- **Seleção rápida:** Marcar tudo / Desmarcar tudo respeitando os filtros visíveis e preservando favoritos.
- **Próxima passagem:** contador regressivo HH:MM:SS grande em amarelo ao lado de Satélites / ISS; durante cobertura conta até LOS.
- **Despertador de cobertura:** antecedência configurável, som próprio, popup, Centro de notificações, silenciar passagem, favoritar e abrir/seguir.
- **TLE multifonte:** CelesTrak Amateur, CelesTrak Stations e AMSAT nasabare com prioridade, teste, fallback e deduplicação por NORAD ID.
- **Scheduler orbital:** atualização automática diária interna, padrão 00:00 local, sem tarefas externas do sistema.
- **Controle operacional:** Monitorar, Ignorar e Fora do ar persistentes e independentes da atualização do TLE.
- **Serviços por satélite:** APRS, SSTV, Telemetria, Voz/FM e Packet/AX.25 configuráveis individualmente.
- **TM-D700/TM-D710:** perfis de equipamento e distinção explícita entre terminal/command mode e KISS.
- **Serial × RF:** baud rate da porta serial separado de packet RF 1200/9600.
- **Diagnóstico serial:** amostra limitada ASCII/HEX e estados específicos para terminal/TNC, sem recomendar menu KISS inexistente no TM-D700 em PKT.
- **Segurança TNC:** TX automático bloqueado no perfil serial terminal/PKT.
- **Autoteste TNC:** relatório por camadas de transporte, protocolo, AX.25, RX e modelo de TX; emissão RF física permanece explicitamente não validada.

## Concluído na v1.12.0

- **Satélites / ISS:** aba dedicada, mapa orbital, footprint, trajetória passada/futura, seleção múltipla, favoritos e modo seguir.
- **Passagens:** AOS/TCA/LOS, elevação máxima, azimutes, duração, frequências, modo e Doppler estimado.
- **TLE/catalogação:** SatNOGS + CelesTrak com cache local, atualização manual/automática, fonte e época do TLE.
- **Alertas espaciais:** antecedência e elevação mínima configuráveis, popup e Centro de notificações.
- **Mapa → Ver → Satélites / ISS:** camada opcional no mapa APRS principal, independente da aba orbital.
- **Topologia RF × Internet:** meio de recepção propagado até a topologia; removida a migração destrutiva legada e adicionado reparo histórico RF.
- **Classificação explicável:** RF direto do transporte, RF inferido do path, APRS-IS confirmado ou evidência mista.
- **Painéis destacáveis:** Mensagens, Estações e Logs com minimizar, maximizar/restaurar e fechar/encaixar no padrão Windows.
- **Geometria das janelas:** correção de restauração/redimensionamento, limites de viewport, persistência e reset de layout.
- **Logs:** nova aba destacável.
- **Menu superior:** removido o campo da extremidade esquerda da barra contextual do mapa.

## Concluído na v1.11.1

- **Mapa / topologia — RF até iGate:** qualquer evidência RF mantém o enlace como RF/linha contínua; tracejado somente para Internet/APRS-IS puro.
- **Evidência mista:** RF tem precedência visual, sem perder os contadores de observações via Internet.
- **Popup/hover:** mostra o meio real e informa evidência adicional APRS-IS quando existente.
- **Regressão:** testes específicos para RF → iGate, qAR/qAO e Internet-only.

## Concluído na v1.11.0

- **Alertas configuráveis:** corrigidos para respeitar preferências, usar transições reais e evitar duplicação.
- **TNC — contadores RX/TX:** reconciliados com evidência persistida da sessão.
- **TNC — health check:** classificação operacional automática e diagnóstico copiável.
- **TNC — simulador/autoteste:** KISS/AX.25 RX/TX/ACK sem hardware físico.
- **TNC — timeline:** histórico de mudanças de saúde/conectividade.
- **Centro de notificações:** histórico persistente com contador de não lidas.
- **SQLite:** saúde, retenção por categoria, limpeza manual e otimização.
- **Perfil operacional da estação:** pacotes, meios, mensagens, paths e “Ouvido por”.
- **Regressão:** testes dedicados aos recursos acima.

## Concluído na v1.9.0

- **Painéis destacáveis:** Mensagens e Estações podem ficar sobre o mapa, com arraste, redimensionamento, minimização, encaixe e persistência de tamanho/posição.
- **Busca Global:** estações, objetos, WX, AIS, repetidores e texto contextual.
- **Favoritos/estações avançados:** nome amigável, cor, nota e grupos.
- **Grupos de estações:** cadastro e associação persistentes, integrados à busca e organização.
- **Backup completo:** snapshot SQLite versionado com restauração validada e cópia automática pré-restauração.
- **Alertas configuráveis:** aparecimento/desaparecimento de estação, favorito, mensagem, TNC, APRS-IS e integridade SQLite.
- **Timeline unificada:** mensagens, posições, queries e tráfego RF em uma sequência cronológica.
- **Modo apresentação:** mapa em tela cheia para acompanhamento operacional/demonstrações.
- **TNC / RF:** diagnóstico assistido preservado e botão **Testar TNC** não destrutivo para KISS Serial/TCP e AGWPE.
- **TNC / RF — correção crítica:** eliminado o erro `$(...).forEach is not a function` que podia interromper a inicialização da aba.
- **AGWPE:** consolidado como terceiro transporte.
- **Estatísticas:** preservados saúde da rede, comparação de períodos e grafo “Quem fala com quem”.
- **Exportação/diagnóstico:** CSV, GeoJSON e pacote ZIP de suporte.
- **Linux ARM64:** mantido como build oficial e reconhecido pelo updater.
- **Regressão:** adicionada suíte específica v1.9.0 e validador de produção.

## Concluído na v1.8.18

- **TNC / RF — AGWPE:** transporte AGWPE TCP em raw AX.25, configurável por host, porta e radio port, preservando KISS TCP/Serial.
- **Simulador KISS:** cenários de fragmentação, duplicidade e multi-hop para regressão sem rádio físico.
- **Busca rápida:** pesquisa por indicativo completo/parcial no Mapa, priorizando correspondência exata e favoritos.
- **Painel lateral de estação:** visão responsiva com dados principais e atalhos para Mensagens e Log.
- **Quem fala com quem:** grafo visual SVG interativo derivado das interações observadas.
- **Estatísticas:** painel de saúde da rede com RF × APRS-IS, duplicados, ACK, RTT e estações novas/desaparecidas.
- **Comparação entre períodos:** período atual × anterior de mesma duração, com deltas absolutos e percentuais.
- **Exportação:** CSV e GeoJSON por período.
- **Diagnóstico:** resumo de integridade SQLite e pacote ZIP sanitizado para suporte.
- **Linux ARM64:** pipeline oficial e updater consciente da arquitetura.
- **Atualização:** seleção de pacote por arquitetura para impedir atualização Linux cruzada x86_64/ARM64.
- **Idiomas:** novos recursos da v1.8.18 usam PT-BR/EN/ES/FR, preservando termos técnicos de protocolo.
- **Produção:** Windows x64/ARM64, Linux x86_64/ARM64, macOS ARM64/Intel e Manual PDF.

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

## Concluído na v1.10.0

- **QRZ.com:** perfil enriquecido opcional por API XML oficial, com foto principal quando disponibilizada, nome, cidade, estado/região, país, grid, link, cache e fallback.
- **AIS:** provedor externo configurável por MMSI/IMO, cache e ausência de scraping por nome.
- **Métricas RF:** arquitetura para RSSI, SNR, DCD, frequência, canal e origem; ausência de dado permanece explícita.
- **TM-D700:** diagnóstico específico em PKT e roteiro de validação física. A validação física real permanece como requisito externo, não como pendência de software.
- **Portable:** soak test de 24 h, 72 h e 7 dias com relatório automático e detecção de crescimento anormal de memória.
- **Bancos antigos:** matriz automatizada de migração histórica integrada à CI.
- **Idiomas:** auditoria contínua, paridade de dicionários e scanner de strings visíveis integrados à CI.

## Validações externas encerradas administrativamente

- **Kenwood TM-D700 — teste físico externo:** retirado do backlog ativo em 07/10/2026, por decisão do mantenedor. Diagnóstico em software concluído. **RX/TX físico com rádio real não foi validado**; o encerramento é administrativo, não comprovação de funcionamento em RF.

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


