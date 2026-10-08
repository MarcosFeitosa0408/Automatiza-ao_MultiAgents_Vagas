# Orientações para trabalhar neste projeto

## Conferência do estado atual
- Leia este arquivo antes de modificar o projeto.
- Confira o estado do Git e os arquivos atuais envolvidos na tarefa.
- Use o código atual como referência. Backups e conversas antigas podem estar desatualizados.
- Não afirme que verificações foram executadas sem apresentar resultados reais.

## Propósito da plataforma
- A plataforma auxilia na descoberta, análise e preparação para oportunidades.
- O candidato decide quais oportunidades deseja seguir.
- Não envie candidaturas, currículos ou mensagens automaticamente.
- Preserve os controles de revisão e aprovação humana.

## Compatibilidade com vagas
- Preserve o cálculo atual de compatibilidade e seus pesos.
- Preserve as classificações atuais: RECOMENDADA a partir de 7/10,
  FILA_SECUNDARIA de 6,5 até abaixo de 7 e NAO_RECOMENDADA abaixo de 6,5.
- A pontuação não representa percentual de requisitos atendidos nem probabilidade de contratação.
- Não implemente um corte de 80% sem uma nova solicitação explícita.
- Não use a classificação, por si só, para impedir uma escolha manual do candidato.

## Dados profissionais e currículo
- Preserve a edição manual do perfil pelo candidato.
- Utilize apenas informações profissionais fornecidas pelo candidato.
- Não invente competências, experiências, cursos, resultados ou requisitos da vaga.
- Diferencie cursos em andamento de cursos concluídos.
- Mantenha os dados completos no perfil e selecione informações relevantes para o currículo.
- Priorize um currículo conciso de uma página, sem apagar informações do perfil.
- Não acrescente competências ao perfil apenas para melhorar a pontuação.
- Não complete anúncios truncados por suposição.

## Preservação de dados e histórico
- Preserve candidaturas, etapas, observações, datas e histórico de acompanhamento.
- Preserve o isolamento dos dados entre contas.
- Não apague dados, backups ou registros como parte de ajustes não relacionados.
- Alterações em persistência exigem avaliação do impacto e da recuperação dos dados.
- Reverter código pelo Git não restaura dados apagados do banco.

## Implementação e validação
- Faça alterações pequenas e relacionadas à solicitação.
- Preserve contratos de API e comportamentos existentes, salvo mudança solicitada.
- Não substitua arquivos inteiros sem conferir seu conteúdo atual.
- Nunca registre senhas, tokens ou dados pessoais reais no repositório.
- Para alterações funcionais, execute testes adequados ao comportamento alterado.
- Backend: utilize python -m pytest tests -v para a suíte do projeto,
  evitando a coleta de testes em pastas de backup.
- Frontend: utilize os scripts existentes de test, lint e build conforme a alteração.
- Para alterações somente de documentação, confira o conteúdo e git diff --check.
- Confira o diff e inclua no commit apenas os arquivos relacionados à tarefa.
- Mantenha mudanças de documentação separadas de mudanças funcionais.
- Após publicação, verifique a versão implantada e o comportamento afetado.

## Comunicação
- Explique o que mudou, como foi validado e quaisquer limitações relevantes.
- Ao orientar pelo PowerShell, forneça etapas claras e confira os resultados.
- Não declare uma publicação ou teste como concluído apenas porque o código foi alterado.
