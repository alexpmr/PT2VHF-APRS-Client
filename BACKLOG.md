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



## Encerrar completamente ao fechar a janela

**Objetivo:** fazer o fechamento da janela principal encerrar de fato o PT2VHF APRS Client, sem manter serviços ou ícone na bandeja do Windows.

- Ao clicar no **X** da janela principal, encerrar completamente a aplicação.
- Desconectar do **APRS-IS** antes de finalizar.
- Encerrar o servidor local Flask/Waitress.
- Remover o ícone da bandeja do Windows.
- Encerrar threads/processos auxiliares, incluindo loops de beacon, monitoramento e atualização.
- Não manter o aplicativo ativo junto ao relógio/área de notificação após o fechamento da janela.
- Preservar uma saída limpa, garantindo que o SQLite finalize as operações pendentes antes do encerramento.
- O menu da bandeja poderá continuar existindo enquanto a janela estiver aberta/minimizada, mas o fechamento pelo **X** passará a significar **Sair**.
- Se for mantida uma opção de minimizar para a bandeja, ela deverá ser uma ação explícita separada, e não o comportamento padrão do botão **X**.

