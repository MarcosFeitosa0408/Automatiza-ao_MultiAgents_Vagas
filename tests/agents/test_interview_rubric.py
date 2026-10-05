import pytest
from pydantic import ValidationError
from agents.agent_08_interview.interview_agent import InterviewQuestion
from agents.agent_08_interview.interview_feedback import FeedbackRequest, evaluate_answer


def question(key='problem-solving'):
    return InterviewQuestion(question_id=key, category='Teste', question='Teste')


def test_short_keyword_list_and_repetition_do_not_earn_points():
    for answer in ('problema criei resultado', 'problema criei resultado ' * 40):
        result = evaluate_answer(question(), answer)
        assert result.score == 0 if len(answer.split()) < 15 else result.score <= 48


def test_feedback_is_bounded_transparent_and_does_not_echo_answer():
    answer = ('O problema era organizar dados de um projeto de estudo. Eu analisei as fontes, '
              'criei uma consulta e comparei os valores. O resultado foi identificar registros duplicados; '
              'aprendi a verificar a consistência antes de apresentar o relatório para a equipe.')
    result = evaluate_answer(question(), answer)
    assert result.score == 100
    assert sum(c.score for c in result.criteria) == result.score
    assert 'Não verifica' in result.limitation
    assert answer not in result.model_dump_json()
    assert evaluate_answer(question(), answer) == result


def test_rubric_depends_on_question():
    answer = 'Quais são as responsabilidades da equipe e as etapas da seleção? Como acompanham o desempenho e as expectativas para os primeiros meses de trabalho nessa função na empresa e neste projeto?'
    result = evaluate_answer(question('ask-recruiter'), answer)
    assert result.criteria[1].name == 'Responsabilidades'
    assert all(c.score > 0 for c in result.criteria[1:])


@pytest.mark.parametrize('answer', ['', '   ', 'a' * 6001])
def test_invalid_answers(answer):
    with pytest.raises(ValidationError):
        FeedbackRequest(question_id='presentation', answer=answer)
