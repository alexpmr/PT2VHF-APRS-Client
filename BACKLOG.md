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

