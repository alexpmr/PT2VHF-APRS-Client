# Backlog

Este arquivo registra funcionalidades planejadas que **ainda não fazem parte da versão atual**.

## Mensagens longas — melhorias futuras

A v0.3.1 implementou o envio automático em partes APRS, numeração, IDs individuais e indicação verde por ACK. Permanecem como evoluções futuras:

- permitir reenviar diretamente apenas uma parte que tenha recebido `REJ` ou permaneça sem ACK;
- apresentar um status agregado da mensagem longa, por exemplo `2/3 confirmadas` ou `Todas confirmadas`;
- permitir configurar política de retry/timeout sem gerar tráfego APRS excessivo.

## Topologia observada — análises futuras

A v0.3.1 implementou a topologia observada básica e a v1.0 adicionou personalização de cores/espessura. Permanecem como evoluções futuras:

- ranking de digipeaters mais utilizados;
- ranking de IGates mais ativos;
- identificação de enlaces que desapareceram ou mudaram de frequência de uso;
- histórico comparativo por período;
- métricas agregadas por nó/enlace;
- eventual animação temporal do tráfego observado.

## Linux — evoluções de empacotamento

A v1.0 inicia a distribuição Linux oficial em `.deb` e `.tar.gz`. Permanecem para avaliação:

- AppImage oficial;
- teste automatizado em mais distribuições Linux;
- integração mais profunda com desktop environments e notificações nativas.



## Usabilidade e organização das configurações

### Orientar campos obrigatórios ao tentar conectar

**Objetivo:** evitar que a mensagem de erro deixe o usuário sem saber onde corrigir a configuração.

- Quando o usuário clicar em **Conectar** e faltarem Indicativo, Latitude, Longitude ou Altitude:
  - manter a mensagem informando quais campos estão faltando;
  - indicar claramente que eles devem ser preenchidos em **Configuração → Estação**;
  - oferecer botão/ação **Ir para Configuração**;
  - abrir automaticamente a aba Configuração quando apropriado;
  - destacar visualmente os campos obrigatórios ausentes;
  - posicionar o foco no primeiro campo pendente.
- A mensagem deve usar linguagem direta, por exemplo: **“Preencha os campos obrigatórios em Configuração → Estação: Indicativo, Latitude, Longitude e Altitude.”**

### Chaveamento rápido Claro/Escuro

O tema claro/escuro já existe em **Configuração → Aparência**. A evolução planejada é:

- adicionar um chaveamento rápido de **Tema Claro / Tema Escuro** em local de acesso imediato da interface;
- manter a opção existente em Configuração;
- sincronizar as duas formas de alteração;
- persistir a preferência atual no banco local.

### Idioma Português/Inglês

- Adicionar chaveamento de idioma entre **Português** e **English**.
- **Português (Brasil)** deve ser o idioma padrão.
- Internacionalizar textos da interface, mensagens, botões, ajuda, alertas e validações.
- Persistir a preferência de idioma.
- Preparar a estrutura para inclusão futura de outros idiomas sem duplicar telas ou lógica.

### Coordenadas em decimal, graus/minutos/segundos e posição do sistema

Na seção **Configuração → Estação**:

- permitir entrada de latitude/longitude em **graus decimais**;
- permitir entrada em **graus, minutos e segundos (GMS/DMS)**;
- converter automaticamente entre os dois formatos;
- validar latitude entre -90 e +90 e longitude entre -180 e +180;
- tratar corretamente hemisférios N/S/E/W;
- adicionar ação **Usar minha localização** usando a API de geolocalização disponível no WebView/navegador;
- solicitar permissão ao sistema/navegador somente quando o usuário acionar essa função;
- preencher automaticamente latitude e longitude após autorização;
- exibir, quando disponível, a precisão aproximada informada pelo sistema;
- não sobrescrever coordenadas já configuradas sem confirmação explícita.

### Separar APRS das configurações do aplicativo

**Objetivo:** reduzir confusão entre parâmetros da estação/protocolo e preferências visuais do cliente.

Reorganizar a aba Configuração em grupos ou subabas claramente separados:

- **Estação APRS**
  - Indicativo;
  - SSID;
  - posição;
  - altitude;
  - comentário;
  - símbolo;
  - e-mail;
  - beacon.
- **APRS-IS**
  - servidor;
  - porta;
  - passcode;
  - filtro;
  - conectar ao iniciar.
- **Aplicativo**
  - abrir também no navegador;
  - idioma;
  - tema;
  - fontes;
  - avisos de mensagens.
- **Mapa e Topologia**
  - provedor do mapa;
  - brilho;
  - tracklogs;
  - cores e espessura da topologia.
- **Backup e dados**
  - exportação/importação;
  - localização dos dados;
  - ações relacionadas a backup/restauração.

A reorganização não deve alterar os valores já armazenados nem quebrar arquivos JSON de configuração existentes.


## Editor gráfico de filtro APRS-IS

**Objetivo:** facilitar a criação de filtros APRS-IS sem esconder ou limitar a sintaxe nativa.

- Manter o campo atual de **filtro manual por string** para usuários avançados.
- Adicionar um modo **Editor gráfico** que componha automaticamente a string APRS-IS equivalente.
- Permitir alternar entre:
  - **Editor gráfico**;
  - **Filtro manual**.
- Ao alterar opções no editor gráfico, atualizar em tempo real a string APRS-IS gerada.
- Ao editar a string manualmente, preservar o valor informado mesmo que ela utilize recursos ainda não representados no editor gráfico.
- Quando possível, interpretar a string existente e preencher automaticamente os controles gráficos correspondentes.
- Quando a string contiver elementos que o editor gráfico ainda não suporte, exibir aviso claro e manter a string original intacta.

### Componentes previstos no editor

O editor deve permitir combinar, conforme a sintaxe APRS-IS suportada:

- **Raio em torno da posição configurada**;
- **Raio em torno de coordenadas informadas**;
- **Indicativo(s) específicos**;
- **Prefixos/sufixos de indicativos**, quando aplicável;
- **Tipos de pacote/estações**;
- **Objetos/itens**;
- **Faixa geográfica/área**, quando suportada;
- combinação de múltiplos critérios.

### Usabilidade

- Mostrar a **string final gerada** antes de salvar.
- Disponibilizar ação **Copiar filtro**.
- Validar a sintaxe antes de aplicar.
- Exibir explicação curta de cada critério e exemplo prático.
- Oferecer botão **Restaurar filtro padrão**.
- Manter o filtro padrão da aplicação como **`r/2000`** em novas instalações, salvo alteração futura deliberada.
- Não reconectar automaticamente ao APRS-IS enquanto o usuário ainda estiver editando; aplicar/reconectar somente após salvar a configuração.


## Alerta para filtro APRS-IS vazio

**Objetivo:** evitar que o usuário deixe o campo de filtro vazio sem perceber o impacto operacional.

- Quando o campo **Filtro APRS-IS** estiver vazio ao salvar/aplicar a configuração, exibir um alerta de confirmação.
- Informar claramente que, **sem filtro**, o cliente poderá receber todo o tráfego disponibilizado pelo servidor APRS-IS, aumentando significativamente o volume de dados processados.
- O alerta deve oferecer duas ações claras:
  - **Voltar e configurar um filtro**;
  - **Continuar sem filtro**.
- Não preencher automaticamente um filtro caso o usuário confirme explicitamente que deseja continuar sem filtro.
- Se o filtro for apagado acidentalmente e o usuário cancelar o alerta, manter a tela de Configuração aberta e devolver o foco ao campo de filtro.
- Integrar essa validação tanto ao modo **Filtro manual** quanto ao futuro **Editor gráfico de filtro APRS-IS**.
- Na Ajuda, explicar a diferença entre:
  - filtro configurado;
  - filtro vazio;
  - filtro padrão da aplicação.

## Manual PDF - conteúdo incompleto/vazio

**Problema:** o manual PDF gerado automaticamente na Release pode sair praticamente sem conteúdo útil, exibindo apenas a capa/estrutura básica sem as instruções completas esperadas.

- Corrigir o gerador `tools/generate_manual.py` para produzir um manual realmente completo.
- Incluir conteúdo de uso, instalação, configuração APRS, mapas, mensagens, filtros, topologia, backup/restauração, atualização e solução de problemas.
- Incorporar automaticamente as novidades da versão a partir de `VERSION` e `CHANGELOG.md`.
- Validar o PDF gerado antes da publicação: quantidade mínima de páginas, seções obrigatórias presentes e tamanho de arquivo coerente.
- Fazer o workflow falhar se o PDF estiver vazio, muito curto ou sem as seções obrigatórias, impedindo a publicação de um manual incompleto no Latest.
- Manter a identidade visual oficial PT2VHF / APRS / CLIENT.

## Formatação de texto por tela

**Objetivo:** permitir personalizar a leitura das principais telas diretamente em **Configuração → Aplicativo / Aparência**.

- Criar controles independentes de formatação para **Mensagens**, **Estações** e **Logs**.
- Para cada tela, permitir configurar pelo menos:
  - família da fonte;
  - tamanho da fonte;
  - negrito/peso da fonte;
  - opcionalmente espaçamento entre linhas e densidade/altura das linhas quando fizer sentido.
- Aplicar as alterações imediatamente como pré-visualização, salvando de forma persistente ao confirmar a configuração.
- Manter configurações independentes entre as três telas; alterar Mensagens não deve alterar Estações ou Logs.
- Adicionar botão **Restaurar padrão** para cada grupo e, se conveniente, uma ação para restaurar toda a aparência do aplicativo.
- Garantir legibilidade tanto no tema Claro quanto no Escuro.
- Preservar ordenação, alinhamento das colunas, rolagem e responsividade das tabelas ao aumentar a fonte ou ativar negrito.

## Manual PDF profissional com screenshots

**Objetivo:** transformar o manual em uma documentação profissional, visual e realmente útil para novos usuários.

- Criar uma **capa azul profissional**, seguindo a identidade visual oficial PT2VHF / APRS / CLIENT.
- Usar a **logo oficial do projeto** em destaque na capa.
- Exibir na capa pelo menos: nome do aplicativo, versão, data e subtítulo **Manual do Usuário**.
- Estruturar o conteúdo com diagramação profissional, hierarquia visual consistente, cabeçalhos, rodapés, numeração de páginas e índice.
- Incluir **screenshots reais da aplicação** ao longo do manual, vinculadas às instruções correspondentes.
- Priorizar screenshots para: tela principal, mapa, mensagens, estações, logs, configuração APRS, configuração do aplicativo, editor de filtro, coordenadas/localização e instalação quando aplicável.
- Evitar screenshots decorativas: cada imagem deve ajudar a explicar uma função ou procedimento.
- Garantir boa resolução e legibilidade das imagens no PDF.
- Sempre que a interface mudar em uma nova versão, atualizar ou regenerar os screenshots afetados antes de publicar o manual.
- Manter o manual sincronizado com VERSION e CHANGELOG e validar conteúdo mínimo antes de anexá-lo à Release.

## Conexão com campos obrigatórios ausentes

**Objetivo:** melhorar a experiência quando o usuário tenta conectar ao APRS-IS sem ter preenchido os dados obrigatórios da estação.

- Ao clicar em **Conectar**, verificar antes se **Latitude, Longitude e Altitude** estão preenchidas.
- Se algum desses campos obrigatórios estiver ausente, **não tentar a conexão** naquele momento.
- Exibir um **pop-up claro e não técnico** informando exatamente quais campos estão faltando.
- O pop-up deve ter um botão **Ir para Configuração**.
- Ao clicar nesse botão, abrir automaticamente a aba **Configuração → APRS / Estação**.
- Realçar visualmente todos os campos obrigatórios ausentes.
- Colocar o foco no primeiro campo ausente para facilitar o preenchimento.
- Após o usuário corrigir os campos, remover o destaque visual correspondente.
- Manter também a mensagem de erro acessível no status/log para diagnóstico.

## Indicativo obrigatório e passcode automático

**Objetivo:** simplificar a configuração inicial e impedir tentativa de conexão sem identificação da estação.

- Tornar o campo **Indicativo** obrigatório para conexão ao APRS-IS.
- Ao clicar em **Conectar** sem indicativo, incluir **Indicativo** no mesmo pop-up de campos obrigatórios ausentes.
- O botão **Ir para Configuração** deve abrir **Configuração → APRS / Estação**, destacar o campo Indicativo e posicionar o foco nele quando for o primeiro campo ausente.
- Preencher o **Passcode APRS-IS automaticamente** assim que o usuário informar ou alterar o indicativo.
- Calcular o passcode usando apenas o indicativo-base; o **SSID não altera o passcode**.
- Atualizar automaticamente o passcode se o indicativo for alterado.
- Manter o campo visível para conferência, mas evitar exigir que o usuário conheça ou calcule manualmente o passcode.
- Validar o indicativo antes de calcular o passcode e mostrar uma mensagem clara se o formato for inválido.

## Coordenadas automáticas e mapa centralizado no usuário

**Objetivo:** reduzir a configuração inicial manual e abrir o aplicativo já contextualizado na localização atual do usuário.

- Na primeira execução, solicitar ao navegador/WebView/SO permissão para acessar a **localização atual** do usuário.
- Quando a permissão for concedida, **pré-preencher automaticamente Latitude e Longitude** em **Configuração → APRS / Estação**.
- Manter os campos de Latitude e Longitude totalmente editáveis após o preenchimento automático.
- Exibir a **precisão estimada** da localização quando o provedor disponibilizar essa informação.
- Preencher **Altitude** automaticamente somente quando a plataforma fornecer um valor confiável; caso contrário, manter o campo para preenchimento manual.
- Na primeira abertura do mapa, centralizar automaticamente o mapa na **localização atual do usuário** quando houver permissão e coordenadas válidas.
- Usar um nível de zoom inicial adequado para visualizar a região ao redor do usuário, sem impedir que ele altere zoom e posição manualmente.
- Após o usuário mover o mapa manualmente, respeitar a posição escolhida e não recentralizar continuamente sem solicitação.
- Manter o botão **Usar minha localização atual** para permitir atualização manual posterior das coordenadas e do centro do mapa.
- Se a permissão de localização for negada ou indisponível, não bloquear o aplicativo; mostrar instrução clara para preencher as coordenadas manualmente.
- Tratar separadamente a localização usada para centralizar o mapa e as coordenadas salvas da estação, evitando sobrescrever dados já confirmados sem aviso.

## Altitude padrão quando indisponível

**Objetivo:** evitar que a ausência de altitude impeça a conexão ao APRS-IS, sem esconder do usuário que o dado está incompleto.

- Quando a localização automática fornecer Latitude/Longitude, mas **não fornecer Altitude confiável**, preencher a altitude automaticamente com **0 m**.
- O valor **0 m** deve ser aceito como valor válido para fins de conexão, para que a ausência de altitude não bloqueie o APRS-IS.
- Exibir um aviso claro junto ao campo, por exemplo: **Altitude não disponível automaticamente. Foi usado 0 m. Recomendamos informar a altitude real da estação.**
- Manter o campo de Altitude editável para correção manual pelo usuário.
- Diferenciar visualmente altitude **estimada/obtida pelo sistema** de altitude **assumida como 0 m por ausência de dado**.
- Não sobrescrever uma altitude já informada manualmente pelo usuário com 0 m em execuções futuras.
- Se o usuário tentar transmitir beacon ainda com altitude igual a 0 m, permitir a transmissão, mas exibir uma recomendação não bloqueante para revisar o valor.

## Mover “Conectar ao iniciar” para a seção APRS-IS

**Objetivo:** organizar melhor as preferências de conexão dentro de **Configuração → APRS / Estação**.

- Mover a opção **Conectar ao iniciar** para a subseção **APRS-IS**.
- Posicionar essa opção próxima aos campos de **Servidor**, **Porta**, **Passcode** e **Filtro APRS-IS**.
- Remover a opção da localização atual em que ela aparece hoje, evitando duplicidade.
- Manter o comportamento e a persistência existentes da configuração `connect_on_start`.
- Não alterar o valor já salvo pelo usuário durante a migração da interface.

## Idiomas Português e English com bandeiras

**Objetivo:** oferecer seleção clara de idioma na interface, mantendo **Português** como padrão.

- Implementar suporte de interface para **Português** e **English**.
- Definir **Português** como idioma padrão para novas instalações e para situações em que não houver preferência salva.
- Na seleção de idioma, exibir uma bandeira antes de cada opção:
  - 🇧🇷 Português
  - 🇺🇸 English
- Aplicar a troca de idioma à interface principal, abas, botões, configurações, mensagens de validação, pop-ups, avisos, ajuda e textos de diagnóstico.
- Manter a preferência de idioma persistida entre execuções.
- A alteração de idioma deve ser aplicada imediatamente, sem necessidade de reiniciar o aplicativo.
- Garantir que novos recursos adicionados futuramente incluam os textos nos dois idiomas.

## “Conectar ao iniciar” habilitado por padrão

**Objetivo:** fazer o cliente tentar conectar automaticamente ao APRS-IS ao abrir o aplicativo, sem exigir ativação manual dessa preferência em novas instalações.

- Definir **Conectar ao iniciar** como **habilitado por padrão** em novas instalações.
- Manter a opção disponível em **Configuração → APRS / Estação → APRS-IS** para o usuário poder desativá-la.
- Preservar a preferência já salva em instalações existentes; não reativar automaticamente se o usuário já tiver desabilitado essa opção.
- Se a configuração obrigatória da estação estiver incompleta, não iniciar tentativas repetidas de conexão; mostrar a orientação de campos obrigatórios e aguardar correção do usuário.

## Filtro padrão para estações brasileiras

**Objetivo:** reduzir o tráfego inicial do APRS-IS e apresentar, por padrão, apenas estações brasileiras.

- Em novas instalações, configurar o filtro APRS-IS padrão para aceitar **apenas indicativos brasileiros**.
- Considerar os prefixos brasileiros reconhecidos para radioamadorismo, incluindo famílias como **PP, PQ, PR, PS, PT, PU, PV, PW, PX e PY**, além de prefixos especiais brasileiros quando aplicável.
- Implementar o filtro usando a sintaxe nativa do APRS-IS, sem fazer filtragem apenas na interface depois de receber todo o tráfego.
- O filtro deve considerar o **indicativo de origem da estação** e não excluir indevidamente pacotes válidos de estações brasileiras por causa de SSID.
- Manter o usuário livre para editar, ampliar ou remover esse filtro em **Configuração → APRS-IS**.
- No editor gráfico, oferecer uma opção clara como **Somente estações brasileiras (padrão)**.
- Se o usuário escolher outro filtro manual ou gráfico, respeitar integralmente a escolha e não restaurar automaticamente o filtro brasileiro.
- Preservar filtros personalizados já existentes durante atualizações; aplicar o novo padrão apenas quando não houver configuração anterior ou em nova instalação.

## Restaurar configuração padrão e página única de Configuração

**Objetivo:** simplificar a organização da configuração e oferecer uma forma segura de voltar aos valores padrão do aplicativo.

- Transformar **Configuração** em uma **página única**, sem subabas internas.
- Organizar essa página em **seções compartimentalizadas e visualmente bem separadas**, mantendo todos os grupos acessíveis por rolagem.
- Estruturar pelo menos as seguintes seções:
  - **Estação APRS**;
  - **APRS-IS**;
  - **Mapa e Topologia**;
  - **Mensagens / Aparência**;
  - **Aplicativo**;
  - **Backup e Dados**.
- Cada seção deve ter título claro, descrição curta e agrupamento visual consistente, sem misturar parâmetros de protocolo com preferências visuais.
- Incluir botão **Restaurar configuração padrão** em local de destaque na página de Configuração.
- Antes de restaurar, exibir um **pop-up de confirmação** informando que as preferências serão redefinidas.
- A restauração deve devolver todos os parâmetros configuráveis aos valores padrão da versão atual, incluindo servidor APRS-IS, porta, filtro padrão, tema, idioma, fontes e demais preferências.
- Preservar dados operacionais/históricos como mensagens, estações recebidas, logs e tracklogs, salvo se houver uma ação separada e explicitamente destrutiva.
- Após restaurar, atualizar imediatamente a interface com os novos valores padrão.
- Sempre que possível, oferecer também ação **Cancelar** no pop-up sem alterar qualquer configuração.
- Documentar claramente quais itens são restaurados e quais dados não são apagados.

## Ordenação das conversas agrupadas por remetente

**Objetivo:** facilitar a localização de conversas na aba **Mensagens** quando o modo **Agrupar por remetente** estiver ativo.

- No modo **Agrupar por remetente**, tornar o título **Conversas** clicável.
- Ao clicar em **Conversas**, alternar a ordenação da lista de remetentes entre:
  - **ordem alfabética crescente (A → Z)**;
  - **ordem alfabética decrescente (Z → A)**.
- Exibir um indicador visual junto ao título mostrando o sentido atual da ordenação, como **▲ / ▼** ou equivalente.
- A ordenação deve considerar o indicativo/remetente exibido na lista de conversas.
- Manter a conversa atualmente selecionada aberta após a troca da ordenação.
- Não alterar a ordem cronológica das mensagens dentro de cada conversa; a ordenação afeta apenas a lista de conversas/remetentes.
- Persistir a preferência de ordenação durante a sessão e, se conveniente, entre execuções.

## Selecionar conversa e preencher destino automaticamente

**Objetivo:** agilizar o envio de mensagens quando o modo **Agrupar por remetente** estiver ativo.

- Ao selecionar uma conversa/remetente na lista agrupada, preencher automaticamente o campo **Destino** do compositor de mensagens com o indicativo correspondente.
- Usar o indicativo completo da estação selecionada, incluindo SSID quando houver.
- Atualizar o campo imediatamente ao trocar de conversa, sem exigir clique adicional no indicativo.
- Manter o campo **Destino** editável para permitir que o usuário altere manualmente o destinatário depois.
- Se o usuário selecionar a própria estação em algum contexto, evitar preencher o próprio indicativo como destino quando houver outro participante claramente identificável na conversa.
- Não enviar a mensagem automaticamente; apenas preparar o destinatário para que o usuário escreva e confirme o envio.
- Manter esse comportamento compatível com a seleção direta de indicativos já existente em mensagens e estações.
