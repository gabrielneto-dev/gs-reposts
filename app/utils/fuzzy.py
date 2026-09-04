import difflib
import re


def similaridade_nome(termo: str, alvo: str) -> float:
    """Similaridade percentual (0-100) entre `termo` e `alvo`.

    Substring exata (case-insensitive) vale 100. Caso contrário, compara `termo` contra cada
    palavra de `alvo` (e contra `alvo` inteiro) e usa a melhor razão de similaridade, o que
    tolera pequenas diferenças de digitação sem gerar falsos positivos vindos de trechos
    aleatórios no meio de palavras compostas (ex: "astra" dentro de "cadastrais")."""

    termo = termo.lower().strip()
    alvo = alvo.lower().strip()
    if not termo or not alvo:
        return 0.0
    if termo in alvo:
        return 100.0

    candidatos = [alvo, *re.findall(r"\w+", alvo)]
    melhor = max(difflib.SequenceMatcher(None, termo, c).ratio() for c in candidatos)
    return round(melhor * 100, 2)
