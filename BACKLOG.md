# Backlog

Este arquivo registra funcionalidades planejadas que ainda **não fazem parte da versão em desenvolvimento atual**.

## Topologia observada APRS no mapa

**Objetivo:** representar visualmente como o tráfego APRS observado chega à rede, conectando estações, digipeaters e IGates quando houver evidência suficiente no path recebido.

### Escopo planejado

- Adicionar no **Mapa** um controle **Topologia: Ligada/Desligada**.
- Desenhar linhas apenas entre nós identificáveis e com posição conhecida; nunca inventar coordenadas.
- Interpretar o path APRS para identificar digipeaters efetivamente usados, incluindo indicativos marcados com `*`.
- Interpretar constructos APRS-IS como `qAR` e `qAO` para identificar o IGate que recebeu o pacote por RF quando aplicável.
- Não criar enlace RF para tráfego puramente Internet, como caminhos `TCPIP*`/equivalentes sem evidência de RF.
- Tratar aliases genéricos como `WIDE1-1` e `WIDE2-1` como informação de roteamento, não como estação geolocalizável.
- Persistir enlaces observados em uma estrutura própria no SQLite, com pelo menos:
  - origem;
  - destino;
  - tipo do enlace;
  - quantidade de pacotes observados;
  - primeira observação;
  - última observação;
  - IGate associado, quando conhecido.
- Permitir filtros temporais da topologia, por exemplo **1 h, 6 h, 24 h e 7 dias**.
- Ao clicar em uma linha, exibir estatísticas do enlace: origem, destino, quantidade de pacotes, primeira/última observação, caminhos observados e IGate mais frequente quando disponível.
- Diferenciar visualmente enlaces RF observados e entrada no IGate.
- Considerar uma evolução posterior com métricas de uso de digipeaters, IGates mais ativos, enlaces que desapareceram e visão histórica da malha.

### Critério de nomenclatura

A função deverá ser apresentada como **Topologia observada**, evitando sugerir que o APRS-IS fornece uma medição RF física completa da rede. As linhas representarão relações inferidas diretamente dos paths e metadados APRS recebidos.



## Mensagens longas com envio automático em partes

**Objetivo:** permitir que o usuário escreva uma mensagem maior no campo de composição, sem precisar dividir manualmente o texto para respeitar o limite de cada mensagem APRS.

### Escopo planejado

- Remover do campo de edição o limite visual atual de 63/67 caracteres.
- Permitir a digitação de mensagens longas em uma única caixa de texto.
- No momento do envio, dividir automaticamente o conteúdo em várias mensagens APRS compatíveis com o limite de payload do protocolo.
- Preferir a quebra entre palavras, evitando cortar palavras ao meio sempre que possível.
- Identificar as partes de forma clara, por exemplo `[1/3]`, `[2/3]`, `[3/3]`, contabilizando esse marcador dentro do limite de cada pacote.
- Manter a ordem correta de transmissão das partes.
- Para mensagens individuais, gerar um ID APRS próprio para cada parte e acompanhar ACK/REJ separadamente.
- Exibir no histórico uma indicação de que as linhas pertencem à mesma mensagem longa, preservando a ordem das partes.
- Informar antes do envio em quantas partes o texto será transmitido.
- Evitar envio simultâneo excessivo: transmitir as partes de forma sequencial, com pequeno intervalo e respeitando confirmação/retry quando aplicável.
- Caso uma parte falhe, indicar exatamente qual parte não foi confirmada e permitir novo envio.
- Manter compatibilidade com clientes APRS comuns: o destinatário receberá as partes como mensagens APRS individuais numeradas, sem depender de um protocolo proprietário de remontagem.

### Observação

O limite efetivo de texto por parte depende do formato da mensagem APRS e dos caracteres usados para identificação da parte e do ID da mensagem. O cliente deverá calcular dinamicamente o tamanho disponível, em vez de assumir um valor fixo para todos os casos.


## Reorganização dos contadores e ações fora do mapa

**Objetivo:** deixar a tela do Mapa mais limpa, removendo a barra flutuante superior e levando contadores e ações para as abas correspondentes.

### Escopo planejado

- Remover completamente a barra superior atualmente exibida sobre o **Mapa**.
- Retirar do mapa:
  - contador de estações recebidas;
  - contador de pacotes APRS-IS;
  - filtro APRS-IS ativo;
  - última atualização;
  - botão **Apagar tracklogs**;
  - botão **Apagar estações**.
- Na aba **Estações**:
  - mostrar a quantidade total de estações recebidas;
  - manter a ação **Limpar estações** nessa própria aba;
  - concentrar também a limpeza de tracklogs junto aos controles de estações, evitando ações de manutenção sobre o mapa.
- Na aba **Mensagens**:
  - mostrar a quantidade total de mensagens armazenadas/exibidas;
  - manter a ação **Limpar mensagens** nessa própria aba.
- O mapa deverá ficar dedicado apenas à visualização geográfica das estações, símbolos, tracklogs e demais camadas.
- Informações técnicas como quantidade de pacotes APRS-IS, filtro ativo e última atualização poderão ser mantidas em uma área de status/diagnóstico fora do mapa, caso ainda sejam úteis, sem recriar a barra flutuante.

