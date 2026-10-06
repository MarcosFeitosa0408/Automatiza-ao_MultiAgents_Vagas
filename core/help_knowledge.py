"""Base revisada de ajuda. Não consulta dados privados nem serviços externos."""
import re
import unicodedata


def normalize(text):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', unicodedata.normalize('NFKD', text.casefold()).encode('ascii', 'ignore').decode())).strip()


ARTICLES = [
    ('perfil', 'Como cadastro ou altero meu perfil?', ('perfil','formacao','experiencia','habilidades','dados pessoais'), 'Abra Meu perfil, preencha ou edite os campos e clique em Salvar meu perfil. Confira a confirmação. Use somente informações verdadeiras. Seus dados salvos pertencem à sua conta.'),
    ('busca', 'Como encontro vagas?', ('buscar vagas','encontrar vagas','buscar oportunidades','adzuna','codigo do pais'), 'Abra Buscar oportunidades. Informe cargo, código do país (br para Brasil) e localização opcional. Clique em Buscar oportunidades e depois em Selecionar oportunidade. A fonte conectada é a Adzuna; a cobertura varia por país. Confira o anúncio original.'),
    ('salvar', 'Salvar uma vaga envia candidatura à empresa?', ('cadastrar oportunidade','salvar vaga','enviar candidatura','candidaturas'), 'Candidaturas reúne as oportunidades salvas pelo candidato. Selecionar e cadastrar uma oportunidade salva a vaga na sua conta; não envia seu currículo à empresa. Você faz o envio no anúncio ou canal indicado pela empresa.'),
    ('requisitos', 'Como completo a descrição e os requisitos?', ('requisitos','descricao da vaga','curriculo nao gera','entrevista nao abre'), 'Em Candidaturas, abra Editar descrição e requisitos. Copie as informações do anúncio completo e clique em Salvar requisitos da vaga. Currículo e roteiro usam os requisitos e os dados do seu perfil. Se aparecer erro, confira a mensagem apresentada.'),
    ('pdf', 'Como salvo o currículo em PDF?', ('pdf','imprimir','baixar curriculo'), 'Na vaga salva, clique em Gerar prévia do currículo e revise. Clique em Salvar currículo em PDF. Na impressão, escolha Salvar como PDF, papel A4 e desative cabeçalhos e rodapés. Salve no computador ou celular e envie à empresa por conta própria.'),
    ('traducao', 'Como traduzo meu currículo?', ('traduzir','traducao','espanhol','curriculo em ingles','idioma do curriculo'), 'Gere a prévia e escolha Inglês ou Espanhol em Idioma do currículo. Clique em Traduzir currículo: os textos profissionais são enviados ao DeepL. Revise e salve o PDF no idioma da prévia. Selecionar Português do Brasil restaura o original. A interface continua em português.'),
    ('entrevista', 'Como funciona a nota da entrevista?', ('nota','pontuacao','treinamento','treino','entrevista','avaliar resposta'), 'Na vaga salva, clique em Preparar entrevista. Leia as orientações, escreva sua resposta e clique em Avaliar resposta. A nota avalia indícios de estrutura, não a correção técnica nem a chance de contratação. As respostas digitadas são perdidas ao sair ou atualizar a página.'),
    ('excluir', 'Como excluo uma vaga?', ('excluir vaga','excluir oportunidade','duplicada','duplicadas','apagar vaga'), 'Em Candidaturas, escolha Excluir oportunidade na cópia que deseja remover. Confira a vaga e confirme a exclusão. Cancelar mantém a vaga. Para completar uma vaga existente, edite seus requisitos em vez de cadastrar outra cópia.'),
    ('senha', 'Como recupero ou confiro minha senha?', ('senha','password','olho','esqueci'), 'Na entrada, use Esqueci minha senha para solicitar um link por e-mail. Confira também o spam. Abra o link e confirme a nova senha de 8 a 128 caracteres. O olho mostra ou oculta o campo; Limpar apaga o texto digitado. Recuperar a senha não libera uma conta bloqueada ou pendente.'),
    ('acesso', 'Por que meu cadastro aguarda autorização?', ('autorizacao','autorizar','bloqueado','bloqueada','cadastro','criar conta'), 'Novos cadastros aguardam autorização do administrador. Não compartilhe sua senha. Cada conta guarda seu próprio perfil e suas vagas. Sair da conta encerra o acesso; ao recarregar ou fechar a aba, será necessário entrar novamente.'),
    ('celular', 'Como abro a plataforma no celular?', ('celular','instalar','play store','playstore','link'), 'Abra https://multiagents-vagas.onrender.com/ no navegador do celular. Use a opção do navegador para adicionar ou instalar na tela inicial, quando disponível. A plataforma ainda não foi publicada na Play Store.'),
    ('ajuda', 'Como funcionam as dúvidas para melhoria?', ('limite','duvidas','robo','ajuda'), 'Sou um assistente com respostas revisadas sobre esta plataforma. Não executo ações e não consulto seu perfil. Se eu não souber, você pode encaminhar a dúvida ao administrador: até 3 encaminhamentos por candidato por semana, renovados na segunda-feira às 00h no horário de São Paulo. Respostas conhecidas e o guia atual continuam disponíveis.'),
]


def answer(question):
    text = normalize(question)
    # Um assunto curto/exato ou pergunta diretamente relacionada; não tratar
    # texto longo ou várias perguntas como se soubéssemos responder tudo.
    if len(text) > 220 or '?' in question[:-1] or any(term in text for term in ('minha senha e ', 'qual e a minha senha', 'ignore instrucoes', 'receita de ', 'conte uma piada')):
        return None
    exact = [item for item in ARTICLES if text == normalize(item[1])]
    if exact:
        return exact[0][3]
    matches = [item for item in ARTICLES if any(re.search(r'\b'+re.escape(alias)+r'\b', text) for alias in item[2])]
    return matches[0][3] if len(matches) == 1 else None


def suggestions():
    return [item[1] for item in ARTICLES]
