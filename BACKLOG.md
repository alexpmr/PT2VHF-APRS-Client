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
