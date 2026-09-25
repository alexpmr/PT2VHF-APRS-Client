# Backlog

Os itens registrados até **24/09/2026** foram incorporados na **v1.6.1**.

## Concluído na v1.6.1

- atualização OTA: verificar, baixar e instalar ao fechar habilitados por padrão em novas instalações;
- verificação automática da Release a cada 5 minutos, sem consultas sobrepostas;
- mensagens longas divididas sem marcadores visíveis de parte e com quebra por palavras;
- nova aba superior **Análise** com métricas, rankings, comparação histórica e replay;
- análise removida da página Configuração, mantendo ali somente opções visuais de mapa/topologia;
- botão **Mostrar log** no popup das estações;
- remoção do bloco introdutório da página Configuração;
- legenda dinâmica dos tipos de linhas diretamente no Mapa;
- animação do tráfego APRS em modos Histórico/Ao vivo, incluindo múltiplos enlaces simultâneos;
- sinal sonoro de atividade e destaque vermelho temporário da estação transmissora;
- período **Completo** como padrão para Topologia observada e Análise;
- estações favoritas com estrela amarela, persistência e fixação/priorização em Estações e Mensagens;
- botão **Não lidas** na aba Mensagens, com estado lida/não lida persistido.

Novas demandas serão adicionadas abaixo deste ponto para as próximas versões **1.6.x**.


## Replay da Rede com linha do tempo interativa

**Objetivo:** permitir voltar no tempo e reproduzir visualmente o tráfego APRS da rede usando uma barra temporal semelhante à navegação de um vídeo.

- Adicionar um modo **Replay da Rede** integrado à aba **Análise** e ao **Mapa**.
- Exibir uma **barra de tempo horizontal arrastável**, semelhante ao controle de posição de um vídeo/YouTube.
- O usuário deve poder mover o cursor para qualquer instante do histórico disponível e iniciar a reprodução a partir daquele ponto.
- Exibir a **data e hora exatas** correspondentes à posição atual do cursor.
- Incluir controles:
  - **Play/Pausa**;
  - **voltar ao início**;
  - **avançar/recuar** por eventos ou por intervalo de tempo;
  - botão **Ao vivo** para retornar ao momento atual;
  - velocidades de reprodução, incluindo pelo menos **0,25x, 0,5x, 1x, 2x, 5x, 10x e 20x**.
- Permitir selecionar/reproduzir apenas um intervalo específico do histórico.
- Mostrar na própria timeline uma representação da **densidade de tráfego ao longo do tempo**, por exemplo pequenos picos/histograma para períodos com maior número de pacotes.
- Durante o replay, animar os pacotes pelos caminhos realmente observados:
  - **Estação → Digipeater**;
  - **Digipeater → Digipeater**;
  - **Digipeater → IGate**;
  - demais segmentos identificáveis no path APRS/TNC2.
- Permitir que um mesmo pacote percorra **múltiplos enlaces simultaneamente** quando o histórico indicar propagação concorrente.
- Ao mover manualmente a barra para outro instante, interromper as animações em andamento, limpar o estado transitório e reconstruir o mapa para o novo ponto temporal.
- Durante a reprodução, os enlaces utilizados podem **acender temporariamente** e desaparecer gradualmente, permitindo visualizar quais partes da rede estavam efetivamente em uso.
- Quando vários pacotes utilizarem o mesmo enlace em curto intervalo, permitir intensificar temporariamente brilho/espessura sem alterar a configuração permanente da topologia.
- Ao pausar o replay, permitir clicar em um pacote/evento para ver, quando disponível:
  - origem;
  - destino;
  - data/hora;
  - path APRS;
  - tipo do pacote;
  - segmentos percorridos.
- Não inventar posições ou enlaces quando o histórico não tiver informação suficiente.
- Para históricos grandes, não carregar todos os eventos no navegador de uma vez: implementar **carregamento por janela temporal/chunks** em torno da posição atual da timeline.
- O backend deve suportar busca eficiente por intervalo de tempo e paginação/índice temporal para manter o replay fluido mesmo após meses de histórico.
- A timeline deve permanecer sincronizada com a animação, avançando conforme os eventos são reproduzidos.
- A estrutura deve reutilizar a base já existente de **animação Histórico/Ao vivo**, transformando-a em uma experiência de “DVR da rede”.


## Som e animação de atividade somente para estações visíveis no mapa

**Objetivo:** limitar os avisos de atividade ao contexto visual atual do usuário, evitando som ou destaque de estações fora da área exibida no zoom corrente.

- O **sinal sonoro de atividade** e a **animação/destaque vermelho do marcador** devem ocorrer somente para estações que estejam **dentro da área atualmente visível do mapa**.
- Antes de tocar o som ou animar o marcador, verificar se a posição conhecida da estação está contida nos limites atuais do mapa (`map.getBounds()` ou equivalente).
- Se a estação estiver fora da área visível, **não tocar som** e **não executar a animação visual**.
- A regra deve considerar o **zoom e o enquadramento atuais** do mapa; ao mover ou alterar o zoom, o conjunto de estações elegíveis muda imediatamente.
- Não usar distância fixa, estado, cidade ou raio geográfico como critério principal: a referência deve ser exatamente o que está aparecendo na tela naquele momento.
- Se a estação não tiver coordenadas válidas, não gerar som nem animação de atividade.
- Aplicar a mesma regra tanto no modo normal quanto durante o modo **Ao vivo** da animação de tráfego.
- No **Replay da Rede/Histórico**, por padrão animar somente eventos cujo trecho ou estação esteja visível no mapa, evitando efeitos de atividade fora do enquadramento atual.
- Se um pacote tiver origem fora da tela, mas algum trecho do seu caminho estiver visível, permitir animar apenas os segmentos visíveis, sem provocar som da estação de origem fora da tela.
- O objetivo é evitar, por exemplo, que o cliente toque aviso de uma estação em outro estado ou região que esteja sendo recebida pelo APRS-IS, mas não esteja visível no zoom atual.


## Mover controles da animação do tráfego para a parte inferior do Mapa

**Objetivo:** manter os controles do replay/animação junto da visualização em que o usuário acompanha os pacotes.

- Remover o bloco **Animação do tráfego APRS** da aba **Análise**.
- Exibir esse bloco na aba **Mapa**, fixado na **parte inferior da tela**, imediatamente abaixo da área do mapa ou sobreposto em uma faixa inferior própria.
- Manter no novo local todos os controles atuais:
  - **Modo** (Histórico/Ao vivo);
  - **Velocidade**;
  - **Início**;
  - **voltar**;
  - **Play/Pausa**;
  - **avançar**;
  - contadores de reproduzidos/pendentes;
  - horário atual da reprodução;
  - velocidade atual.
- Integrar nesse mesmo espaço, futuramente, a barra temporal do **Replay da Rede**, evitando controles duplicados em abas diferentes.
- A aba **Análise** deve continuar concentrando métricas, rankings, comparações e comandos analíticos, enquanto a reprodução visual do tráfego fica junto do **Mapa**.
- A faixa inferior deve ser responsiva e não reduzir excessivamente a área útil do mapa; em janelas menores, permitir layout compacto/recolhível.
- Ao alternar entre Mapa e outras abas, preservar o estado da animação (posição, modo, velocidade e Play/Pausa).


## Controles da animação de tráfego na parte inferior do Mapa

**Objetivo:** manter os controles do replay/animação junto da visualização onde os pacotes são efetivamente acompanhados.

- Mover o bloco **Animação do tráfego APRS** da aba **Análise** para a aba **Mapa**.
- Posicionar o painel na **parte inferior da tela do Mapa**, abaixo/ao lado da área principal conforme o espaço disponível.
- Manter no painel os controles de:
  - modo **Histórico/Ao vivo**;
  - velocidade;
  - **Início**;
  - voltar;
  - **Play/Pausa**;
  - avançar;
  - contadores de reproduzidos/pendentes;
  - horário atual;
  - velocidade atual.
- Não duplicar o painel na aba Análise; após a mudança, os controles devem existir somente no Mapa.
- A aba Análise continua responsável por métricas, rankings, seleção de período e indicadores analíticos.
- O painel deve permanecer integrado ao futuro **Replay da Rede** com linha do tempo interativa.
- Em telas menores, permitir layout compacto para não reduzir excessivamente a área útil do mapa.


## Desativar auto-update e manter apenas aviso de nova versão

**Objetivo:** eliminar travamentos e regressões associados ao download/instalação automática, mantendo somente a detecção de novas versões.

- **Desativar completamente o auto-update** do aplicativo.
- O cliente deve continuar consultando a versão mais recente publicada e indicar claramente quando houver uma versão nova.
- Manter a verificação automática de versão, mas **não baixar arquivos automaticamente**.
- **Não instalar atualizações automaticamente ao fechar**.
- Remover/desabilitar as opções de Configuração:
  - **Baixar atualização automaticamente**;
  - **Instalar atualização automaticamente ao fechar**.
- Manter apenas:
  - **Verificar atualizações automaticamente**;
  - **Verificar atualização agora**.
- Quando houver nova versão, mostrar aviso com:
  - versão instalada;
  - versão disponível;
  - notas da release, quando disponíveis;
  - botão/link para abrir a página oficial da Release/Download.
- O usuário deve fazer o download e a instalação manualmente.
- Não iniciar PowerShell, instalador, DMG, AppImage substituta ou qualquer processo de atualização automática ao encerrar o programa.
- Não preparar atualização em background e não deixar arquivo pendente para instalação posterior.
- Manter a verificação de integridade/download somente para fluxos manuais que vierem a ser explicitamente reintroduzidos no futuro.
- Preservar a checagem periódica de nova versão sem bloquear a interface nem interferir no encerramento do aplicativo.
- Esta mudança deve priorizar **estabilidade** e evitar que o mecanismo de atualização cause travamentos para usuários.


## Remover “Animar período” da aba Análise

**Objetivo:** concentrar todos os controles de animação/replay exclusivamente na aba Mapa.

- Remover o botão **Animar período** da aba **Análise**.
- A aba **Análise** deve permanecer focada em métricas, rankings, períodos e indicadores da rede.
- Toda reprodução visual de tráfego, replay histórico e navegação temporal deve ficar na aba **Mapa**, junto ao painel inferior de animação.
- Não manter controles de animação duplicados entre Análise e Mapa.
- Quando o usuário alterar o período na aba Análise, o período selecionado pode continuar sincronizado com o Replay da Rede no Mapa, mas a reprodução deverá ser iniciada/controlada somente pelo painel do Mapa.


## Renomear ação do popup da estação para “Ver logs”

**Objetivo:** padronizar o acesso rápido ao histórico da estação a partir do Mapa.

- No popup exibido ao clicar em uma estação, usar o botão **Ver logs**.
- Ao clicar em **Ver logs**, abrir automaticamente a aba **Log**.
- Aplicar no campo de filtro o **indicativo completo da estação**, incluindo SSID quando houver.
- Atualizar imediatamente a listagem para mostrar os registros relacionados à estação.
- Dar foco visual ao campo de filtro para deixar claro qual estação está sendo analisada.
- Esta demanda substitui a nomenclatura anterior **Mostrar log**; manter apenas **Ver logs** na interface.
