# Automatiza-ao_MultiAgents_Vagas
MultiAgents em automatização de Vagas de Emprego

# AGENTS.md

# Plataforma_Especialização_Multiagente_Vaga

## Objetivo

Construir uma plataforma multiagente profissional para descoberta, qualificação, personalização, preparação, candidatura, acompanhamento e otimização de oportunidades profissionais.

O sistema deve ser:

- automatizado;
- interativo;
- dinâmico;
- orientado por critérios;
- auditável;
- testável;
- modular;
- baseado em dados reais.

O objetivo não é maximizar indiscriminadamente o número de candidaturas.

O objetivo é aumentar a eficiência da busca por oportunidades compatíveis, melhorar a qualidade das candidaturas e aprender com os resultados reais do processo seletivo.

---

# Fonte oficial do candidato

O arquivo:

`data/master_profile/MASTER_PROFILE.json`

é a fonte oficial de verdade sobre o candidato.

Os agentes devem utilizar somente informações comprovadas nesse perfil ou em outras fontes explicitamente autorizadas pelo sistema.

## Regra fundamental de evidência

Nunca inventar:

- competências;
- experiências;
- empresas;
- cargos;
- formação;
- certificações;
- resultados;
- métricas;
- salários;
- projetos;
- tecnologias;
- vagas;
- informações pessoais.

Quando uma informação necessária não estiver comprovada:

`NAO_IDENTIFICADO`

Nunca adicionar uma competência apenas porque uma vaga a solicita.

Nunca modificar fatos do `MASTER_PROFILE` para aumentar artificialmente o fit de uma candidatura.

---

# Pipeline principal

O fluxo conceitual da plataforma é:

`DISCOVERY`
→ `QUALIFICATION`
→ `PERSONALIZATION`
→ `VALIDATION`
→ `HUMAN APPROVAL`
→ `APPLICATION`
→ `TRACKING`
→ `FOLLOW-UP`
→ `OPTIMIZATION`

O objeto central que acompanha a candidatura é:

`JobApplicationObject`

Arquivo:

`core/schemas/job_application.py`

O pipeline deve evoluir progressivamente para operar através desse objeto e de `application_id`.

---

# Arquitetura Multiagente

## Agent 00 — Memory

Responsável por:

- carregar `MASTER_PROFILE.json`;
- validar sua estrutura;
- disponibilizar dados confiáveis aos demais agentes;
- impedir o uso de informações não comprovadas.

Arquivo principal:

`agents/agent_00_memory/memory_agent.py`

---

## Agent 01 — Discovery

Responsável pela descoberta, normalização e deduplicação de oportunidades.

Deve priorizar cargos compatíveis com os objetivos presentes no `MASTER_PROFILE`.

A descoberta real de vagas ainda não está implementada.

Quando essa integração for criada:

- utilizar providers/interfaces quando apropriado;
- permitir múltiplas fontes;
- evitar scraping frágil como núcleo da arquitetura;
- não inventar vagas;
- não realizar candidatura durante Discovery.

---

## Agent 02 — Qualification

Responsável por avaliar a compatibilidade entre candidato e vaga.

Score esperado:

`0.0` a `10.0`

Pesos atuais:

- competências técnicas: 35%;
- experiência profissional: 20%;
- atividades/responsabilidades: 15%;
- senioridade: 10%;
- localização/modelo de trabalho: 10%;
- compatibilidade ATS: 10%.

Regra estratégica:

- `fit_score >= 7.0`: faixa principal recomendada;
- `6.5 <= fit_score < 7.0`: fila secundária possível;
- `fit_score < 6.5`: normalmente bloqueado pelo Validation Gate.

Requisitos eliminatórios devem ser tratados separadamente.

O scoring atual é uma primeira implementação e não deve ser apresentado como uma medição científica ou definitiva de empregabilidade.

---

## Agent 03 — Personalization

Responsável por selecionar informações verdadeiras e relevantes para uma vaga.

Pode trabalhar com:

- competências;
- experiências;
- projetos;
- palavras-chave ATS;
- resumo profissional;
- posteriormente currículo e carta de apresentação.

Somente utilizar informações comprovadas.

Exemplo:

Se uma vaga solicitar `Apache Spark` e o `MASTER_PROFILE` não comprovar essa competência, `Apache Spark` não deve ser inserido em `selected_skills`.

A competência deve permanecer identificada como requisito não suportado quando aplicável.

Nunca fabricar experiência para aumentar o fit.

---

## Validation Gate

Responsável por impedir que uma candidatura avance quando existirem problemas críticos.

Deve considerar, entre outros:

- fit mínimo;
- evidências verificadas;
- requisitos eliminatórios;
- informações não suportadas.

O `ValidationGate` não deve ser contornado para acelerar o pipeline.

---

## Agent 04 — Application

Responsável por preparar a candidatura para decisão humana.

Estados importantes:

- `PENDING_HUMAN_APPROVAL`;
- `APPROVED_BY_HUMAN`;
- `REJECTED_BY_HUMAN`.

Uma candidatura somente pode ficar:

`ready_to_apply = true`

depois de aprovação humana válida.

Não realizar candidatura autônoma em massa.

---

## Human Approval

A aprovação humana é uma regra crítica da plataforma.

Fluxo esperado:

`PREPARED`
→ `PENDING_HUMAN_APPROVAL`
→ `APPROVED_BY_HUMAN`
→ `READY_TO_APPLY`

ou:

`PREPARED`
→ `PENDING_HUMAN_APPROVAL`
→ `REJECTED_BY_HUMAN`

Não remover, contornar ou simular aprovação humana para acelerar uma automação.

---

## Agent 05 — Tracking

Responsável por registrar a evolução da candidatura.

Estados utilizados:

- `DISCOVERED`
- `QUALIFIED`
- `VALIDATION_REVIEW`
- `APPROVED`
- `READY_TO_APPLY`
- `APPLIED`
- `SCREENING`
- `INTERVIEW`
- `FINAL`
- `OFFER`
- `HIRED`
- `REJECTED`
- `WITHDRAWN`
- `NO_RESPONSE`
- `EXPIRED`
- `APPLICATION_FAILED`

As transições devem respeitar as regras definidas pelo `TrackingAgent`.

Não permitir transições incoerentes apenas para facilitar implementação ou testes.

---

## Agent 06 — Follow-up

Responsável por decidir quando um acompanhamento profissional é adequado.

Regras atuais:

- primeiro follow-up após aproximadamente 5 dias;
- segundo follow-up aproximadamente 7 dias depois;
- máximo de 2 follow-ups;
- não realizar follow-up em estados incompatíveis;
- evitar mensagens repetitivas ou insistentes.

Atualmente o agente decide elegibilidade.

Geração e envio real de mensagens ainda não fazem parte do fluxo operacional.

---

## Agent 07 — Optimization

Responsável por analisar resultados reais do funil.

Métricas atualmente implementadas incluem:

- total de candidaturas;
- screening ou além;
- entrevistas;
- etapas finais;
- ofertas;
- contratações;
- rejeições;
- response rate;
- interview rate;
- offer rate;
- hire rate.

Evoluções futuras podem incluir:

- tempo médio entre etapas;
- desempenho por fonte;
- desempenho por faixa de fit;
- desempenho por cargo;
- recomendações de estratégia.

O aprendizado deve utilizar dados registrados no sistema.

Nunca gerar taxas fictícias para preencher ausência de dados.

Nunca alterar fatos do `MASTER_PROFILE`.


---

# Orchestrator

Arquivo principal:

`core/orchestrator/orchestrator.py`

O `JobOrchestrator` é a camada responsável por coordenar os agentes e o pipeline.

Responsabilidades atuais incluem:

- criação do `JobApplicationObject`;
- qualificação;
- personalização;
- preparação;
- aprovação humana;
- início do tracking;
- atualização de status;
- verificação de follow-up;
- cálculo de métricas;
- acesso ao repository de candidaturas.

Evitar colocar lógica de negócio complexa diretamente nos endpoints FastAPI.

Os endpoints devem delegar as operações ao Orchestrator e às camadas apropriadas.

---

# Objeto central da candidatura

O modelo central implementado é:

`JobApplicationObject`

Arquivo:

`core/schemas/job_application.py`

Estrutura atual:

- `application_id`;
- `job`;
- `qualification`;
- `personalization`;
- `preparation`;
- `tracking`;
- `created_at`;
- `updated_at`.

O `JobApplicationObject` deve ser utilizado progressivamente como contrato central entre as etapas.

Evitar criar estruturas paralelas desnecessárias para representar a mesma candidatura.

O campo `updated_at` existe, mas sua atualização automática e consistente após mutações ainda precisa ser aprimorada.

---

# Repository

Arquivo atual:

`core/repositories/job_application_repository.py`

Existe uma implementação de repository em memória.

Operações atuais:

- `save`;
- `get`;
- `list_all`;
- `delete`.

Essa implementação é temporária e perde os dados quando o processo da aplicação é reiniciado.

A evolução planejada é adicionar persistência real com PostgreSQL.

A API deve acessar as candidaturas através do Orchestrator/Repository, e não manipular diretamente a estrutura interna de armazenamento.

Ao implementar persistência definitiva, preservar a separação entre regras de negócio e infraestrutura.

---

# Stack atual

## Backend

- Python 3.12+
- FastAPI
- Pydantic v2
- Pytest
- Uvicorn
- HTTPX

## Persistência

Atualmente:

- Repository Pattern;
- armazenamento em memória.

Planejado:

- PostgreSQL;
- SQLAlchemy ou outra camada de persistência adequada;
- migrations quando a persistência relacional for implementada.

Não introduzir uma tecnologia de persistência de forma silenciosa.

Antes de uma mudança estrutural importante nessa camada, analisar o código existente e preservar os contratos utilizados pelo Orchestrator.

## Inteligência Artificial

Planejado:

- integração OpenAI/Agents SDK ou equivalente;
- agentes com ferramentas quando apropriado;
- guardrails;
- Human-in-the-Loop;
- uso de evidências do `MASTER_PROFILE`.

Ainda não existe integração operacional com LLM/OpenAI API.

Não adicionar uma dependência de IA apenas para substituir regras determinísticas que já funcionam adequadamente.

## Frontend planejado

- React;
- TypeScript.

## Infraestrutura

Atual:

- Git;
- GitHub;
- GitHub Actions.

Planejado:

- Docker;
- PostgreSQL;
- ambiente de execução/deploy apropriado.

---

# API

Arquivo principal:

`main.py`

A aplicação FastAPI possui endpoints legados e o novo pipeline central baseado em `application_id`.

## Pipeline central implementado

Atualmente existem:

- `POST /job-applications`
- `GET /job-applications`
- `GET /job-applications/{application_id}`
- `POST /job-applications/{application_id}/qualify`
- `POST /job-applications/{application_id}/personalize`
- `POST /job-applications/{application_id}/prepare`

O endpoint de consulta de uma candidatura inexistente deve retornar HTTP `404`.

O pipeline central foi interrompido propositalmente após a etapa `prepare`.

## Próximas etapas da API central

Implementar progressivamente:

- aprovação humana por `application_id`;
- rejeição humana por `application_id`;
- início de tracking por `application_id`;
- atualização de tracking por `application_id`;
- consulta de elegibilidade de follow-up;
- métricas das candidaturas.

Preservar compatibilidade com endpoints antigos enquanto a migração para o pipeline central estiver em andamento, salvo quando uma alteração incompatível for explicitamente aprovada.

Erros de ordem de estágio ou regras de negócio não devem resultar em respostas HTTP genéricas quando puderem ser traduzidos para respostas profissionais como `404`, `409` ou `422`, conforme o caso.

Não alterar essa política de erros indiscriminadamente: analisar o significado do erro antes de escolher o status HTTP.

---

# Estado atual do projeto

## Já implementado

- `MASTER_PROFILE.json`;
- schemas Pydantic;
- Agent 00 — Memory;
- Agent 01 — Discovery inicial;
- Agent 02 — Qualification;
- Agent 03 — Personalization;
- Agent 04 — Application;
- Agent 05 — Tracking;
- Agent 06 — Follow-up;
- Agent 07 — Optimization;
- Validation Gate;
- JobOrchestrator;
- JobApplicationObject;
- Repository em memória;
- FastAPI;
- health check;
- testes unitários;
- testes de integração;
- testes de API;
- GitHub Actions;
- criação de candidatura por API;
- consulta de candidatura por ID;
- retorno `404` para candidatura inexistente;
- listagem de candidaturas;
- qualificação por ID;
- personalização por ID;
- preparação por ID.

## Ainda não concluído

- aprovação humana central por `application_id`;
- rejeição humana central por `application_id`;
- tracking central completo pela API;
- follow-up central pela API;
- optimization/métricas centrais pela API;
- persistência PostgreSQL;
- frontend;
- autenticação;
- descoberta real de vagas;
- integração operacional com LLM/Agents SDK;
- envio real de candidatura;
- geração/envio operacional de follow-up;
- Docker;
- interface operacional;
- tratamento completo de erros HTTP;
- response models consolidados;
- atualização automática consistente de `updated_at`;
- logging estruturado;
- event system operacional;
- lint/type checking no CI.

---

# Estrutura principal do repositório

A estrutura inclui:

```text
agents/
  agent_00_memory/
  agent_01_discovery/
  agent_02_qualification/
  agent_03_personalization/
  agent_04_application/
  agent_05_tracking/
  agent_06_followup/
  agent_07_optimization/

core/
  schemas/
  validation/
  orchestrator/
  events/
  repositories/

data/
  master_profile/
  raw/
  processed/
  applications/

documents/
  base/
  personalized/
  cover_letters/

tests/
  agents/
  api/
  integration/
  validation/
  application/
  tracking/
  followup/
  optimization/
  schemas/
  repositories/

config/

.github/
  workflows/
```

A ausência ou presença de um diretório vazio não deve ser usada como prova de que uma funcionalidade está implementada.

O Git não mantém diretórios vazios por si só.


---

# Testes

Framework principal:

`pytest`

Comando padrão para execução da suíte:

```bash
python -m pytest -v
```

Todo comportamento novo relevante deve possuir teste.

Antes de considerar uma implementação concluída:

1. executar os testes relacionados;
2. adicionar ou atualizar testes para o novo comportamento;
3. executar a suíte completa;
4. corrigir regressões relacionadas à alteração;
5. informar claramente o resultado.

Não afirmar que uma funcionalidade nova está validada apenas porque testes antigos continuam verdes.

Testes devem verificar comportamento real e não apenas executar código sem validar resultados relevantes.

---

# GitHub Actions

Workflow atual:

`.github/workflows/tests.yml`

A suíte é executada automaticamente em:

- push para `main`;
- pull requests para `main`.

Um workflow verde significa que a suíte executada passou.

Isso não significa automaticamente que toda a aplicação possui cobertura completa.

Uma falha antiga no histórico do GitHub Actions não deve ser confundida com o estado atual quando execuções posteriores comprovarem a correção.

---

# Segurança

Nunca armazenar diretamente no repositório:

- API keys;
- tokens;
- senhas;
- credenciais;
- segredos;
- dados pessoais desnecessários;
- outras informações sensíveis.

Utilizar, quando necessário:

- variáveis de ambiente;
- `.env`;
- GitHub Secrets;
- mecanismos equivalentes de gerenciamento seguro de segredos.

O `.gitignore` atualmente protege:

- `.env`;
- `.env.*`.

Antes de criar `.env.example`, revisar o `.gitignore`, pois a regra `.env.*` também pode ignorar esse arquivo.

Se `.env.example` for necessário, permitir explicitamente seu versionamento sem inserir valores secretos.

Nunca inserir uma chave real apenas para facilitar testes.

---

# Idioma e experiência do usuário

A experiência destinada ao usuário deve utilizar Português do Brasil.

Usar pt-BR em:

- interface;
- menus;
- botões;
- mensagens visíveis;
- README;
- documentação de uso;
- dashboard;
- estados apresentados ao usuário.

Identificadores internos de código podem permanecer em inglês.

Exemplos de apresentação ao usuário:

`PENDING_HUMAN_APPROVAL`
→ `Aguardando sua aprovação`

`READY_TO_APPLY`
→ `Pronta para candidatura`

Não é necessário traduzir enums internos apenas para modificar sua apresentação na interface.

---

# Qualidade do código

O código deve, quando aplicável:

- utilizar type hints;
- possuir funções pequenas e compreensíveis;
- utilizar docstrings quando agregarem valor;
- evitar duplicação;
- respeitar separação de responsabilidades;
- preservar os schemas existentes;
- possuir tratamento adequado de erros;
- possuir testes para comportamentos relevantes;
- manter regras de negócio fora dos endpoints sempre que possível.

Não realizar grandes refatorações junto com uma funcionalidade pequena sem necessidade técnica.

Não substituir componentes funcionais apenas por preferência de estilo.

---

# Regra para refatoração

Quando uma refatoração maior parecer necessária:

1. identificar claramente o problema;
2. explicar o benefício esperado;
3. propor a mudança;
4. avaliar impactos;
5. separar a refatoração da nova funcionalidade sempre que possível.

Não apagar funcionalidades existentes silenciosamente.

Não alterar contratos centrais sem avaliar seus consumidores e testes.

---

# Como o Codex deve trabalhar

Antes de alterar código:

- ler este `AGENTS.md`;
- inspecionar os arquivos relevantes para a tarefa;
- revisar schemas e testes relacionados;
- compreender o fluxo existente antes de modificá-lo;
- preservar a arquitetura atual quando não houver motivo técnico para alterá-la;
- identificar dependências importantes entre agentes;
- verificar o estado do repositório quando o ambiente disponibilizar Git.

Não é obrigatório analisar todos os arquivos do repositório para uma alteração pequena e localizada.

Para mudanças amplas, ampliar a inspeção antes de implementar.

Durante a implementação:

- alterar somente o necessário;
- reutilizar componentes existentes;
- preservar tipagem;
- evitar duplicação;
- manter regras de negócio nas camadas apropriadas;
- preservar compatibilidade quando possível;
- não contornar o `ValidationGate`;
- não contornar aprovação humana;
- não inventar dados ausentes;
- não inserir segredos;
- não adicionar dependências desnecessárias.

Depois da implementação:

- adicionar ou atualizar testes;
- executar os testes relacionados;
- executar `python -m pytest -v`;
- corrigir regressões relacionadas à alteração;
- informar os arquivos modificados;
- explicar o comportamento implementado;
- informar quais testes foram executados;
- informar o resultado dos testes;
- apontar limitações que permanecerem.

---

# Execução de tarefas maiores pelo Codex

Para tarefas maiores:

1. ler o `AGENTS.md`;
2. inspecionar o estado atual relevante;
3. apresentar um plano curto;
4. identificar arquivos que provavelmente serão alterados;
5. implementar em etapas coerentes;
6. testar comportamentos importantes;
7. executar a suíte completa;
8. apresentar resumo das alterações.

Quando houver dúvida sobre uma regra de negócio crítica, não assumir silenciosamente.

Preservar a decisão existente ou apontar a dúvida antes de alterar o comportamento.

Não receber uma instrução genérica como “finalize todo o projeto” como autorização para reescrever indiscriminadamente a arquitetura.

---

# Critério de conclusão de uma tarefa

Uma tarefa somente deve ser considerada concluída quando:

- o comportamento solicitado estiver implementado;
- as regras do projeto estiverem preservadas;
- testes relevantes existirem;
- os testes relacionados passarem;
- a suíte completa estiver verde, salvo problema externo claramente identificado;
- nenhum segredo tiver sido inserido;
- as alterações forem compreensíveis;
- limitações restantes forem informadas;
- nenhuma funcionalidade crítica tiver sido removida silenciosamente.

---

# Aprendizado e revisão humana

Este projeto também possui objetivo de aprendizado.

Ao concluir tarefas relevantes, apresentar um resumo compreensível contendo:

- o que foi implementado;
- por que foi implementado;
- quais arquivos foram alterados;
- como o fluxo funciona;
- quais testes comprovam o comportamento;
- quais limitações permanecem;
- qual é o próximo passo recomendado.

O código gerado deve permanecer compreensível e revisável por uma pessoa.

Não esconder decisões arquiteturais importantes atrás da automação.

---

# Automação e controle humano

Automatizar principalmente tarefas:

- repetitivas;
- verificáveis;
- baseadas em regras;
- auditáveis.

Manter controle humano em decisões que envolvam:

- aprovação de candidatura;
- alteração de informações profissionais do candidato;
- mudança importante de estratégia;
- envio de comunicações externas;
- envio efetivo de candidatura;
- ações irreversíveis ou sensíveis.

Automação de candidatura deve signific automação assistida após validação e aprovação humana, e não candidatura indiscriminada.

---

# Prioridades atuais

## Prioridade 1

Concluir o pipeline central baseado em:

`JobApplicationObject`

e:

`application_id`

Começar pela aprovação e rejeição humana por ID.

## Prioridade 2

Concluir tracking, follow-up e métricas através da API central.

## Prioridade 3

Melhorar tratamento de erros e estados inválidos.

## Prioridade 4

Garantir atualização consistente de `updated_at`.

## Prioridade 5

Adicionar persistência PostgreSQL preservando o Repository Pattern.

## Prioridade 6

Consolidar a API operacional.

## Prioridade 7

Criar frontend mínimo utilizável em Português do Brasil.

## Prioridade 8

Integrar descoberta real de oportunidades através de fontes apropriadas.

## Prioridade 9

Adicionar IA de forma controlada e baseada em evidências.

## Prioridade 10

Evoluir automação assistida de candidatura, acompanhamento e otimização.

---

# Próximo ponto exato de implementação

No estado atual documentado, o pipeline central possui:

`create`
→ `get/list`
→ `qualify`
→ `personalize`
→ `prepare`

O próximo bloco de implementação deve começar por:

`approve/reject by application_id`

Depois:

`tracking`
→ `follow-up`
→ `metrics`

Antes de implementar, confirmar o estado real do código e dos testes, pois o repositório é a fonte técnica mais atual.

---

# Evolução planejada

A evolução esperada é aproximadamente:

`JobApplicationObject`
→ pipeline central completo
→ tratamento de erros
→ `updated_at`
→ PostgreSQL
→ API consolidada
→ frontend
→ descoberta real de vagas
→ IA controlada
→ automação assistida de candidatura
→ tracking/follow-up operacional
→ métricas e aprendizado
→ preparação para produção

Essa ordem pode ser ajustada quando houver justificativa técnica clara.

---

# Filosofia do projeto

A plataforma deve permanecer:

- automatizada;
- orientada por dados;
- auditável;
- testável;
- modular;
- interativa;
- dinâmica;
- profissional.

Automação não significa ausência de controle humano.

A plataforma deve ajudar o candidato a tomar melhores decisões, reduzir trabalho repetitivo, aumentar a qualidade das candidaturas e aprender com resultados reais.

Veracidade, rastreabilidade e controle humano possuem prioridade sobre volume de candidaturas.










