from test_interview_plan import interview_context


def test_feedback_uses_existing_question_and_preserves_data(interview_context):
    client, profile, application = interview_context
    before = (profile.model_dump_json(), application.model_dump_json())
    response = client.post('/job-applications/interview-test/interview-feedback', json={
        'question_id': 'technical-1', 'answer': 'Estou aprendendo SQL em um projeto de estudo.'})
    assert response.status_code == 200
    assert response.json()['question_id'] == 'technical-1'
    assert before == (profile.model_dump_json(), application.model_dump_json())
    assert client.post('/job-applications/interview-test/interview-feedback', json={
        'question_id': 'technical-9', 'answer': 'Resposta'}).status_code == 422
    assert client.post('/job-applications/missing/interview-feedback', json={
        'question_id': 'presentation', 'answer': 'Resposta'}).status_code == 404
