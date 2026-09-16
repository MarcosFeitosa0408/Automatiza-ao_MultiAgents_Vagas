import json
from pathlib import Path

from core.schemas.candidate import MasterProfile


class MemoryAgent:
    """Carrega e valida o perfil mestre do candidato."""

    def __init__(
        self,
        profile_path: str = "data/master_profile/MASTER_PROFILE.json",
    ) -> None:
        self.profile_path = Path(profile_path)
        self._profile: MasterProfile | None = None

    def load_profile(self) -> MasterProfile:
        """Carrega o MASTER_PROFILE.json e valida com Pydantic."""

        if not self.profile_path.exists():
            raise FileNotFoundError(
                f"MASTER_PROFILE não encontrado em: {self.profile_path}"
            )

        with self.profile_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)

        self._profile = MasterProfile.model_validate(raw_data)
        return self._profile

    def get_profile(self) -> MasterProfile:
        """Retorna o perfil validado, carregando-o quando necessário."""

        if self._profile is None:
            return self.load_profile()

        return self._profile

    def get_candidate_name(self) -> str:
        """Retorna o nome do candidato."""

        return self.get_profile().candidate.name

    def get_primary_roles(self) -> list[str]:
        """Retorna os cargos-alvo principais."""

        return self.get_profile().candidate.career_target.primary_roles

    def get_core_skills(self) -> list[str]:
        """Retorna as competências principais."""

        return self.get_profile().skills.core
