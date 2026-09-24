# Política de Versionamento

A partir da publicação da **v1.6**, as próximas versões devem seguir esta regra:

- correções, ajustes e melhorias incrementais dentro da linha 1.6: **v1.6.1, v1.6.2, v1.6.3, ...**;
- permanecer na série **1.6.x** até orientação explícita do mantenedor para avançar;
- somente após essa orientação será iniciada a série **v1.7**;
- cada Release deve manter o mesmo número em `VERSION`, `pt2vhf_aprs/__init__.py`, metadados de Windows, nomes dos artefatos, manual, changelog e notas da Release.

Exemplos de sequência válida:

```text
v1.6
v1.6.1
v1.6.2
v1.6.3
...
v1.7   # somente quando autorizado explicitamente
```
