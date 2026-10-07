from pathlib import Path
from core.resume_preview import build_resume_preview
from core.schemas.candidate import Education, MasterProfile
from core.schemas.personalization import PersonalizationResult


def test_review_identifies_missing_information_without_changing_profile():
    profile = MasterProfile.model_validate_json(Path('tests/fixtures/profile.json').read_text())
    profile.candidate.name = ' '
    profile.candidate.phone = 'NAO_IDENTIFICADO'
    profile.candidate.location.city = ''
    profile.education = [Education(degree='Curso real', institution='', status='Concluído')]
    before = profile.model_dump()
    personalization = PersonalizationResult(job_id='review', professional_title=' ', professional_summary=' ')
    result = build_resume_preview('review', 'Analista', 'Empresa', profile, personalization)
    warnings = ' '.join(result.warnings)
    for part in ('nome', 'telefone', 'cidade', 'instituição', 'título profissional', 'resumo', 'Nenhuma experiência'):
        assert part in warnings
    assert profile.model_dump() == before
    assert result.experience == []
    assert result.projects == []
    assert result.skills == []
    assert result.phone == 'NAO_IDENTIFICADO'


def test_review_does_not_demand_invented_experience_or_full_address():
    profile = MasterProfile.model_validate_json(Path('tests/fixtures/profile.json').read_text())
    profile.education = []
    result = build_resume_preview('review', 'Analista', 'Empresa', profile,
        PersonalizationResult(job_id='review', professional_title='Analista', professional_summary='Resumo verdadeiro'))
    warnings = ' '.join(result.warnings)
    assert 'apenas se fizer parte da sua trajetória' in warnings
    assert 'não inclua experiências que não possui' in warnings
    assert 'Preencha seu nome' not in warnings
    assert 'Confira cidade e país' not in warnings
