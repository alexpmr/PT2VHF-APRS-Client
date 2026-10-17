# Retenção de downloads do PT2VHF APRS Client

A distribuição oficial de instaladores, versões portáteis e manual PDF concentra-se **somente na última GitHub Release estável publicada**.

A rotina `tools/prune_obsolete_release_downloads.py` identifica a última versão a partir de `VERSION` e de `/releases/latest`, bloqueando a limpeza se houver divergência ou se os downloads da versão atual estiverem incompletos.

Arquivos removidos de Releases anteriores: `.exe`, `.msi`, `.dmg`, `.pkg`, `.deb`, `.rpm`, `.AppImage`, `.pdf`, `.zip`, `.7z` e `.tar.gz`.

**Preservados:** notas de Releases, tags Git, código-fonte, CHANGELOG, issues, PRs, SBOMs e licenças de terceiros. O histórico das versões anteriores permanece auditável, mas seus instaladores e manuais não estarão mais disponíveis para baixar.

A rotina é **dry-run por padrão**. O workflow `.github/workflows/prune-obsolete-downloads.yml` só executa exclusões para o commit explícito de manutenção na `main`, após validar a versão mais recente. Logs do GitHub Actions documentam quantidade e progresso. Atualizações futuras exigem nova execução deliberada da rotina se também precisarem de limpeza.
