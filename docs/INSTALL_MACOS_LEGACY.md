# PT2VHF APRS Client — macOS Intel Legacy (Catalina 10.15.x)

O instalador `PT2VHF_APRS_Client_macOS_Intel_Legacy_vX.Y.Z.dmg`
é diferente dos pacotes Intel atuais (macOS 11+) e Apple Silicon (ARM64).

## Pré-requisitos
- Mac Intel x86_64 com macOS Catalina 10.15.x.
- Teste de abertura do app aprovado em Mac Catalina durante o build.
- Aplicativo obtido exclusivamente de https://www.pt2vhf.com/aprs.

## Instalação
1. Abra o DMG específico **Intel Legacy**.
2. Arraste `PT2VHF APRS Client.app` para Aplicativos.
3. Inicie pela pasta Aplicativos.
4. Se o Gatekeeper bloquear um pacote não notarizado, use
   **Preferências do Sistema > Segurança e Privacidade > Geral > Abrir Mesmo Assim**,
   apenas após confirmar a origem do pacote.
5. Não desative globalmente o Gatekeeper.

## Dados e atualização
Os dados são persistidos em
`~/Library/Application Support/PT2VHF APRS Client/data/pt2vhf_aprs.db`.
Faça backup antes de substituir versões. Não instale DMG Apple Silicon em Mac Intel.
A atualização automática não deve trocar o pacote Legacy pelo Intel moderno.

## Observações
A assinatura Developer ID e a notarização são etapas separadas do teste de
compatibilidade, e dependem das credenciais Apple do mantenedor. Sem notarização,
o macOS pode apresentar o alerta de primeira execução.
