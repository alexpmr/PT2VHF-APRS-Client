# Publicação do APRS Client para macOS Catalina (Intel Legacy)

## Estado da entrega
- Fonte, build específico e validação de compatibilidade preparados.
- O GitHub **não oferece** runner hospedado 10.15, e desde 2026 o runner
  self-hosted oficial só aceita macOS 11+.
- O job `candidate-intel` em `.github/workflows/release-macos-catalina-legacy.yml`
  constrói somente um **candidato não homologado** usando macOS 15 Intel.
  **Não coloque esse DMG no site como versão Catalina.**
- Para o pacote oficial, compile **nativamente** em Mac Intel Catalina 10.15.x,
  faça smoke test e gere o registro de verificação.

## Build homologável no Mac Catalina
1. Instale o Python 3.10 Intel/universal2 da Python Software Foundation e
   o Xcode Command Line Tools compatível com Catalina.
2. Abra o Terminal no Mac Catalina e execute:
   ```bash
   git clone https://github.com/alexpmr/PT2VHF-APRS-Client.git
   cd PT2VHF-APRS-Client
   PYTHON_BIN=/Library/Frameworks/Python.framework/Versions/3.10/bin/python3.10 \
     bash macos/build_macos_legacy.sh
   ```
3. O script verifica a versão do macOS, arquitetura Intel, Python,
   executa os testes, produz DMG, checa Info.plist, verifica a imagem DMG e
   tenta abrir o aplicativo na própria máquina. Uma falha interrompe a entrega.
4. Após sucesso, os arquivos ficam em:
   ```
   dist-macos/PT2VHF_APRS_Client_macOS_Intel_Legacy_v1.15.6.dmg
   dist-macos/catalina-verification.json
   ```
5. Anexe **ambos os arquivos reais** à release
   https://github.com/alexpmr/PT2VHF-APRS-Client/releases/tag/v1.15.6
   no GitHub. Não renomeie os arquivos e não anexe um candidato do CI macOS 15.
6. Em `alexpmr/PT2VHF-Site`, abra Actions > `Publish verified APRS Catalina Intel Legacy DMG`
   > Run workflow. O job verifica tamanho/SHA-256/evidência, comita o
   instalador em `downloads/aprs-client/`, preserva os demais arquivos no
   `updates.json`, atualiza o contador Legacy e confere os bytes na Hostinger.

## Gatekeeper
O pacote Legacy não fica notarizado automaticamente. Sem certificado
Developer ID e credenciais de notarização Apple, o usuário ainda poderá ver
um aviso de segurança; isso não é falha de compatibilidade Catalina.

## Critério de conclusão
Somente anunciar a versão publicada quando o job de publicação terminar
com sucesso e o site oficial servir DMG com SHA-256 idêntico.
