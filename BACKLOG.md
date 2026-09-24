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
