# PT2VHF APRS Client - v1.6.1

Cliente APRS-IS multiplataforma para **Windows, Linux e macOS**, com mapa, mensagens, estações, tracklogs, topologia observada, Log TNC2, banco SQLite local e atualização integrada.

A **v1.6.1** é a primeira atualização incremental da série 1.6. Ela conclui o backlog aberto após a v1.6: OTA totalmente habilitada por padrão em novas instalações, divisão transparente de mensagens longas, nova aba Análise, atalho de Log no popup das estações e limpeza visual da página Configuração.

## Downloads

Cada Release completa publica:

### Windows
- `PT2VHF_APRS_Client_Setup_x64_vX.Y.exe` — instalador recomendado.
- `PT2VHF_APRS_Client_Portable_x64_vX.Y.exe` — executável portátil.

### Linux
- `PT2VHF_APRS_Client_x86_64_vX.Y.AppImage` — AppImage portátil.
- `PT2VHF_APRS_Client_Linux_x86_64_vX.Y.tar.gz` — pacote portátil genérico.
- `pt2vhf-aprs-client_X.Y_amd64.deb` — Debian/Ubuntu e derivados.

### macOS
- `PT2VHF_APRS_Client_macOS_arm64_vX.Y.dmg` — Apple Silicon.
- `PT2VHF_APRS_Client_macOS_x86_64_vX.Y.dmg` — Macs Intel.

### Manual
- `PT2VHF_APRS_Client_Manual_vX.Y.pdf` — manual profissional gerado e validado no workflow da Release.

## Destaques da v1.6.1

### Configuração
- Configuração organizada em seções, iniciando diretamente pela Estação APRS, sem bloco introdutório redundante.
- **Conectar ao iniciar** fica na seção APRS-IS e vem habilitado por padrão em novas instalações.
- Se houver alterações não salvas e o usuário tentar mudar de aba, o cliente oferece **Salvar e sair**, **Descartar alterações** ou **Cancelar**.
- Botão **Restaurar configuração padrão** sem apagar mensagens, estações, logs ou tracklogs.
- Chaveamento rápido de tema no cabeçalho.
- Idiomas **🇧🇷 Português** (padrão) e **🇺🇸 English**.

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
- Selecionar uma conversa preenche automaticamente o campo **Destino**, incluindo SSID.
- Mensagens longas são divididas sem `1/2`, `2/2` ou outros marcadores visíveis; as partes respeitam limites de palavra sempre que possível.
- O controle interno continua mantendo identificação de grupo e status agregado, como **2/3 confirmadas** ou **Todas confirmadas**.
- Retry individual de partes e retry automático configurável por timeout/número máximo de tentativas.
- Cada retry usa novo ID APRS.
- O peso de fonte configurado em Mensagens é aplicado também a **De**, **Para** e **Tipo**.

### Log
- A coluna **Hora** mantém data e hora em uma única linha.
- Clique em **Hora** para alternar entre mais antigos → mais recentes e mais recentes → mais antigos.
- Colunas e cabeçalhos usam alinhamento consistente.

### Mapa, Log e Análise
- OpenStreetMap, OpenTopoMap e Esri World Imagery.
- Tracklogs automáticos de estações móveis.
- O popup da estação oferece **Mostrar log**, abrindo o Log já filtrado pelo indicativo/SSID.
- A análise da rede foi movida para a nova aba **Análise**, com períodos de 1 h, 6 h, 24 h ou 7 dias.
- Ranking de digipeaters e IGates, enlaces que deixaram de aparecer, comparação com o período anterior e métricas agregadas.
- Histórico limitado de eventos de topologia com **animação temporal no mapa**.

### Atualização integrada
- **Verificar atualizações automaticamente** — habilitado por padrão.
- **Baixar atualização automaticamente** — habilitado por padrão em novas instalações.
- **Instalar atualização automaticamente ao fechar** — habilitado por padrão em novas instalações.
- Botão **Verificar atualização agora**.
- O cliente seleciona o asset correspondente à plataforma, baixa apenas da Release oficial do repositório e calcula **SHA-256**; quando o GitHub fornece digest SHA-256, o valor é conferido.
- **Windows Portable:** aplica a nova versão ao fechar e mantém uma cópia para rollback.
- **Windows Setup:** pode iniciar o instalador silencioso.
- **macOS:** pode baixar e abrir o DMG.
- **Linux AppImage:** pode baixar/iniciar o novo AppImage.
- **Linux .deb/.tar.gz:** continuam com instalação manual, pois a atualização do sistema pode exigir privilégios.

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
