from abc import ABC, abstractmethod
from collections.abc import Iterable


class BaseJobSource(ABC):
    """Contrato base para fontes externas de vagas."""

    @abstractmethod
    def fetch_jobs(self) -> Iterable[dict]:
        """Coleta vagas brutas da fonte externa."""
        raise NotImplementedError
