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
