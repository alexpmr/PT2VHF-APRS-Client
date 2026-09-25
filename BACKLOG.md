# Backlog

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

- **Portátil — aplicação deixa de responder após alguns minutos (prioridade alta)**
  - **Teste v1.6.11:** preparada correção experimental para reduzir contenção SQLite, impedir pollings sobrepostos, limitar chamadas HTTP a 10 s e gravar mensagens multipartes em uma única transação. Manter este item aberto até validação em uso real.
  - **Resultado do teste v1.6.11:** ocorreu a mensagem **“O backend local não respondeu em 10 segundos.”**. Portanto, o timeout do frontend funcionou, mas a causa raiz permanece: o servidor HTTP local fica indisponível por mais de 10 s.
  - **Configuração também afetada na v1.6.11:** o botão **Salvar configuração** não conclui a gravação quando o backend entra nesse estado. Isso confirma que a falha não está restrita a Mensagens; a rota `POST /api/config` também fica sem atendimento.
  - Tratar a v1.6.11 como **não resolvida**. O próximo diagnóstico deve identificar qual rota/request ocupa as threads do Waitress no momento do travamento e se há esgotamento do pool de workers.
  - Instrumentar cada request com início/fim/duração, endpoint, thread e status; incluir contador de requests ativos e dump das threads quando o health-check detectar atraso.
  - Quando o backend entrar em timeout, suspender temporariamente os pollings automáticos para evitar que novos requests agravem o esgotamento das threads.
  - Na versão **Portable**, após alguns minutos aberta, a interface aparenta continuar visível, mas as operações que dependem do backend deixam de responder.
  - **Reprodutibilidade confirmada:** ao fechar e abrir novamente, a aplicação volta a funcionar normalmente por algum tempo e depois trava de novo.
  - **Confirmação pelo navegador:** quando ocorre o travamento, abrir a interface pelo navegador ou tentar atualizar/recarregar a página também não responde. Isso indica indisponibilidade do **servidor HTTP local/backend**, e não apenas travamento do WebView ou da janela portátil.
  - Sintomas observados: **não conecta ao APRS-IS**, **não verifica nova versão**, **não salva Configurações** e outras chamadas da interface ficam sem conclusão.
  - O padrão temporal sugere acúmulo progressivo de requests/threads/conexões, lock persistente, polling sobreposto ou recurso não liberado, e não apenas erro pontual de uma tela.
  - Priorizar investigação de **esgotamento das 8 threads do Waitress** por requests bloqueados e de contenção SQLite. O uso atual de `PRAGMA journal_mode=WAL` a cada nova conexão deve ser removido do caminho normal das requisições e executado somente na inicialização/migração do banco.
  - Investigar travamento/indisponibilidade do servidor HTTP local, esgotamento ou bloqueio das threads do Waitress, chamadas `fetch` sem timeout, pollings concorrentes, contenção/lock do SQLite e interação com o WebView.
  - Instrumentar watchdog/health-check interno do backend e registrar último request iniciado/concluído, threads ativas, fila de requests, conexões SQLite abertas/tempo de espera e exceções não tratadas.
  - Evitar que uma operação lenta bloqueie as demais rotas da aplicação.
  - Adicionar timeout e cancelamento às chamadas HTTP do frontend, com feedback explícito quando o backend local não responder.
  - Criar teste de estabilidade prolongada da versão portátil, mantendo a aplicação aberta com recepção APRS, atualização de mapa/mensagens e ações de Configuração por vários minutos.


- **Configurações — falha de salvamento com banco antigo/inconsistente**
  - O problema desapareceu após apagar o banco local e iniciar com um banco novo.
  - Isso indica possível incompatibilidade de migração, esquema antigo, registro de configuração inconsistente ou dado legado inválido, e não necessariamente falha do botão de salvar em uma instalação limpa.
  - Investigar a abertura de bancos existentes após upgrade e validar/migrar automaticamente a tabela de configuração.
  - Se houver dado inválido ou coluna ausente, corrigir/migrar sem exigir que o usuário apague todo o banco.
  - Revisar também o fluxo do `saveConfigFooterButton` e do modal **Salvar e sair** para sempre exibir erro explícito caso a persistência falhe.
  - Adicionar teste de regressão cobrindo upgrade com banco de versão anterior → alterar configuração → salvar → persistir e navegar.


- **Logo APRS oficial ainda não aplicada corretamente**
  - A imagem enviada pelo usuário ainda precisa ser incorporada com um arquivo de imagem válido no repositório.
  - Atualizar cabeçalho/interface, favicon, ícones Windows/Linux e demais pontos visuais sem quebrar o build.
  - Adicionar validação de integridade da imagem no pipeline para evitar novos empacotamentos com arquivo corrompido.

Novas demandas devem continuar na série **1.6.x** até indicação explícita para avançar para **1.7**.
