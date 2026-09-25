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
