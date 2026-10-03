import json
import os
import tempfile
from pathlib import Path

from core.schemas.candidate import MasterProfile


class MemoryAgent:
    """Carrega, valida e salva o perfil mestre do candidato."""

    def __init__(
        self,
        profile_path: str = "data/master_profile/MASTER_PROFILE.json",
    ) -> None:
        self.profile_path = Path(profile_path)
        self._profile: MasterProfile | None = None

    def load_profile(self) -> MasterProfile:
        """Lê o perfil salvo e valida sua estrutura com Pydantic."""

        if not self.profile_path.exists():
            raise FileNotFoundError(
                f"MASTER_PROFILE não encontrado em: {self.profile_path}"
            )

        with self.profile_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)

        self._profile = MasterProfile.model_validate(raw_data)
        return self._profile

    def get_profile(self) -> MasterProfile:
        """Lê a versão atual para evitar o uso de dados desatualizados."""

        return self.load_profile()

    def save_profile(self, profile: MasterProfile) -> MasterProfile:
        """Valida e substitui o arquivo somente após concluir a escrita."""

        validated_profile = MasterProfile.model_validate(
            profile.model_dump(mode="json")
        )

        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.profile_path.parent,
                prefix=f".{self.profile_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = Path(file.name)

                json.dump(
                    validated_profile.model_dump(mode="json"),
                    file,
                    ensure_ascii=False,
                    indent=2,
                    allow_nan=False,
                )

                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

            os.replace(temporary_path, self.profile_path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

        self._profile = validated_profile
        return validated_profile

    def get_candidate_name(self) -> str:
        """Retorna o nome do candidato."""

        return self.get_profile().candidate.name

    def get_primary_roles(self) -> list[str]:
        """Retorna os cargos-alvo principais."""

        return self.get_profile().candidate.career_target.primary_roles

    def get_core_skills(self) -> list[str]:
        """Retorna as competências principais."""

        return self.get_profile().skills.core