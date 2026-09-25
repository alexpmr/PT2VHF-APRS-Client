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


## Período “Completo” na Topologia observada

**Objetivo:** permitir visualizar toda a topologia histórica disponível no banco, sem limitar obrigatoriamente a análise às janelas parciais de horas ou dias.

- No controle **Mapa → Topologia observada**, adicionar a opção **Completo**.
- **Completo deve ser a opção padrão**.
- Manter também as opções parciais já existentes por período, como:
  - **1 hora**;
  - **6 horas**;
  - **24 horas**;
  - **7 dias**;
  - demais períodos em horas/dias que forem disponibilizados.
- Ao selecionar **Completo**, carregar todos os enlaces de topologia ainda disponíveis no histórico/banco de dados, respeitando apenas os limites técnicos de retenção definidos pelo aplicativo.
- A opção **Completo** deve valer também para a nova aba **Análise**, quando aplicável, para que rankings, métricas e comparação possam usar todo o histórico disponível.
- O estado selecionado deve ser persistido entre execuções.
- Se o volume de dados completo for muito grande, carregar/processar de forma eficiente para não travar o mapa nem a interface.
- Exibir claramente quando o usuário estiver vendo **Topologia completa** em vez de uma janela temporal parcial.


## Verificação de atualização a cada 5 minutos

**Objetivo:** reduzir o intervalo entre a publicação de uma nova versão e sua detecção pelo cliente.

- Quando **Verificar atualizações automaticamente** estiver habilitado, consultar a Release oficial a cada **5 minutos**.
- Substituir o intervalo atual de verificação periódica pela cadência de **300 segundos**.
- Manter a verificação inicial na abertura do aplicativo.
- Evitar verificações simultâneas ou sobrepostas se uma consulta anterior ainda estiver em andamento.
- Respeitar normalmente as opções de **baixar automaticamente** e **instalar automaticamente ao fechar**.
- Em caso de falha de rede ou indisponibilidade do GitHub, não interromper o funcionamento do cliente; tentar novamente no próximo ciclo.
- Não gerar pop-ups repetitivos para a mesma versão já detectada/baixada.
