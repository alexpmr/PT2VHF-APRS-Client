# PT2VHF APRS Client - instalação no macOS

## Arquivos disponíveis

A partir da v1.1, a Release publica imagens DMG para:

- **Apple Silicon (arm64)** - Macs com processadores Apple Silicon compatíveis.
- **Intel (x86_64)** - Macs Intel compatíveis com a versão do macOS usada no build.

Escolha o DMG correspondente à arquitetura do seu Mac.

## Instalação

1. Baixe o arquivo `PT2VHF_APRS_Client_macOS_<arquitetura>_vX.Y.dmg`.
2. Abra o DMG.
3. Arraste **PT2VHF APRS Client.app** para **Applications**.
4. Abra o aplicativo pela pasta Aplicativos.

## Primeira abertura e Gatekeeper

Os builds comunitários atuais podem não possuir assinatura Developer ID/notarização da Apple. Nesse caso, o macOS pode bloquear a primeira abertura.

1. Tente abrir o aplicativo.
2. Se ele for bloqueado, abra **Ajustes do Sistema > Privacidade e Segurança**.
3. Localize o aviso referente ao PT2VHF APRS Client e escolha **Abrir Mesmo Assim**, se você confia no arquivo obtido da Release oficial.
4. Confirme a abertura.

Não desative globalmente o Gatekeeper.

## Dados do usuário

O banco e os dados persistentes ficam em:

`~/Library/Application Support/PT2VHF APRS Client/data/pt2vhf_aprs.db`

A atualização do aplicativo não deve apagar esse banco.

## Localização

O botão **Usar minha localização atual** em Configuração solicita permissão ao macOS/WebView. Latitude e longitude são preenchidas quando autorizadas. A altitude só é preenchida se o sistema a fornecer; caso contrário, informe-a manualmente.

## Atualização

Feche o aplicativo, abra o DMG da nova versão e substitua o aplicativo em **Applications**. O banco persistente permanece em Application Support.

## Remoção

Remova o aplicativo da pasta **Applications**. Para também apagar os dados locais, remova manualmente:

`~/Library/Application Support/PT2VHF APRS Client`

Faça backup antes caso deseje preservar mensagens, estações ou configuração.
