# Backlog

Este arquivo registra funcionalidades planejadas que **ainda não fazem parte da versão atual**.

## Mensagens longas — melhorias futuras

A v0.3.1 implementa o envio automático em partes APRS, numeração, IDs individuais e indicação verde por ACK. Permanecem como evoluções futuras:

- permitir reenviar diretamente apenas uma parte que tenha recebido `REJ` ou permaneça sem ACK;
- apresentar um status agregado da mensagem longa, por exemplo `2/3 confirmadas` ou `Todas confirmadas`;
- permitir configurar política de retry/timeout sem gerar tráfego APRS excessivo.

## Topologia observada — análises futuras

A v0.3.1 implementa a topologia observada básica, persistência dos enlaces e filtros de 1 h, 6 h, 24 h e 7 dias. Permanecem como evoluções futuras:

- ranking de digipeaters mais utilizados;
- ranking de IGates mais ativos;
- identificação de enlaces que desapareceram ou mudaram de frequência de uso;
- histórico comparativo por período;
- métricas agregadas por nó/enlace;
- eventual animação temporal do tráfego observado.


## Opção para abrir também no navegador

**Objetivo:** manter a janela integrada como comportamento padrão e permitir que o navegador seja aberto apenas quando o usuário desejar.

- Corrigir o comportamento atual em que o navegador também é aberto junto com a janela principal.
- Por padrão, ao iniciar o PT2VHF APRS Client, abrir **somente a janela integrada WebView2**.
- Adicionar em **Configuração** a opção **“Abrir também no navegador ao iniciar”**.
- A opção deverá vir **desligada por padrão** em novas instalações.
- Quando desligada, não abrir Chrome, Edge ou outro navegador durante a inicialização normal.
- Quando ligada, iniciar a janela integrada normalmente e, adicionalmente, abrir a interface local no navegador padrão.
- Persistir essa preferência no banco SQLite/configuração exportável.
- Manter o parâmetro de diagnóstico `--browser` como forma explícita de abrir pelo navegador, independentemente da preferência salva.
- Atualizar Ajuda e README para documentar a diferença entre:
  - janela integrada;
  - opção de abrir também no navegador;
  - modo de diagnóstico `--browser`.

