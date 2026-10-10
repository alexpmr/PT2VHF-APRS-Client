## Novo — Indicador global de processamento em primeiro plano

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


