import { useId, useState } from "react";

export default function PlatformGuide() {
  const [open, setOpen] = useState(false);
  const contentId = useId();

  return (
    <section className="dashboard-panel" aria-label="Ajuda para usar a plataforma">
      <button className="secondary-button" type="button"
        aria-expanded={open} aria-controls={contentId}
        onClick={() => setOpen((current) => !current)}>
        Como usar a plataforma <span aria-hidden="true">💡</span>
      </button>
      <div id={contentId} hidden={!open}>
        <h2>Seu passo a passo <span aria-hidden="true">🚀</span></h2>
        <p>Comece pelo perfil e siga as etapas abaixo. Clique novamente em “Como usar a plataforma” para fechar este guia.</p>
        <ol>
          <li><strong>Preencha Meu perfil.</strong> Cadastre seus dados, formação, experiências, projetos, habilidades e links. Clique em Salvar meu perfil e confira a confirmação. Use somente informações verdadeiras.</li>
          <li><strong>Abra Buscar oportunidades.</strong> Informe cargo, país e localização nos filtros disponíveis e faça a busca. Clique em Selecionar oportunidade na vaga desejada.</li>
          <li><strong>Revise Nova candidatura.</strong> Confira cargo, empresa, link, descrição e requisitos antes de clicar em Cadastrar oportunidade. Isso salva a vaga na sua conta; não envia uma candidatura à empresa.</li>
          <li><strong>Confira Candidaturas.</strong> Esta tela reúne suas vagas salvas. Para completar uma vaga, abra Editar descrição e requisitos, copie as informações do anúncio completo e clique em Salvar requisitos da vaga. Currículo e entrevista precisam desses requisitos.</li>
          <li><strong>Prepare seu currículo.</strong> Na vaga salva, clique em Gerar prévia do currículo. Revise o conteúdo. Se precisar montar um documento, copie o texto revisado para seu editor de preferência. O envio à empresa é feito por você no site indicado pela vaga.</li>
          <li><strong>Treine para a entrevista.</strong> Clique em Preparar entrevista, leia as orientações e escreva sua resposta. Ao clicar em Avaliar resposta, você recebe nota de estrutura e sugestões. Edite e avalie novamente para praticar; a nota não verifica correção técnica nem prevê aprovação.</li>
          <li><strong>Organize sua conta.</strong> Use Excluir oportunidade para remover uma vaga que não deseja guardar. Confira a confirmação antes de excluir. Ao terminar, clique em Sair da conta.</li>
        </ol>
        <p><span aria-hidden="true">💙</span> As respostas do treino são perdidas ao sair ou atualizar a página. Seu perfil e suas vagas permanecem na sua conta quando salvos.</p>
      </div>
    </section>
  );
}
