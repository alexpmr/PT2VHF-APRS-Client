# Assinatura e notarização do macOS

Desde a v2.0.7, o job `macos` de `build-production-current.yml` e `macos/build_macos.sh` assinam o `.app` e o DMG
com Developer ID e enviam o DMG para notarização da Apple. Tudo é condicional: sem os segredos abaixo, o DMG sai sem
assinatura, como antes (o usuário precisa liberar em Ajustes > Privacidade e Segurança).

## O que é preciso (conta Apple Developer, US$ 99/ano)

1. Entrar no Apple Developer Program com a Apple ID do mantenedor.
2. Criar um certificado **Developer ID Application** (Xcode > Settings > Accounts > Manage Certificates, ou no portal).
3. Exportar o certificado com a chave privada como `.p12`, com senha.
4. Criar uma **senha de app** em appleid.apple.com (Iniciar sessão e segurança > Senhas de app).
5. Anotar o **Team ID** (10 caracteres) em developer.apple.com > Membership.

## Segredos do repositório (Settings > Secrets and variables > Actions)

| Segredo | Conteúdo |
| --- | --- |
| `MACOS_CERTIFICATE_P12_BASE64` | `base64 -i certificado.p12` |
| `MACOS_CERTIFICATE_PASSWORD` | senha do `.p12` |
| `MACOS_NOTARY_APPLE_ID` | e-mail da Apple ID |
| `MACOS_NOTARY_PASSWORD` | senha de app (não a senha da conta) |
| `MACOS_NOTARY_TEAM_ID` | Team ID |

Só com o certificado, o DMG sai assinado mas não notarizado. Com os cinco, sai notarizado e "grampeado" (stapled),
e abre sem aviso do Gatekeeper.

## O que o build faz

- Importa o `.p12` num keychain temporário do runner.
- Assina cada Mach-O dentro do `.app` (de dentro para fora), depois o `.app`, com Hardened Runtime e
  `macos/entitlements.plist` (o PyInstaller precisa de `allow-unsigned-executable-memory` e `disable-library-validation`).
- Cria o DMG, assina, envia com `xcrun notarytool submit --wait`, grampeia com `stapler` e confere com `spctl`.
