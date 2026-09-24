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

**Objetivo:** permitir que o usuário escreva uma mensagem maior no campo de composição, sem precisar dividi-la manualmente para respeitar o limite de cada mensagem APRS.

### Comportamento do campo de mensagem

- Remover do campo de edição o limite visual atual de 63/67 caracteres.
- Permitir a digitação de mensagens longas em uma única caixa de texto.
- **Enter** passa a enviar a mensagem.
- **Shift+Enter** insere uma nova linha sem enviar.
- Antes do envio, informar quantas partes APRS serão necessárias quando o texto ultrapassar o limite de uma única mensagem.

### Fragmentação e transmissão APRS

- No momento do envio, dividir automaticamente o conteúdo em várias mensagens APRS compatíveis com o limite efetivo do protocolo.
- Calcular dinamicamente o tamanho útil de cada parte, considerando destino, identificador da mensagem, numeração da parte e demais caracteres de controle.
- Preferir quebra entre palavras, evitando cortar palavras ao meio sempre que possível.
- Identificar as partes de forma clara, por exemplo `[1/3]`, `[2/3]`, `[3/3]`, contabilizando esse marcador dentro do limite do pacote.
- Manter a ordem correta de transmissão.
- Para mensagens individuais, gerar um ID APRS próprio para cada parte.
- Transmitir as partes de forma sequencial, com intervalo apropriado e controle de ACK/REJ individual.
- Não depender de um protocolo proprietário para remontagem: o destinatário recebe mensagens APRS normais, numeradas e compatíveis com outros clientes.

### ACK e indicação visual

- Cada parte enviada deve aparecer separadamente no histórico enquanto aguarda confirmação.
- Ao receber o **ACK** correspondente a uma parte, essa linha passa para **verde** e o status exibido será **Lido**.
- Partes ainda sem ACK permanecem com aparência de pendentes/enviadas.
- Em caso de `REJ`, destacar a parte como rejeitada.
- Se apenas algumas partes forem confirmadas, mostrar exatamente quais já receberam ACK e quais ainda aguardam confirmação.
- Permitir reenviar somente a parte que falhou ou não foi confirmada, sem retransmitir obrigatoriamente toda a mensagem longa.
- Opcionalmente, apresentar também um status agregado da mensagem longa, por exemplo `2/3 confirmadas` ou `Todas confirmadas`.

### Observação

No APRS, o **ACK confirma o recebimento da mensagem pelo cliente remoto**, mas não comprova necessariamente que uma pessoa leu o conteúdo. A interface poderá continuar usando o rótulo amigável **Lido** em verde, mas a lógica interna deverá tratar isso tecnicamente como confirmação APRS de recebimento.


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



## Simplificação do título/cabeçalho da aplicação

**Objetivo:** deixar o cabeçalho principal mais limpo e direto.

- Remover a frase **“Cliente APRS-IS com banco local SQLite”** do título/cabeçalho exibido na interface.
- Manter como identificação principal **PT2VHF APRS Client**.
- Exibir no cabeçalho, junto ao título, os contadores dinâmicos:
  - **Estações recebidas:** `xx`
  - **Pacotes APRS-IS:** `xx`
- Apresentação sugerida: **Estações recebidas:** xx — **Pacotes APRS-IS:** xx.
- Atualizar os dois valores automaticamente conforme o cliente recebe novas estações/pacotes, sem exigir recarregar a interface.
- Preservar informações técnicas sobre APRS-IS e SQLite apenas na documentação/Ajuda, e não no título principal da aplicação.



## Remoção da barra flutuante do mapa

**Objetivo:** eliminar completamente a barra horizontal flutuante exibida sobre o mapa.

- Remover do mapa a barra que atualmente mostra:
  - **Estações recebidas**;
  - **Pacotes APRS-IS**;
  - filtro ativo;
  - última atualização;
  - botão **Apagar tracklogs**;
  - botão **Apagar estações**.
- O mapa deve ficar visualmente limpo, dedicado apenas às estações, símbolos, tracklogs e demais camadas.
- Os contadores principais deverão ser reposicionados no cabeçalho/título da aplicação no formato:
  - **Estações recebidas: XX - Pacotes APRS-IS: XX**
- As ações de limpeza deverão permanecer nas abas correspondentes:
  - **Mensagens** → limpar mensagens;
  - **Estações** → limpar estações e tracklogs.
- Informações secundárias, como filtro ativo e última atualização, deverão ficar fora do mapa, em área de diagnóstico/status quando necessário.



## Nome dos arquivos incluindo a versão

**Objetivo:** facilitar a identificação de cada build baixado e evitar arquivos com nomes idênticos entre versões.

- Incluir o número da versão diretamente no nome dos executáveis publicados.
- O **Portable EXE** deve deixar de usar sempre o mesmo nome.
- Adotar nomes no formato:
  - `PT2VHF_APRS_Client_Portable_x64_v0.3.1.exe`
  - `PT2VHF_APRS_Client_Setup_x64_v0.3.1.exe`
- Aplicar o mesmo padrão automaticamente a cada nova release.
- Atualizar o workflow do GitHub Actions, o build local e as notas da Release para usar os nomes versionados.
- Garantir que os links de download da Release apontem para os arquivos com o número correto da versão.

