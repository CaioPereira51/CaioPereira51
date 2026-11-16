# Instalação do contador anual de commits

O arquivo `README.md` agora referencia `./assets/github-commits-ano.svg`.
O gráfico é gerado pelo GitHub Actions diretamente no repositório do perfil.

1. Extraia o ZIP no repositório de perfil `CaioPereira51/CaioPereira51`, mantendo as pastas `.github/`, `scripts/` e `assets/`.
2. Faça commit/push dos arquivos no branch padrão do repositório.
3. No GitHub, abra **Actions → Atualizar commits do ano → Run workflow** para executar imediatamente.
4. Após a execução e o commit do bot, atualize a página do perfil. O gráfico será atualizado automaticamente todos os dias às 08:15 UTC.
5. Se a etapa de push falhar por falta de permissão, configure **Settings → Actions → General → Workflow permissions → Read and write permissions**, quando essa opção estiver disponível. Repositórios com regras de proteção de branch podem exigir configuração adicional.

O card distingue a contagem de *commits* (`totalCommitContributions`) do total de *contribuições* do calendário (que inclui outras atividades). Não exibe os nomes dos repositórios. O primeiro SVG incluído é um marcador visual, sem números inventados; o workflow o substituirá após a primeira execução. O ano é detectado automaticamente a cada execução.
