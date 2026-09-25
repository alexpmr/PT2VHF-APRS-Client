# Backlog

Os itens registrados até **24/09/2026** foram incorporados na **v1.6.1**.

## Concluído na v1.6.1

- atualização OTA: verificar, baixar e instalar ao fechar habilitados por padrão em novas instalações, preservando preferências existentes;
- mensagens longas divididas sem marcadores visíveis de parte e com quebra por palavras;
- nova aba superior **Análise** com métricas, rankings, comparação histórica e animação temporal;
- análise removida da página Configuração, mantendo ali somente opções visuais de mapa/topologia;
- botão **Mostrar log** no popup das estações, abrindo o Log filtrado pelo indicativo completo;
- remoção do bloco introdutório da página Configuração.

Novas demandas serão adicionadas abaixo deste ponto para as próximas versões **1.6.x**.


## Legenda dos tipos de linhas no mapa

**Objetivo:** deixar claro, diretamente na tela do Mapa, o significado visual de cada tipo de linha exibida.

- Adicionar uma **legenda fixa e discreta na tela do Mapa**, sem exigir acesso à Configuração.
- A legenda deve identificar pelo menos:
  - **Tracklog da estação**;
  - **Enlace RF observado**;
  - **Enlace via IGate/APRS-IS**;
  - **Linhas da animação temporal**, quando a animação estiver ativa.
- A amostra de cada item da legenda deve usar a **mesma cor, espessura e estilo de linha** atualmente configurados para o mapa.
- Se o usuário alterar as cores ou a espessura em Configuração, a legenda deve ser atualizada imediatamente.
- Itens que não estiverem ativos/visíveis no mapa podem ser ocultados ou apresentados de forma atenuada.
- A legenda deve funcionar nos temas Claro e Escuro e não deve cobrir os controles principais do Leaflet.
- Em janelas menores, permitir formato compacto/recolhível para evitar ocupar área excessiva do mapa.


## Animação do tráfego APRS no mapa

**Objetivo:** visualizar dinamicamente o fluxo de pacotes APRS entre estações, digipeaters e IGates, em um modelo semelhante à animação já usada no Traffic Analyzer da rede Meshtastic.

- Adicionar um modo de **animação de tráfego no Mapa**, usando o histórico de pacotes/topologia já registrado pelo cliente.
- Representar cada pacote como um **pulso/partícula em movimento** ao longo do caminho observado entre os nós envolvidos.
- Quando o path tiver múltiplos saltos, permitir que a animação mostre o pacote **percorrendo mais de um enlace simultaneamente**, em vez de obrigatoriamente esperar um trecho terminar para iniciar o seguinte.
- O efeito deve permitir visualizar a propagação do mesmo pacote por vários segmentos do caminho quase ao mesmo tempo, reproduzindo melhor a sensação de tráfego se espalhando pela rede.
- Quando houver múltiplas cópias/encaminhamentos observados do mesmo pacote, animar os caminhos concorrentes de forma sincronizada quando os timestamps permitirem essa correlação.
- Diferenciar visualmente os trechos:
  - **Estação → Digipeater**;
  - **Digipeater → Digipeater**;
  - **Digipeater → IGate**;
  - **Estação → IGate**, quando não houver digipeater intermediário;
  - **Tráfego via APRS-IS**, quando aplicável e identificável.
- Usar o path APRS/TNC2 observado para reconstruir o caminho do pacote sempre que houver informação suficiente, sem inventar enlaces inexistentes.
- Quando um nó do caminho não tiver coordenadas conhecidas, não criar posição artificial; indicar o trecho como incompleto ou ignorá-lo na animação.
- A animação deve poder operar em dois modos:
  - **Ao vivo** — animando pacotes conforme chegam;
  - **Histórico** — reproduzindo um período selecionado.
- Incluir controles semelhantes aos do Traffic Analyzer:
  - **Play/Pausa**;
  - **voltar ao início**;
  - **avançar/recuar**;
  - **velocidade de reprodução** (ex.: 0,5x, 1x, 2x, 5x, 10x);
  - seleção de período/histórico.
- Exibir indicadores durante a reprodução, como:
  - quantidade de pacotes/eventos reproduzidos;
  - fila de eventos ainda pendentes;
  - timestamp atual da reprodução;
  - velocidade ativa.
- Permitir pausar a animação sem perder a posição atual e retomar do mesmo ponto.
- Ao selecionar um pacote/pulso, quando viável, mostrar detalhes como origem, destino, path, horário e tipo do pacote.
- Integrar a animação com a nova aba **Análise**, deixando os controles analíticos nessa aba e a visualização gráfica no **Mapa**.
- Manter a animação independente das linhas estáticas de topologia: o usuário deve poder ver somente a animação, somente a topologia ou ambas.
- A nova legenda de tipos de linhas do mapa deve incluir também o elemento visual usado para representar **pacotes em movimento**.
- Projetar a estrutura para funcionar bem com grande volume de tráfego, usando fila limitada, agregação/descartes controlados e sem travar a interface.


## Aviso sonoro e destaque visual de estação transmitindo

**Objetivo:** identificar imediatamente, no mapa, qual estação acabou de transmitir um pacote APRS.

- Ao receber um novo pacote de uma estação conhecida, emitir um **sinal sonoro curto** indicando atividade.
- Ao mesmo tempo, destacar temporariamente o **ícone da estação transmissora no mapa**.
- Durante o destaque, o marcador deve:
  - mudar temporariamente para **vermelho** ou receber um halo/contorno vermelho;
  - executar uma **animação curta de pulso/piscar**;
  - retornar automaticamente ao estilo normal após alguns segundos.
- A animação deve ocorrer exatamente no marcador da estação que originou o pacote, facilitando identificar visualmente quem transmitiu.
- Se várias estações transmitirem em sequência, cada marcador deve poder animar de forma independente.
- O destaque não deve alterar permanentemente o símbolo APRS original da estação.
- Adicionar em Configuração uma opção para **ativar/desativar o sinal sonoro de atividade da rede**, separada do alerta sonoro de mensagem pessoal.
- Adicionar uma opção para **ativar/desativar o destaque visual de transmissão**, permitindo usar apenas som, apenas animação ou ambos.
- Evitar reprodução excessiva de áudio em períodos de tráfego intenso, aplicando um pequeno cooldown/agregação sonora quando necessário.
- Integrar esse efeito à futura animação de tráfego: quando um pacote iniciar sua animação, o marcador da estação de origem deve pulsar em vermelho no mesmo instante.
