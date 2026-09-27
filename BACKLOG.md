# Backlog

## Política de versões a partir da próxima geração

- A próxima versão completa será **v1.7**.
- As versões seguintes desta linha usarão numeração incremental **v1.7.1, v1.7.2, v1.7.3...**.
- Não publicar a versão intermediária **v1.6.25**.

## Concluído na v1.6.1

- atualização OTA com preferências configuráveis;
- verificação automática da Release a cada 5 minutos;
- mensagens longas sem marcadores visíveis de parte;
- aba **Análise** com métricas e rankings;
- período **Completo** da topologia;
- favoritos com estrela amarela;
- filtro **Não lidas** em Mensagens;
- botão **Mostrar log** no popup da estação;
- legenda de linhas no Mapa;
- animação inicial de tráfego APRS;
- som/destaque visual de atividade.

## Concluído na v1.6.2

- **Replay da Rede** com timeline arrastável, histograma/densidade de tráfego, seek, intervalo personalizado e velocidades de 0,25x a 20x.
- Controles de replay/animação movidos para a **parte inferior do Mapa**.
- Removido **Animar período** da aba Análise.
- Pacotes multi-hop podem percorrer múltiplos enlaces simultaneamente.
- Som, notificação e destaque visual limitados às estações visíveis no enquadramento/zoom atual.
- Ondas/círculos concêntricos animados ao redor do marcador da estação que transmite.
- Indicador **RX/TX** de atividade de tráfego na barra superior.
- Legenda do Mapa sincronizada com as **cores e espessuras** configuradas.
- Correção da **espessura da topologia** refletindo no Mapa.
- Botão **Ver logs** no popup da estação, abrindo o Log filtrado pelo indicativo/SSID.
- Um único botão **Salvar configuração** no rodapé da aba Configuração.
- Confirmação visual após salvar e proteção ao trocar de aba com alterações pendentes.
- **Auto-update desativado**; o cliente somente informa quando existe uma versão nova.
- Verificação de versão com timeout, recuperação automática e sem manter falhas presas em cache.
- Popup de **novidades da versão** exibido uma única vez após atualização.
- Release gerada somente para **Windows x64**: Setup + Portable, sem nova documentação PDF, Linux ou macOS.

## Concluído na v1.6.4

- Corrigido o envio na aba **Mensagens** pelo botão **Enviar** e pela tecla **Enter**.
- Corrigido o **filtro por origem** na aba Mensagens.
- Corrigido o **Replay da Rede** para voltar a mostrar os pacotes trafegando entre os nós, além do realce das estações.
- Adicionado rastro visual ao pacote animado para destacar o enlace em uso.
- Mantida a animação das estações móveis com tracklog progressivo.
- Incluído teste de regressão para impedir que o replay volte a exibir apenas o *highlight* das estações.
- Release somente **Windows x64 Portable**, sem instalador e sem PDF.

## Concluído na v1.6.7

- Gerada versão **Linux x86_64** nos formatos **TAR.GZ, AppImage e DEB**.
- Aplicadas ao build Linux as correções acumuladas das versões 1.6.4 a 1.6.6.
- Corrigida a aplicação da **logo APRS oficial** na interface e no ícone Linux.
- Adicionados smoke tests em **Ubuntu 22.04** e **Ubuntu 24.04**.
- Release somente Linux, sem Windows, macOS ou PDF.

## Concluído na v1.6.8

- Corrigido o travamento no envio de mensagens com **fila assíncrona de transmissão APRS**.
- Adicionada **deduplicação** para impedir múltiplos envios após cliques repetidos.
- Botão **Enviar** é temporariamente bloqueado enquanto a mensagem entra na fila.
- Ao fechar a aplicação, filas pendentes são canceladas e não são reenviadas na próxima abertura.
- Adicionada manutenção leve de encerramento com **PRAGMA optimize** e checkpoint do WAL do SQLite.
- Serviços, conexão APRS-IS e worker de transmissão são encerrados de forma controlada.
- Release para **Windows x64 e Linux x86_64**, sem macOS e sem PDF.

## Consolidado na v1.6.9

- Consolidada a correção do travamento de mensagens com **fila assíncrona e deduplicação**.
- Corrigido o teste legado que ainda exigia a logo APRS oficial e bloqueava os builds.
- Mantida a logo estável anterior no empacotamento até a imagem oficial ser reintegrada com validação.
- Release para **Windows x64 e Linux x86_64**, sem macOS e sem PDF.

## Preparado para a v1.6.10

- Release completa com **Windows x64 Setup + Portable**.
- Release Linux x86_64 em **TAR.GZ, AppImage e DEB**.
- Release macOS em **ARM64 e Intel x86_64 (DMG)**.
- **Manual PDF versionado** gerado e validado no workflow.
- Aplicação dos patches acumulados também aos builds macOS e ao ambiente de captura do manual.
- Correção do pipeline do ícone Windows para não depender do JPEG oficial inválido.

## Pendências para próximas versões

- **Nova aba Sobre — autor, contato e divulgação do projeto**
  - Criar uma nova aba superior **Sobre**.
  - Apresentar uma breve descrição do autor/projeto, identificando **Alex, PT2VHF** como idealizador do PT2VHF APRS Client e radioamador responsável pelo projeto.
  - Explicar de forma curta o objetivo da aplicação: oferecer um cliente APRS moderno, multiplataforma e voltado à visualização, mensagens, estatísticas e análise da rede.
  - Exibir claramente o repositório oficial por meio do link curto **tiny.cc/aprs**.
  - Incluir uma área **Contato / Sugestões / Dúvidas / Melhorias** com:
    - **WhatsApp:** +55 61 98402-3634
    - **E-mail:** alexpmr@gmail.com
  - Tornar WhatsApp e e-mail clicáveis quando a plataforma permitir, abrindo o aplicativo/navegador apropriado.
  - Adicionar um botão de divulgação, por exemplo **Divulgar PT2VHF APRS Client na rede APRS**.
  - Ao clicar no botão, preparar um **Announcement APRS** com texto curto contendo o nome do cliente e **tiny.cc/aprs**.
  - Exibir uma prévia completa do pacote/mensagem antes do envio e exigir **confirmação explícita** do usuário.
  - O envio da divulgação deve ser sempre **manual**, sem transmissão automática ao iniciar o programa e sem repetição agressiva.
  - Permitir editar o texto antes do envio, respeitando o limite aplicável a bulletins/announcements APRS.
  - Usar o mecanismo APRS apropriado para divulgação coletiva, preferencialmente **Announcement/Bulletin**, em vez de mensagens individuais em massa.
  - Registrar no Log quando uma divulgação for enviada, incluindo horário e conteúdo transmitido.
  - Manter a aba visualmente consistente com a identidade oficial da aplicação e exibir a logo APRS oficial do projeto.
  - Todo o conteúdo textual da aba **Sobre** deve acompanhar o **idioma corrente da aplicação** (**Português, English, Español ou Français**), incluindo títulos, descrição do autor/projeto, contatos, instruções, botões, avisos, confirmação e mensagens de status.
  - O texto sugerido para o **Announcement/Bulletin APRS** de divulgação também deve ser gerado no **idioma corrente**, mantendo **tiny.cc/aprs** inalterado.
  - Para **Português**, usar como texto padrão de divulgação: **PT2VHF APRS Client v1.7 - Download: tiny.cc/aprs**.
  - Nas demais línguas, manter a mesma estrutura semântica, traduzindo apenas o texto descritivo e preservando **PT2VHF APRS Client**, a versão e **tiny.cc/aprs**.
  - Ao trocar o idioma da aplicação, a aba **Sobre** e o texto padrão de divulgação devem ser atualizados imediatamente, sem exigir reinicialização.

- **Mapa — mover Histórico para uma barra contextual abaixo das abas**
  - Remover o botão **Histórico** da barra superior global da aplicação.
  - Exibir o controle **Histórico** em uma barra contextual **logo abaixo das abas superiores**, somente quando a aba **Mapa** estiver ativa.
  - Ocultar completamente esse controle ao mudar para **Mensagens, Estações, Log, Estatísticas, Configuração, Sobre** ou qualquer outra aba.
  - Manter no novo local o mesmo comportamento atual do Histórico, incluindo acesso ao modo de replay/animação temporal.
  - Preservar estado, período e demais preferências relacionadas ao Histórico ao trocar de aba e voltar ao Mapa.
  - Garantir que a barra contextual do Mapa não sobreponha o canvas e permaneça visualmente integrada aos demais controles específicos do Mapa.

- **Mapa — substituir Atividade por controles independentes de Topologia, Tracklog e Estações**
  - Remover da barra superior do **MAPA** o controle atual de **Atividade** e sua contagem associada.
  - Manter **Topologia observada** com chave liga/desliga e seletor de período.
  - Adicionar controle equivalente para **Tracklog**, com chave liga/desliga e seletor de período.
  - Adicionar controle equivalente para **Estações**, com chave liga/desliga e seletor de período.
  - Usar o mesmo padrão visual e de interação para os três controles, mantendo-os alinhados na barra superior e fora do canvas do mapa.
  - Para **Topologia**, **Tracklog** e **Estações**, oferecer os mesmos ranges temporais já usados no mapa, incluindo **Completo, 1 h, 6 h, 24 h e 7 dias**.
  - O filtro temporal de **Tracklog** deve limitar os pontos/segmentos desenhados ao período escolhido.
  - O filtro temporal de **Estações** deve mostrar apenas estações cuja última recepção/interação esteja dentro do período escolhido.
  - Desligar **Tracklog** deve ocultar somente os trajetos, sem ocultar as estações.
  - Desligar **Estações** deve ocultar os marcadores das estações, sem obrigatoriamente desligar Topologia ou Tracklog.
  - Desligar **Topologia** deve ocultar somente os enlaces observados.
  - Preservar de forma independente o estado ligado/desligado e o período escolhido de cada controle entre reinicializações.
  - Garantir que filtros independentes não gerem inconsistência visual: por exemplo, um tracklog pode permanecer visível mesmo que o marcador da estação esteja oculto, se esse for o estado configurado pelo usuário.

- **Atualizador automático — aplicação fecha e atualização não inicia**
  - Ao clicar em **Nova versão** e depois em **Baixar e instalar**, a aplicação é encerrada, porém o download/instalação da nova versão **não é iniciado**.
  - Corrigir o fluxo para garantir que o helper externo do atualizador seja iniciado e permaneça executando **antes** de a aplicação principal encerrar.
  - Não fechar a aplicação se o helper não tiver sido criado/iniciado com sucesso.
  - Validar a seleção do asset correto da Release conforme plataforma, arquitetura e formato instalado/portátil.
  - Exibir progresso de **download**, **verificação**, **instalação** e **reinicialização**, além de mensagem de erro visível quando qualquer etapa falhar.
  - A janela/modal **Nova versão disponível** não deve fechar automaticamente após alguns segundos; deve permanecer aberta até uma ação explícita do usuário ou até a conclusão controlada do fluxo de atualização.
  - Depois que o usuário clicar em **Baixar e instalar**, manter o modal visível durante **download**, **validação**, **instalação** e **reinicialização**, atualizando barra de progresso e texto de status.
  - Não permitir que timers genéricos de pop-up/notificação fechem a janela de atualização enquanto houver operação em andamento.
  - O botão **Depois** continua sendo a forma explícita de adiar/fechar a atualização antes do início do processo; durante uma atualização já iniciada, evitar fechamento acidental.
  - Registrar em log dedicado o caminho/URL do asset, PID do helper, diretório temporário, tamanho esperado/baixado, SHA-256, comando de instalação e código de saída.
  - No Windows, validar separadamente **Portable** e **Setup**, incluindo UAC quando necessário.
  - Após atualização bem-sucedida, reiniciar automaticamente a nova versão; em caso de falha, manter/restaurar a versão anterior quando aplicável.
  - Adicionar teste de regressão cobrindo o cenário em que o helper não inicia, garantindo que a aplicação permaneça aberta e informe o erro ao usuário.
  - Tratar como **bug prioritário da v1.7.1**, pois o comportamento atual pode deixar o usuário sem a aplicação aberta e sem atualização concluída.

- **Mapa — filtrar saltos irreais de posição nos tracklogs**
  - Antes de acrescentar uma nova posição ao tracklog, comparar a coordenada recebida com a **última posição válida aceita** da mesma estação.
  - Calcular a distância entre os pontos e o intervalo de tempo, derivando a **velocidade implícita** do deslocamento.
  - Ignorar posições claramente anômalas quando houver salto repentino incompatível com um deslocamento realista, evitando linhas falsas de centenas ou milhares de quilômetros no mapa.
  - Um ponto rejeitado **não deve substituir a última posição válida** usada como referência; assim, o próximo pacote correto não ficará ligado ao ponto incorreto.
  - Não desenhar segmento de tracklog de/para uma posição classificada como outlier.
  - Considerar o intervalo de tempo entre os pacotes para não bloquear deslocamentos reais após longos períodos sem recepção.
  - Se várias posições consecutivas confirmarem uma nova região, tratar como **mudança real de localização** e iniciar um novo trecho de tracklog, em vez de descartar indefinidamente a estação.
  - Registrar no diagnóstico/log os pontos descartados, com indicativo, distância do salto, intervalo de tempo e velocidade implícita, para permitir auditoria e ajuste dos limites.
  - Aplicar o mesmo filtro tanto ao tracklog ao vivo quanto ao replay/histórico.

- **Estatísticas — Estações mais ativas com atalho para mensagem**
  - No bloco **Estações mais ativas**, transformar o indicativo de cada estação em **link clicável**.
  - Ao clicar no indicativo, mudar automaticamente para a aba **Mensagens**.
  - Preencher o campo **Destinatário** com o indicativo clicado, incluindo SSID quando houver.
  - Se já existir conversa com a estação, sincronizar o foco da conversa com o mesmo indicativo.
  - Deixar o campo de mensagem pronto para digitação, facilitando o envio de uma mensagem rápida.
  - Não enviar nenhuma mensagem automaticamente; o clique deve apenas preparar a conversa/destinatário.
  - Manter comportamento consistente com outros atalhos de indicativo existentes na aplicação.

- **Estatísticas — ranking das estações que mais conversaram**
  - Adicionar painel com o ranking das estações com maior volume de conversas/mensagens registradas pelo cliente.
  - Ordenar em ordem decrescente e exibir Indicativo, quantidade de mensagens/interações e percentual.
  - Diferenciar, quando útil, mensagens enviadas, recebidas e total de interações.
  - Usar as mensagens armazenadas no banco local e evitar duplicidades artificiais.

- **Portátil — validação prolongada de estabilidade**
  - Manter acompanhamento em uso real do Windows Portable após as correções de CPU/topologia/SQLite já incorporadas.
  - Registrar qualquer novo congelamento com diagnostics.log e verificar se há regressão no backend, WebView2, mapa ou contenção SQLite.
  - Considerar encerrado somente após teste prolongado sem aumento anormal de CPU e sem timeout nas rotas interativas.

- **Configurações — compatibilidade com banco antigo/inconsistente**
  - Validar upgrade com banco de versão anterior, alterar configuração, salvar, reiniciar e confirmar persistência.
  - Garantir migração automática de schema/defaults sem apagar mensagens, estações, logs ou tracklogs.
  - Adicionar/confirmar teste de regressão para banco antigo ou parcialmente migrado.

- **Mapa — painel lateral de estação**
  - Substituir progressivamente o popup grande da estação por um painel lateral fixo, preservando o mapa visível durante a consulta.
  - Exibir Indicativo, última recepção, distância, software/dispositivo, posição, status, favorito, mensagens, Ping, Trace e estações ouvidas.
  - Incluir atalhos para **Mostrar log**, **Enviar mensagem**, **Ping/ACK**, **Trace**, **Posição**, **Status** e histórico de queries.
  - Em telas pequenas, transformar o painel lateral em painel inferior responsivo.
  - Ao trocar de estação, atualizar o mesmo painel sem criar sobreposição adicional no mapa.

- **Mapa — consolidar controles na barra superior**
  - Aproveitar a nova barra acima do mapa para reunir os controles usados com maior frequência.
  - Avaliar incluir seletor de mapa/base cartográfica, mostrar/ocultar tracklogs, mostrar/ocultar enlaces, animações, som e outros controles rápidos.
  - Manter os controles menos usados em um menu **Mais ▾**, evitando poluir a barra.
  - Garantir que nenhum controle volte a ficar sobreposto ao canvas do mapa ou à legenda.

- **Busca rápida — localizar estação por indicativo**
  - Adicionar campo de busca rápida por indicativo, com filtragem caractere por caractere.
  - Aceitar indicativo completo ou parcial, incluindo SSID.
  - Ao selecionar uma estação, abrir a aba **Mapa**, centralizar o marcador e aplicar um nível de zoom adequado.
  - Integrar a seleção ao futuro painel lateral da estação.
  - Priorizar favoritos e correspondências exatas nas sugestões.

- **Estatísticas — qualidade da rede APRS**
  - Adicionar painel específico de qualidade/saúde da rede observada.
  - Exibir taxa de pacotes duplicados, tráfego **RF × APRS-IS**, estações únicas por hora/dia e distribuição por tipo de pacote.
  - Incluir mensagens com ACK/sem ACK, RTT médio/mediano do Ping, estações novas no período e estações que deixaram de aparecer.
  - Respeitar o período selecionado em Estatísticas e permitir análise **Completo, 1 h, 6 h, 24 h e 7 dias**.
  - Evitar que telemetria de alta frequência distorça indicadores de atividade humana.

- **Exportação — CSV, GeoJSON e KML**
  - Adicionar botão **Exportar** nas áreas de Estatísticas e Mapa.
  - Exportar estatísticas tabulares em **CSV** respeitando período e filtros ativos.
  - Exportar estações, posições, tracklogs e enlaces em **GeoJSON** e/ou **KML**.
  - Preservar timestamp, indicativo, origem do dado e atributos úteis para análise externa.
  - Gerar arquivos compatíveis com Excel, QGIS e Google Earth sempre que aplicável.

- **Estatísticas — comparação entre períodos**
  - Permitir comparar o período atual com o período imediatamente anterior de mesma duração.
  - Exemplos: **últimas 24 h × 24 h anteriores** e **últimos 7 dias × semana anterior**.
  - Mostrar variação absoluta e percentual de estações ativas, mensagens, tráfego, enlaces, digipeaters e iGates.
  - Destacar novos enlaces, estações novas e estações que desapareceram.
  - Evitar apresentar variação percentual quando a base anterior for zero; nesse caso, indicar **novo** ou equivalente.

- **Diagnóstico — saúde da aplicação e pacote de suporte**
  - Criar uma área de diagnóstico em **Ajuda** ou seção própria.
  - Exibir integridade do banco SQLite, tamanho do banco, estado da conexão APRS-IS, WebView, CPU, RAM, filas de mensagens, serviços/threads principais e espaço em disco.
  - Adicionar botão **Gerar pacote de diagnóstico**.
  - O pacote deve incluir logs e informações técnicas úteis, removendo ou mascarando dados sensíveis antes da geração.
  - Incluir versão da aplicação, plataforma, arquitetura, caminho do banco, status das migrações e erros recentes.
  - Facilitar o envio desse ZIP em casos de travamento ou comportamento anormal.

## Consolidado na v1.6.17

- Release completa multiplataforma baseada nas correções testadas até a v1.6.16.
- CPU inicial observada em torno de 1% após a correção da consulta de topologia, contra aproximadamente 55% na v1.6.15.
- Mantida a instrumentação diagnóstica e os gauges de CPU/RAM para acompanhar estabilidade em uso real.
- Publicação prevista para Windows, Linux, macOS e Manual PDF.


## Concluído na v1.6.18

- Queries APRS direcionadas pelo popup da estação: posição, status, ouvidos e trace.
- Ping/ACK com RTT e timeout.
- Trace visual no mapa com hops conhecidos, sem inventar posição para hops desconhecidos.
- Histórico local das queries e respostas.
- Estrutura de resposta automática a APRSP/APRSS/APRST/PING com configuração e rate-limit.
## Concluído na v1.6.19

- **Aba Estatísticas:** bloco de clientes/versões APRS por TOCALL mais recente de cada estação, ordenado do mais usado para o menos usado, com quantidade, percentual e Não identificado.
- **Mapa / queries:** resultado da última query passa a ficar claramente visível no popup, com status, RTT, resposta, Trace textual e indicação de hops localizados.
- **Mapa / histórico:** botão para visualizar o histórico de queries daquela estação e restauração da última resposta ao reabrir o popup.
- **Idiomas:** restaurado o controle de idioma na barra superior, com Português/Brasil e English/Inglaterra, persistindo a escolha.
- **Queries de posição:** resposta exibida passa a incluir latitude e longitude recebidas.

## Concluído na v1.6.20

- **Estatísticas / clientes:** nomes amigáveis de software/dispositivo pelo snapshot local da base APRS Device Identification, mantendo o TOCALL como referência.
- **Estatísticas / adoção:** Top 20 + linha adicional destacada com a posição real do PT2VHF APRS Client quando estiver fora do corte.
- **Identificação do cliente:** transmissões do aplicativo passam a usar o TOCALL experimental **APZVHF**, permitindo contabilizar instalações observadas.
- **Idioma no topo:** controle compacto mostra somente o idioma atual e abre as duas opções ao clicar; English usa a bandeira da Inglaterra.
- **Mapa / topologia:** qAR/qAO até o IGate passa a ser classificado como RF e desenhado em linha contínua; bancos existentes são migrados automaticamente.

## Concluído na v1.6.21

- **Estatísticas / estações mais ativas:** aba renomeada de Análise para Estatísticas e novo ranking por tráfego útil no período selecionado.
- O ranking exclui telemetria, iGates e digipeaters; essas infraestruturas continuam nas seções dedicadas.
- Exibe posição, indicativo, pacotes válidos e percentual sobre o total elegível.
- Incluído teste automatizado cobrindo ordenação e exclusões.

## Concluído na v1.6.22

- **Atualização integrada por plataforma:** clicar no aviso de nova versão baixa o asset correspondente ao ambiente em execução e inicia a instalação.
- Download restrito à Release oficial, com conferência de tamanho, SHA-256 calculado localmente e validação do digest do GitHub quando disponível.
- Updater auxiliar separado do processo principal, encerramento limpo primeiro e encerramento forçado por PID após timeout somente se necessário.
- Nova versão relançada automaticamente após instalação bem-sucedida.
- Windows Portable com backup/rollback; Windows Setup com instalador; Linux AppImage/DEB/TAR.GZ e macOS DMG com fluxos próprios.
- Lock em arquivo com PID para impedir duas atualizações concorrentes e recuperar locks obsoletos.
- Configuração, banco SQLite, mensagens, estações, logs e demais dados permanecem preservados fora dos binários.

## Concluído na v1.6.23

- **Identidade visual:** a mesma logo vetorial/raster é aplicada ao cabeçalho, favicon, ícones Windows/Linux/macOS, bandeja do Windows e Manual PDF.
- **Mapa — filtro por última interação:** adicionadas as opções **Tudo** (padrão), **menos de 2 h**, **2 a 24 h** e **mais de 24 h**.
- O filtro atua sobre os marcadores e tracklogs; enlaces de topologia associados a estações conhecidas filtradas também deixam de ser exibidos.
- O Mapa informa quantas estações permanecem visíveis em relação ao total.
- A opção **Tudo** permanece selecionada por padrão em cada abertura da aplicação.
- **Mapa — legenda:** adicionada opção para minimizar/expandir a legenda; o estado escolhido é preservado localmente.

## Concluído na v1.6.24

- **Logo oficial única:** a imagem APRS fornecida para o projeto passa a ser a fonte visual única para interface, favicon, bandeja, ícones de plataforma e Manual PDF.
- **macOS:** removido o desenho alternativo do ícone; o ICNS passa a ser derivado da mesma logo PNG usada pelas demais plataformas.
- **Histórico de versões:** adicionadas as notas internas ausentes da v1.6.23 e as notas da v1.6.24.
- **Backlog consolidado:** removidas pendências já concluídas em queries APRS, estatísticas de clientes, idioma, topologia e gauges CPU/RAM.
- Permanecem abertas apenas melhorias/validações ainda não concluídas, incluindo ranking de conversas, estabilidade prolongada do Portable e compatibilidade de configuração com banco antigo.

## Concluído na v1.7

- **Mapa:** controles de Atividade e Topologia observada ficam fora do canvas, na barra superior.
- **Mapa:** animação de tráfego ao vivo ativada por padrão em novas instalações, com opção persistente para desativar.
- **Mensagens:** filtros compactos, com rótulos em uma linha.
- **Mensagens:** conversa em foco e campo Destinatário sincronizados, incluindo tratamento claro para destinatário novo sem histórico.
- **Idiomas:** suporte a Português, English, Español e Français, com seletor rápido, persistência e fallback seguro.
- **Estatísticas:** somente nome amigável do aplicativo/software na apresentação principal; identificadores técnicos permanecem internos.
- **Estatísticas:** fonte padrão maior e controle próprio de tamanho na Configuração.
- **Versionamento:** nova linha iniciada em v1.7; próximas releases serão v1.7.1, v1.7.2, v1.7.3...

