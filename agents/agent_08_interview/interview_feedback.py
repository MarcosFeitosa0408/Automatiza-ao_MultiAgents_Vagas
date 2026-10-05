"""Feedback formativo por indícios textuais; não corrige conteúdo técnico."""
import re
import unicodedata

from pydantic import Field, field_validator
from core.schemas.job import StrictModel
from agents.agent_08_interview.interview_agent import InterviewQuestion


class FeedbackRequest(StrictModel):
    question_id: str = Field(min_length=1, max_length=80)
    answer: str = Field(min_length=1, max_length=6000)

    @field_validator('answer')
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError('Escreva sua resposta antes de avaliar.')
        return value.strip()


class CriterionFeedback(StrictModel):
    name: str
    score: int = Field(ge=0, le=25)
    maximum: int = 25
    guidance: str


class InterviewFeedback(StrictModel):
    question_id: str
    score: int = Field(ge=0, le=100)
    criteria: list[CriterionFeedback]
    limitation: str


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold())
                   if unicodedata.category(c) != 'Mn')


# Each group contributes at most once. Repeating words never adds points.
RUBRICS = {
    'presentation': [
        ('Trajetória', ['formacao', 'curso', 'estudo', 'experiencia', 'projeto'],
         'Apresente sua formação ou prática real, com um exemplo.'),
        ('Contribuição', ['criei', 'analisei', 'desenvolvi', 'organizei', 'construi', 'aprendi'],
         'Explique o que você fez ou aprendeu pessoalmente.'),
        ('Interesse na vaga', ['interesse', 'vaga', 'quero', 'objetivo', 'empresa'],
         'Explique por que se interessa pela vaga e como pode contribuir.'),
    ],
    'technical': [
        ('Explicação do conceito', ['serve', 'permite', 'consiste', 'utilizado', 'utilizada', 'significa'],
         'Explique o conceito com suas palavras e diga para que serve.'),
        ('Prática ou estudo', ['projeto', 'estudo', 'curso', 'trabalho', 'exemplo', 'aprendendo'],
         'Diferencie experiência, projeto e estudo; reconheça o que ainda precisa aprender.'),
        ('Aplicação e validação', ['usei', 'utilizei', 'validei', 'testei', 'comparei', 'consultar', 'verificar'],
         'Descreva uma aplicação concreta e como verificaria o resultado.'),
    ],
    'problem-solving': [
        ('Contexto', ['problema', 'desafio', 'situacao', 'precisava', 'objetivo'],
         'Descreva o problema e sua responsabilidade naquele contexto.'),
        ('Ação pessoal', ['criei', 'analisei', 'organizei', 'resolvi', 'comparei', 'identifiquei'],
         'Explique sua ação pessoal: o que fez e por que escolheu esse caminho.'),
        ('Resultado e aprendizado', ['resultado', 'aprendi', 'melhorou', 'reduziu', 'consegui', 'validacao'],
         'Conte o resultado observado ou aprendizado. Use números somente com evidências.'),
    ],
    'practical-case': [
        ('Problema e recursos', ['problema', 'objetivo', 'dados', 'recursos', 'cenario'],
         'Defina o objetivo e os dados ou recursos do exercício.'),
        ('Plano de execução', ['primeiro', 'depois', 'etapa', 'executaria', 'criaria', 'analisaria'],
         'Descreva as etapas e as decisões para executar o exercício.'),
        ('Validação', ['validaria', 'testaria', 'compararia', 'verificaria', 'validacao', 'teste'],
         'Explique como verificaria se a solução funciona. Identifique o exemplo como simulação.'),
    ],
    'ask-recruiter': [
        ('Responsabilidades', ['responsabilidades', 'desafios', 'equipe', 'rotina'],
         'Pergunte sobre responsabilidades e desafios da equipe.'),
        ('Condições e seleção', ['modalidade', 'remoto', 'localizacao', 'etapas', 'selecao'],
         'Pergunte sobre modalidade, localização ou etapas da seleção.'),
        ('Expectativas', ['desempenho', 'sucesso', 'metas', 'expectativas', 'avaliacao'],
         'Pergunte como o desempenho será acompanhado e quais são as expectativas.'),
    ],
}


def evaluate_answer(question: InterviewQuestion, answer: str) -> InterviewFeedback:
    """Count explicit textual cues, without storing or echoing the answer."""
    text = normalized(answer)
    words = re.findall(r'\b\w+\b', text)
    # Vocabulary diversity prevents a repeated keyword list earning a full score.
    enough_detail = len(words) >= 35 and len(set(words)) >= 20
    detail_score = 25 if enough_detail else 12 if len(words) >= 15 else 0
    criteria = [CriterionFeedback(
        name='Desenvolvimento da resposta', score=detail_score,
        guidance=('Há extensão e variedade de palavras para desenvolver a resposta. Revise clareza e concisão.'
                  if enough_detail else 'Desenvolva uma resposta com contexto e explicações; uma lista de palavras não basta.'),
    )]
    key = 'technical' if question.question_id.startswith('technical-') else question.question_id
    for name, cues, suggestion in RUBRICS[key]:
        found = any(re.search(r'\b' + re.escape(cue) + r'\b', text) for cue in cues)
        score = (25 if enough_detail else 12 if len(words) >= 15 else 0) if found else 0
        criteria.append(CriterionFeedback(
            name=name, score=score,
            guidance=(f'Indício textual identificado em “{name}”. Confira se explicou esse ponto com clareza. '
                      if found else 'Nenhum indício textual identificado. ') + suggestion,
        ))
    return InterviewFeedback(
        question_id=question.question_id, score=sum(item.score for item in criteria),
        criteria=criteria,
        limitation='Nota de estrutura por regras de palavras e extensão. Pode deixar de reconhecer boas respostas ou pontuar respostas inadequadas. Não verifica correção técnica, veracidade nem chance de contratação.',
    )
