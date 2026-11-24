"""Configuração comum dos testes.

A partir da v2.0.5 o idioma padrão do app vem do sistema operacional. Os testes
antigos foram escritos com o português como padrão, então fixamos pt-BR aqui;
quem quiser testar a detecção usa os_language.map_language diretamente.
"""
import os

os.environ.setdefault("PT2VHF_LANGUAGE", "pt-BR")
