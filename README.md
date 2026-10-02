# PT2VHF APRS Client - v1.8.4

Cliente APRS-IS multiplataforma para **Windows, Linux e macOS**, com mapa, mensagens, estações, tracklogs, topologia observada, Log TNC2, banco SQLite local e atualização integrada.

A **v1.8.4** adiciona alerta preventivo de **CPU/memória crítica**, com persistência, histerese, cooldown e diagnóstico, e alinha à esquerda a barra contextual da aba **Mapa**, mantendo integralmente os recursos da v1.8.3.

## Downloads da versão mais recente

Os arquivos abaixo apontam diretamente para a **release v1.8.4**, evitando links `latest/download` com nomes de arquivo de versões anteriores.

### Windows
- [Windows x64 — Instalador](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.8.4/PT2VHF_APRS_Client_Setup_x64_v1.8.4.exe)
- [Windows x64 — Portable](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.8.4/PT2VHF_APRS_Client_Portable_x64_v1.8.4.exe)
- [Windows ARM64 — Instalador](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.8.4/PT2VHF_APRS_Client_Setup_ARM64_v1.8.4.exe)
- [Windows ARM64 — Portable](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.8.4/PT2VHF_APRS_Client_Portable_ARM64_v1.8.4.exe)

### Linux
- [Linux x86_64 — AppImage](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.8.4/PT2VHF_APRS_Client_x86_64_v1.8.4.AppImage)
- [Linux x86_64 — DEB](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.8.4/pt2vhf-aprs-client_1.8.4_amd64.deb)
- [Linux x86_64 — TAR.GZ](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.8.4/PT2VHF_APRS_Client_Linux_x86_64_v1.8.4.tar.gz)

### macOS
- [macOS — Apple Silicon](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.8.4/PT2VHF_APRS_Client_macOS_arm64_v1.8.4.dmg)
- [macOS — Intel](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.8.4/PT2VHF_APRS_Client_macOS_x86_64_v1.8.4.dmg)

### Documentação
- [Manual PDF](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.8.4/PT2VHF_APRS_Client_Manual_v1.8.4.pdf)
- [Notas da versão mais recente](https://github.com/alexpmr/PT2VHF-APRS-Client/releases/latest)



## Novidades da v1.8.4

- **Saúde do aplicativo:** monitora separadamente CPU/RAM do PT2VHF APRS Client e do sistema operacional.
- **Alertas críticos:** padrão de 90% para CPU e memória, exigindo 30 s de condição sustentada antes do popup.
- **Popup não bloqueante:** informa recurso, escopo, valor, limite, duração e horário, com acesso ao log de diagnóstico.
- **Antirruído:** histerese de 5 pontos percentuais e cooldown padrão de 10 min; após recuperação, um novo alerta exige novo período crítico sustentado.
- **Configuração:** limites, persistência, cooldown e ativação ajustáveis em **Saúde do aplicativo**.
- **Mapa:** barra contextual com Histórico, período/Completo, Ver, Velocidade, Tipo de mapa, Camadas e KML alinhada à esquerda.
- Novos textos traduzidos para **Português, English, Español e Français**.
- Mantém integralmente Estatísticas, TNC/RF, mapas/camadas, mensagens, atualização integrada e demais recursos da v1.8.3.

## Novidades da v1.8.3

- **Estatísticas → Software / dispositivos APRS:** filtros separados para **Aplicativos APRS**, **Dispositivos/Hardware** e **Não identificados**.
- O ranking e os percentuais são recalculados sobre o conjunto visível, permitindo analisar **somente aplicativos APRS**.
- Clientes como **PT2VHF APRS Client, UI-View, WinAPRS, APRSdroid e Dire Wolf** deixam de competir diretamente com rádios D-STAR, rigs, HTs e trackers quando o filtro de dispositivos está desligado.
- Itens ambíguos ficam como **Indeterminados**, evitando classificação forçada.
- **Mapa → Ver:** o antigo botão **Tudo** foi substituído por **Selecionar tudo** e **Remover tudo**.
- As ações globais incluem categorias, subcategorias e filtros dinâmicos, com persistência da escolha.
- Novos controles traduzidos em **Português, English, Español e Français**.
- Mantém integralmente a porta dinâmica, AIS, TNC/RF, mapas sem API key e demais recursos da v1.8.2.

## Novidades da v1.8.2

- **Porta local automática:** o cliente começa em **8080** e avança para 8081, 8082… quando encontra conflito, usando a primeira porta realmente disponível.
- A porta efetivamente escolhida aparece em **Configuração → Interface local** e é usada automaticamente pelo WebView/navegador.
- **Mapa → Ver → Objetos:** nova categoria **AIS**, separada de **Balão/Radiosonda**.
- **Mapa → Ver:** todos os itens continuam habilitados por padrão em novas configurações, sem sobrescrever escolhas já salvas.
- **Configuração:** removida a bandeira grande do seletor de idioma; permanecem o seletor compacto e as pequenas bandeiras do cabeçalho.
- A captura do Manual PDF e os launchers Windows/Linux/macOS acompanham a porta dinâmica.
- Mantém integralmente TNC/RF, Digipeater, iGate inteligente, mapas sem API key e traduções da v1.8.1.

## Novidades da v1.8.1

- Remove **Relevo sombreado** e mantém **Relevo com corte** como camada de elevação.
- Corrige **Claro/Escuro** para funcionar sem API key.
- Adiciona **CyclOSM, Humanitário/HOT, OSM.DE e ÖPNVKarte**.
- Adiciona fallback automático para OSM quando um provedor alternativo falhar.
- Revisa a aba **TNC / RF** em **Português, English, Español e Français**, incluindo textos dinâmicos e troca imediata de idioma.
- Mantém integralmente KISS Serial/TCP, Digipeater, iGate inteligente, grafo “Quem fala com quem” e segurança de TX da v1.8.0.

## Novidades da v1.8.0

### TNC / RF
- Nova aba **TNC / RF** para operar o cliente também com rádio local, sem substituir o APRS-IS.
- **KISS TCP** para Dire Wolf e outros modems compatíveis e **KISS Serial** para TNCs físicos.
- Detecção/listagem de portas seriais, baud rate, conexão/reconexão e estado TNC no cabeçalho.
- Monitor de frames **AX.25/APRS** recebidos e transmitidos, com origem, destino, path, tipo e representação TNC2.

### Digipeater
- Perfis **Fill-in (WIDE1-1)**, **Wide/Regional (WIDEn-N)** e **Personalizado**.
- Supressão de duplicatas por assinatura do pacote e janela temporal.
- Proteção contra loop, limite de hops e rate limit por estação.
- Fila de transmissão com prioridade para **ACK/REJ e mensagens** sobre telemetria/status repetitivos.

### iGate inteligente
- **RF → APRS-IS** com qAR e preservação do pacote recebido.
- **APRS-IS → RF** restrito a mensagens cujo destinatário tenha sido ouvido **diretamente por RF** dentro da janela configurada.
- Tabela própria de estações ouvidas por RF, distinguindo última audição direta de recepções posteriores via digi.
- Decisões de gating ficam registradas com o motivo de envio, bloqueio ou supressão.

### Quem fala com quem
- O cliente constrói um grafo de interações com origem, destino, meio RF/APRS-IS, quantidade, ACK/REJ e última atividade.
- Modos do otimizador: **Desligado**, **Observação/Recomendação** e **Automático conservador**.
- O modo automático atua em prioridades, duplicatas, gating e contenção de tráfego de baixa prioridade; **não cria um protocolo proprietário nem reescreve arbitrariamente paths APRS de terceiros**.

### Segurança operacional
- **TX automático, Digipeater e iGate Internet→RF ficam desligados por padrão.**
- Para liberar transmissão automática é necessário marcar uma confirmação explícita.
- O botão vermelho **PARAR TX** interrompe imediatamente novas transmissões automáticas sem derrubar a recepção TNC.
- O histórico de frames, decisões e relações fica no SQLite local com retenção configurável.

## Novidades da v1.7.7

- **Histórico:** fica somente na barra contextual do Mapa; o botão global antigo não é mais recriado durante o build.
- **Mensagens:** a ação vermelha **Apagar todas** passa a se chamar **Limpar**.
- **Topologia:** padrão amarelo (`#ffff00`) com **1 px**, a menor espessura disponível.
- **Tracklog:** permanece azul (`#3ba6ff`) por padrão.
- **Animação e som:** ativos por padrão em novas configurações.
- **Atualizações:** verificação automática da versão mais recente a cada **30 minutos**.

## Novidades da v1.7.6

- **Atualização automática Windows:** helper CMD nativo como caminho principal, com confirmação mais robusta antes de fechar o aplicativo.
- **KML:** abre **Salvar como** no aplicativo desktop para escolher pasta e nome do arquivo.
- **Mapa:** **Histórico** e **Exportar KML** ficam na barra contextual de Estações/Tracklog/Topologia.
- **Estatísticas:** novo ranking **Estações que mais interagiram**, considerando somente mensagens manuais entre operadores e excluindo tráfego automático.
- **Testes:** regressões cobrindo updater Windows, KML, barra do Mapa e ranking de conversas.

## Novidades da v1.7.5

- **Exportar KML** na barra superior, com Estações, Posições, Tracklogs e Topologia/enlaces selecionados por padrão.
- Rejeição de posições **0,0**, inválidas, saltos implausíveis e coordenadas incompatíveis com recepção RF observada por iGate conhecido.
- Novos blocos em Estatísticas: **Estações com problemas** e **Possíveis melhorias**.
- Digipeaters e iGates dos rankings são clicáveis e levam diretamente ao Mapa.
- Conversas agrupadas podem ser ordenadas por **Remetente** ou **Data**, com ordem crescente/decrescente.
- **Apagar todas** limpa somente o histórico local de mensagens, após confirmação.

## Destaques da v1.7 e da série 1.6

### Identidade visual
- A **logo APRS oficial enviada para o projeto** é a única fonte da identidade visual: cabeçalho, favicon, bandeja do Windows, ícones Windows/Linux/macOS e capa do Manual PDF.
- Todos os ícones de plataforma são derivados de `pt2vhf_aprs/static/img/app_logo.png`; não há desenho alternativo para macOS nem conversão de uma logo SVG diferente para o manual.
- O pipeline valida a presença e o formato PNG da logo antes de gerar os pacotes.

### Configuração
- Configuração organizada em seções, iniciando diretamente pela Estação APRS, sem bloco introdutório redundante.
- **Conectar ao iniciar** fica na seção APRS-IS e vem habilitado por padrão em novas instalações.
- Se houver alterações não salvas e o usuário tentar mudar de aba, o cliente oferece **Salvar e sair**, **Descartar alterações** ou **Cancelar**.
- Botão **Restaurar configuração padrão** sem apagar mensagens, estações, logs ou tracklogs.
- Chaveamento rápido de tema no cabeçalho.
- Idiomas **Português** (padrão), **English**, **Español** e **Français**, com seletor rápido no topo e persistência da preferência.
- A v1.7.1 amplia a cobertura de tradução de textos estáticos e dinâmicos e atualiza imediatamente as áreas dependentes do idioma.

### Identificação do próprio cliente
- As transmissões geradas pelo aplicativo usam o TOCALL experimental **APZVHF**, reservado aqui para identificar o **PT2VHF APRS Client** enquanto não houver uma alocação oficial específica.
- Isso permite que o ranking da aba Estatísticas acompanhe a quantidade de instalações observadas do próprio cliente.

### APRS-IS e filtros
- Servidor padrão do aplicativo: `soam.aprs2.net:14580`, com tentativa alternativa por `rotate.aprs2.net` quando aplicável.
- Novas instalações usam o filtro:
  `p/PP/PQ/PR/PS/PT/PU/PV/PW/PX/PY/ZV/ZW/ZX/ZY/ZZ`
- Filtros personalizados de instalações existentes são preservados.
- Editor gráfico combina:
  - filtro Brasil;
  - raio usando a posição da estação ou centro informado;
  - prefixos;
  - indicativos exatos;
  - área geográfica;
  - tipos de pacote.
- Interpretação de filtros conhecidos, aviso para componentes não representados, validação básica e botão **Copiar filtro**.

### Mensagens
- Conversas agrupadas podem ser ordenadas **A → Z** ou **Z → A** clicando em **Conversas**.
- Selecionar uma conversa preenche automaticamente o campo **Destino**, incluindo SSID; alterar o destinatário também sincroniza a conversa em foco, evitando divergência entre a conversa visível e o indicativo que receberá a mensagem.
- Os botões **Agrupado por remetente**, **Minhas mensagens** e **Não lidas** são compactos e mantêm seus rótulos em uma linha.
- Quando chega uma mensagem direta enquanto outra aba está aberta, a aba **Mensagens** fica destacada/pulsando até o usuário acessá-la.
- Em **Estatísticas → Estações mais ativas**, o indicativo é clicável e abre Mensagens com o destinatário já preenchido para resposta rápida.
- Mensagens longas são divididas sem `1/2`, `2/2` ou outros marcadores visíveis; as partes respeitam limites de palavra sempre que possível.
- O controle interno continua mantendo identificação de grupo e status agregado, como **2/3 confirmadas** ou **Todas confirmadas**.
- Retry individual de partes e retry automático configurável por timeout/número máximo de tentativas.
- Cada retry usa novo ID APRS.
- O peso de fonte configurado em Mensagens é aplicado também a **De**, **Para** e **Tipo**.
- Botão **Não lidas** para mostrar somente mensagens individuais recebidas ainda não lidas, inclusive no modo agrupado.
- O estado lida/não lida é persistido; **Ler mensagem**, seleção de conversa ou seleção explícita de mensagem atualizam esse estado.
- Estações favoritas recebem **estrela amarela** e ficam priorizadas nas conversas agrupadas e nas sugestões do campo Destino.

### Log
- A coluna **Hora** mantém data e hora em uma única linha.
- Clique em **Hora** para alternar entre mais antigos → mais recentes e mais recentes → mais antigos.
- Colunas e cabeçalhos usam alinhamento consistente.

### Mapa, Log e Estatísticas
- Mapas-base **OpenStreetMap, OpenTopoMap, Claro, Escuro, CyclOSM, Humanitário / HOT, OSM.DE, ÖPNVKarte e Esri World Imagery**.
- **Claro e Escuro não exigem API key**: usam tiles OpenStreetMap com tratamento visual local no cliente.
- Em **Camadas**, **Clima** permanece independente do mapa-base e **Relevo com corte** usa DEM real para destacar somente terreno a partir da cota selecionada.
- **Relevo sombreado foi removido na v1.8.1**.
- Se um mapa-base alternativo falhar repetidamente, o cliente volta automaticamente para **OpenStreetMap** e registra o evento no diagnóstico.
- O **Relevo com corte** possui slider vertical no lado direito do mapa, máximo padrão de 3.000 m configurável até 9.000 m e opacidade independente.
- A antiga área **Atividade** foi removida do Mapa. **Estações**, **Tracklog** e **Topologia observada** têm controles independentes de liga/desliga e período (**Completo, 1 h, 6 h, 24 h e 7 dias**), todos fora do canvas.
- O **Histórico/Replay** passa a ser um controle contextual logo abaixo das abas e só aparece quando o **Mapa** está ativo.
- Na v1.7.2, **Estações**, **Tracklog** e **Topologia observada** ficam na mesma linha contextual do **Histórico**, mantendo a barra compacta e liberando mais área útil para o mapa.
- O popup da estação mostra a data/hora da **Última recepção** acompanhada do tempo decorrido (minutos, horas ou dias), atualizado enquanto o popup permanece aberto.
- Tracklogs ignoram saltos de posição incompatíveis com deslocamento realista; o backend preserva a última posição válida e o mapa também quebra linhas históricas em saltos anômalos/relocações.
- A **Legenda** do Mapa pode ser minimizada/expandida; a preferência fica salva localmente para a próxima execução.
- Tracklogs automáticos de estações móveis.
- O popup da estação oferece **Mostrar log**, abrindo o Log já filtrado pelo indicativo/SSID.
- As estatísticas da rede ficam na aba **Estatísticas**, com **Completo** como período padrão, além de 1 h, 6 h, 24 h e 7 dias.
- Ranking de **estações mais ativas** por tráfego útil, excluindo telemetria, iGates e digipeaters; rankings dedicados de digipeaters e iGates, enlaces que deixaram de aparecer, comparação com o período anterior e métricas agregadas.
- **Ranking de software/dispositivos APRS** com nome amigável resolvido pela base APRS Device Identification, quantidade e percentual; o identificador técnico permanece interno e deixa de poluir a apresentação.
- A v1.7.2 consolida em uma única linha TOCALLs diferentes que resolvem para o mesmo nome amigável de software/dispositivo, recalculando quantidade e percentual sem misturar versões com nomes distintos.
- A v1.7.3 consolida também **versões e aliases da mesma família de cliente**. Ex.: **Dire Wolf 1.7, 1.8 e 1.9** aparecem como uma única linha **Dire Wolf**; nomes originais e TOCALLs continuam preservados internamente para diagnóstico.
- A aba **Estatísticas** usa fonte padrão ligeiramente maior e ganha controle próprio de tamanho da fonte em Configurações.
- O Mapa ganhou **legenda dos tipos de linhas**: tracklog, enlace RF, IGate/APRS-IS, replay temporal e pacote em movimento. Em qAR/qAO, o salto físico até o IGate é tratado como RF; o papel de IGate é mantido como metadado, não como meio do enlace.
- Animação do tráfego APRS em modos **Histórico** e **Ao vivo**, com Play/Pausa, início, avanço/recuo, velocidades 0,5x/1x/2x/5x/10x, timestamp e contadores. Em novas instalações, a animação **Ao vivo vem ativada por padrão**, podendo ser desativada em Configurações.
- Em pacotes com múltiplos enlaces observados, os segmentos podem ser animados simultaneamente, reproduzindo a propagação multi-hop.
- Cada transmissão recebida pode gerar som curto e destacar temporariamente em vermelho o marcador da estação de origem; som e destaque são configuráveis separadamente.
- Estações favoritas são persistidas e ficam fixadas no topo da aba Estações; a estrela também aparece no popup do mapa e na área de Mensagens.

### Queries APRS e diagnóstico
- No popup de cada estação no Mapa há botões para **Posição**, **Status**, **Ouvidos**, **Ping/ACK** e **Trace**.
- O Ping/ACK mede o tempo até a confirmação APRS e registra RTT/timeout.
- O Trace usa somente o caminho efetivamente recebido. Hops com posição conhecida são desenhados no mapa; os demais continuam listados como não localizados.
- Em Configuração é possível habilitar respostas automáticas a queries de posição, status e trace. O padrão é desligado para evitar transmissões inesperadas.
- O histórico de queries e respostas fica no banco local e é usado pelo diagnóstico do popup.
- O popup exibe uma área **Resultado da última query** com status, resposta, RTT e caminho do Trace, além do botão **Ver histórico de queries**.

- O indicador **Nova versão** pulsa quando há atualização disponível. O clique abre um modal persistente; a aplicação só encerra depois que o helper externo de atualização confirma que iniciou corretamente.

### Atualização integrada
- **Verificar atualizações automaticamente** — habilitado por padrão e executado na abertura e depois a cada **5 minutos**.
- Quando aparece **Nova versão**, clicar no indicador ou em **Baixar e instalar nova versão** inicia o fluxo automático.
- Na v1.7.3, o botão de instalação fornece feedback imediato e o gerador dos helpers PowerShell/Bash foi corrigido para gravar quebras de linha reais, evitando o caso em que o clique parecia não produzir efeito.
- Na v1.7.4, qualquer falha de atualização é mostrada **dentro do modal**, com o detalhe técnico preservado; o toast também fica acima do modal, sem desfoque, e os controles são reativados após o erro.
- O diagnóstico do updater registra solicitação, asset, URL, caminho temporário, tamanho, SHA-256 e erros de instalação.
- O cliente identifica **plataforma, arquitetura e formato em execução**, seleciona o asset exato da Release oficial, confere o tamanho e calcula **SHA-256**; quando o GitHub fornece digest SHA-256, o valor também é validado.
- Um **updater auxiliar separado** é iniciado antes do encerramento do processo atual. A aplicação tenta encerrar seus componentes de forma limpa; se a instância anterior permanecer viva após o timeout, o helper encerra somente o PID daquela instância antes de instalar.
- Um lock em arquivo com PID impede duas instâncias de iniciarem atualizações concorrentes e permite recuperar lock obsoleto após crash.
- **Windows Portable:** mantém backup para rollback, troca o executável pelo asset Portable e abre a nova versão.
- **Windows Setup:** executa o instalador correspondente com elevação/UAC quando necessária e relança a aplicação.
- **Linux:** AppImage e TAR.GZ são substituídos pelo novo binário; instalações DEB usam dpkg/pkexec quando disponível; a nova versão é relançada.
- **macOS:** o DMG é montado pelo updater, o bundle é substituído quando o local é gravável ou instalado em ~/Applications como fallback, e a nova versão é aberta.
- Configurações e banco SQLite ficam fora dos binários e são preservados. Em caso de falha antes da substituição, a versão funcional existente não é removida.

## Conexão e identificação

Para conectar ao APRS-IS são exigidos:
- Indicativo;
- Latitude;
- Longitude;
- Altitude.

O passcode APRS-IS é calculado automaticamente a partir do indicativo-base. O SSID não altera o passcode.

Se a geolocalização não fornecer altitude, o cliente pode usar **0 m** como contingência para não bloquear a conexão, mantendo aviso para o usuário informar o valor real. Ao transmitir beacon ainda com essa contingência, a transmissão é permitida e uma recomendação não bloqueante é exibida.

## Dados locais

O banco SQLite é mantido fora dos binários e preservado nas atualizações:

- Windows: `%LOCALAPPDATA%\PT2VHF APRS Client\data\pt2vhf_aprs.db`
- Linux: `~/.local/share/PT2VHF-APRS-Client/data/pt2vhf_aprs.db`
- macOS: `~/Library/Application Support/PT2VHF APRS Client/data/pt2vhf_aprs.db`

A exportação JSON de configuração pode conter o passcode APRS-IS em texto legível. Guarde o arquivo em local seguro.

## Linux

### AppImage
```bash
chmod +x PT2VHF_APRS_Client_x86_64_v1.6.1.AppImage
./PT2VHF_APRS_Client_x86_64_v1.6.1.AppImage
```

### Debian/Ubuntu
```bash
sudo apt install ./pt2vhf-aprs-client_1.6.1_amd64.deb
pt2vhf-aprs-client
```

### tar.gz
Consulte `docs/INSTALL_LINUX.md` para o fluxo portátil completo.

O workflow executa smoke tests no Ubuntu 22.04 e 24.04. Em desktops Linux com `notify-send`, mensagens pessoais podem gerar notificação nativa. No macOS, o cliente usa a notificação do sistema quando disponível.

## Política de versionamento

Após a **v1.6**, correções e melhorias incrementais seguem a série **v1.6.1, v1.6.2, v1.6.3, ...**. A passagem para **v1.7** somente ocorrerá mediante orientação explícita do mantenedor. Consulte `VERSIONING.md`.

## Segurança e assinatura

- A interface HTTP local escuta em `127.0.0.1`.
- Use somente arquivos publicados na Release oficial.
- Os builds podem permanecer sem assinatura/notarização de plataforma enquanto o projeto conclui esses processos; consulte `CODE_SIGNING_POLICY.md` e a documentação de instalação.
- Não desative mecanismos de segurança do sistema operacional globalmente para executar o cliente.

## Desenvolvimento

Validação local:

```bash
python -m compileall -q pt2vhf_aprs windows_app.py linux_app.py macos_app.py tools
python -m pytest -q
node --check pt2vhf_aprs/static/js/app.js
```

O workflow oficial também gera SBOMs, inventários de licenças e o manual PDF da versão.

---

**Por Alex, PT2VHF**


### Sobre e divulgação APRS
- Nova aba **Sobre**, com apresentação de **Alex, PT2VHF**, objetivo do projeto, link **tiny.cc/aprs**, WhatsApp **+55 61 98402-3634** e e-mail **alexpmr@gmail.com**.
- A aba acompanha o idioma corrente (**PT/EN/ES/FR**).
- O botão de divulgação prepara um **Announcement APRS BLNA** usando o indicativo/SSID corrente como remetente, mostra prévia, permite edição e exige confirmação explícita.
- O envio é manual e único; não existe repetição automática da divulgação.
