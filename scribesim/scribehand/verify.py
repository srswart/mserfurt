"""HTR-in-the-loop rejection sampling (TD-018 §2.7).

Every generated word is read back by an HTR scorer; words whose CER exceeds
the threshold are regenerated with a fresh retry seed. Words that exhaust
retries are marked unverified — composition refuses them by default.
"""

from __future__ import annotations

from dataclasses import replace

from scribesim.scribehand.generate import WordGenerator
from scribesim.scribehand.htr import cer
from scribesim.scribehand.seeds import word_seed
from scribesim.scribehand.types import WordRequest, WordResult


def verify_words(
    generator: WordGenerator,
    scorer,
    requests: list[WordRequest],
    cer_threshold: float = 0.05,
    max_retries: int = 3,
    base_seed: int | None = None,
) -> list[WordResult]:
    """Generate + verify each request; regenerate failures with retry seeds.

    Retry seeds derive from the word position when it is known (folio/line/
    word indices), falling back to ``seed + retry`` otherwise.
    """
    results = generator.generate(requests)
    pending = list(range(len(requests)))
    retry = 0

    while True:
        images = [results[i].strip.ink for i in pending]
        expected = [requests[i].text for i in pending]
        readings = scorer.read(images, expected=expected)

        failed: list[int] = []
        for i, reading in zip(pending, readings):
            error = cer(requests[i].text, reading)
            results[i].provenance.update({
                "htr_text": reading,
                "htr_cer": error,
                "retries": retry,
                "verified": error <= cer_threshold,
            })
            if error > cer_threshold:
                failed.append(i)

        if not failed or retry >= max_retries:
            return results

        retry += 1
        retry_requests: list[WordRequest] = []
        for i in failed:
            req = requests[i]
            if req.folio_id:
                seed = word_seed(
                    base_seed if base_seed is not None else req.seed,
                    req.folio_id, req.line_index, req.word_index, retry=retry,
                )
            else:
                seed = req.seed + retry
            retry_requests.append(replace(req, seed=seed))

        regenerated = generator.generate(retry_requests)
        for i, req, res in zip(failed, retry_requests, regenerated):
            requests[i] = req
            results[i] = res
        pending = failed
