# Backlog

Os itens registrados até **24/09/2026** foram incorporados ou consolidados na **v1.6**, incluindo os últimos ajustes de popup de mensagem e layout das coordenadas.

A partir desta versão, novas demandas serão adicionadas novamente neste arquivo à medida que forem solicitadas.

## Concluído na v1.6

- mensagens longas: status agregado, retry individual e política configurável de retry/timeout;
- análises de topologia: rankings, enlaces desaparecidos, comparação por período e animação temporal;
- Linux: AppImage, testes em Ubuntu 22.04/24.04 e notificações nativas quando disponíveis;
- página única de Configuração com seções compartimentalizadas;
- aviso ao sair da Configuração com alterações não salvas;
- restauração da configuração padrão sem apagar dados operacionais;
- botão rápido de tema Claro/Escuro;
- Português/English com bandeiras, Português como padrão;
- coordenadas decimal/DMS e localização do sistema;
- organização de Estação APRS, APRS-IS, Aplicativo, Mapa/Topologia e Backup/Dados;
- editor gráfico APRS-IS ampliado, validação, cópia e filtro manual preservado;
- alerta de filtro APRS-IS vazio;
- filtro padrão de novas instalações para indicativos brasileiros;
- Indicativo obrigatório e passcode automático;
- orientação de campos obrigatórios ao conectar;
- localização automática, centralização inicial e altitude de contingência em 0 m;
- recomendação não bloqueante ao enviar beacon ainda com altitude de contingência em 0 m;
- “Conectar ao iniciar” na seção APRS-IS e habilitado por padrão em novas instalações;
- ordenação A–Z/Z–A das conversas agrupadas;
- preenchimento automático do Destino ao selecionar conversa;
- correção do peso de fonte em De, Para e Tipo;
- Log com data/hora em uma linha, alinhamento consistente e ordenação nos dois sentidos;
- manual PDF profissional com screenshots e validação automática;
- atualização integrada com verificação, download, SHA-256, instalação assistida e rollback onde suportado.

## Atualizações automáticas ativadas por padrão

**Objetivo:** deixar o fluxo OTA completamente automático em novas instalações.

- Em novas instalações, deixar ativadas por padrão as três opções de **Atualizações**:
  - **Verificar atualizações automaticamente**;
  - **Baixar atualização automaticamente**;
  - **Instalar atualização automaticamente ao fechar**.
- O usuário continua podendo desativar qualquer uma das três opções individualmente.
- Em instalações existentes, preservar a preferência já salva pelo usuário; não reativar automaticamente uma opção que ele tenha desligado.
- Quando uma nova versão compatível for detectada, o cliente deverá verificar, baixar e preparar a instalação automaticamente conforme essas preferências.
- Manter a validação de origem e SHA-256 antes de considerar o pacote pronto para instalação.
- Para plataformas que exigem intervenção do sistema ou privilégios adicionais, manter o comportamento seguro já definido para cada tipo de pacote.

## Divisão de mensagens longas sem numeração visível

**Objetivo:** dividir mensagens APRS longas em partes de forma transparente, sem inserir marcadores como `1/2`, `2/2` no texto enviado.

- Ao dividir uma mensagem longa em múltiplos pacotes APRS, **não adicionar prefixos ou sufixos visíveis de numeração**, como `1/2`, `2/2`, `[1/2]` etc.
- A mensagem deve ser fragmentada respeitando o limite de caracteres do protocolo, mas preservando ao máximo a leitura natural.
- **Nunca cortar uma palavra ao meio** quando houver espaço para mover essa palavra inteira para a parte seguinte.
- Se o limite cair no meio de uma palavra, encerrar a parte anterior no último separador apropriado antes do limite e iniciar a próxima parte com a palavra completa.
- Considerar como pontos naturais de quebra, nesta ordem de preferência: espaço, quebra de linha e outros separadores seguros, sem remover conteúdo da mensagem.
- Remover apenas o separador excedente da borda quando necessário para não criar espaço duplicado entre partes; não alterar o conteúdo textual.
- Se existir uma palavra individual maior do que o tamanho máximo permitido por uma única mensagem APRS, fazer a divisão técnica dessa palavra apenas como último recurso.
- O controle interno de partes, ACK/REJ, retries e status agregado deve continuar funcionando por metadados internos, **sem depender de numeração escrita no corpo da mensagem**.
- O destinatário deve receber as partes em sequência com o texto original preservado, sem os marcadores artificiais de fragmentação.

## Nova aba “Análise” para análise da rede

**Objetivo:** separar as ferramentas de análise da rede das preferências de Configuração e dar a elas uma área própria na navegação principal.

- Criar uma nova aba superior chamada **Análise**.
- Mover para essa nova aba toda a seção atual de **Análise da topologia observada / análise da rede** que hoje fica em **Configuração → Mapa e Topologia**.
- A nova aba deve concentrar os recursos analíticos, incluindo:
  - ranking de digipeaters;
  - ranking de IGates;
  - enlaces que deixaram de aparecer;
  - comparação com o período anterior;
  - métricas agregadas da topologia;
  - controles de período;
  - ação **Atualizar análise**;
  - ação **Animar período** e demais recursos analíticos relacionados.
- Manter em **Configuração → Mapa e Topologia** apenas preferências de apresentação e comportamento do mapa/topologia, como cores, espessura, provedor do mapa e opções visuais.
- Não duplicar a análise nas duas telas; após a mudança, a área analítica deve existir somente na aba **Análise**.
- A aba **Análise** deve usar os mesmos dados já registrados no banco, sem alterar ou perder o histórico existente.
- Preservar a integração com o mapa: ações como **Animar período** podem abrir/focar a aba Mapa quando necessário.
- Preparar a estrutura da aba para receber futuramente novos indicadores e gráficos de saúde/desempenho da rede.
