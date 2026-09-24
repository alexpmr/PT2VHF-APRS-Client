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



## Versão para Linux

**Objetivo:** disponibilizar uma versão oficial do PT2VHF APRS Client para Linux, mantendo o máximo possível de compatibilidade com a versão Windows.

### Escopo planejado

- Criar build oficial para **Linux x86_64**.
- Avaliar distribuição em formato simples para usuário final, priorizando:
  - **AppImage** como opção portátil;
  - pacote **.deb** para Debian/Ubuntu e derivados, se viável;
  - arquivo compactado `.tar.gz` como alternativa genérica.
- Manter a mesma interface integrada sempre que o mecanismo WebView disponível no Linux permitir.
- Caso a janela integrada não esteja disponível no ambiente, permitir uso pelo navegador local como fallback.
- Preservar recursos principais:
  - APRS-IS;
  - SQLite;
  - Mapa;
  - Mensagens;
  - Estações;
  - Log;
  - Topologia observada;
  - Configuração e Ajuda.
- Definir diretório de dados conforme convenções Linux, preferencialmente em `~/.local/share/PT2VHF-APRS-Client/` ou equivalente via XDG.
- Garantir que atualização/remoção do aplicativo não apague automaticamente o banco e as configurações do usuário.
- Criar workflow no GitHub Actions para gerar e anexar os artefatos Linux às Releases.
- Incluir número da versão no nome dos arquivos Linux publicados.

### Instruções de instalação

A Release deverá incluir documentação em português com instruções completas para cada formato disponibilizado.

As instruções deverão cobrir:

- requisitos mínimos e distribuições testadas;
- como instalar dependências necessárias;
- como instalar e executar o AppImage;
- como instalar o pacote `.deb`, se houver;
- como executar a versão `.tar.gz`, se houver;
- como conceder permissão de execução com `chmod +x`;
- localização do banco SQLite e arquivos de configuração;
- como atualizar para uma nova versão preservando os dados;
- como desinstalar o aplicativo;
- como iniciar o cliente automaticamente com a sessão, se desejado;
- procedimento de diagnóstico pelo navegador/local host quando necessário.

### Documentação

- Adicionar uma seção **Linux** no README.
- Incluir arquivo de instalação específico, por exemplo `docs/INSTALL_LINUX.md`.
- Nas notas de cada Release, identificar claramente quais arquivos são para Windows e quais são para Linux.
- Fornecer comandos prontos para copiar e colar, evitando exigir conhecimento avançado de Linux.



## Nova política de versionamento

**Objetivo:** simplificar a identificação das versões publicadas do PT2VHF APRS Client.

- A próxima versão oficial deverá iniciar em **v1.0**.
- As versões seguintes deverão avançar em incrementos simples:
  - **v1.1**
  - **v1.2**
  - **v1.3**
  - e assim sucessivamente.
- Deixar de usar, nas novas releases, o esquema atual `0.3.x`.
- Atualizar de forma consistente:
  - arquivo `VERSION`;
  - metadados do executável Windows;
  - versão do instalador;
  - nome dos arquivos publicados;
  - README;
  - CHANGELOG;
  - notas da Release;
  - indicador de versão dentro da aplicação;
  - testes automatizados relacionados à versão.
- Preservar normalmente o histórico das versões antigas `0.x`; não renomear releases já publicadas.
- Os arquivos publicados deverão seguir o novo número, por exemplo:
  - `PT2VHF_APRS_Client_Setup_x64_v1.0.exe`
  - `PT2VHF_APRS_Client_Portable_x64_v1.0.exe`

