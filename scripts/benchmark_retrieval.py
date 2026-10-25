"""Benchmark script comparing sequential retrieval against parallel query fan-out retrieval."""

from __future__ import annotations

import statistics
import time
from typing import Any

from healthcare_agents.planning.fanout import build_deterministic_fanout
from healthcare_agents.retrieval.fixtures import (
    FixtureEvidenceRetriever,
    FixturePatientEducationRetriever,
    FixtureProviderRetriever,
    FixtureQualityRetriever,
)
from healthcare_agents.retrieval.parallel_retriever import execute_parallel_retrieval
from healthcare_agents.workflows.state import SearchPlan


class SimulatedDelayedRetriever:
    """Wrapper that introduces realistic I/O network latency to deterministic fixtures."""

    def __init__(self, target: Any, delay_seconds: float) -> None:
        self.target = target
        self.delay_seconds = delay_seconds

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self.target, name)
        if callable(attr):

            def delayed_wrapper(*args: Any, **kwargs: Any) -> Any:
                time.sleep(self.delay_seconds)
                return attr(*args, **kwargs)

            return delayed_wrapper
        return attr


def run_sequential_retrieval(
    fanout: Any,
    prov_retriever: Any,
    ev_retriever: Any,
    edu_retriever: Any,
    q_retriever: Any,
) -> dict[str, Any]:
    """Execute retrieval queries sequentially."""
    t0 = time.perf_counter()
    candidates = []
    clinical = []
    education = []
    cms = []

    for q in fanout.queries:
        if q.source == "NPPES":
            candidates.extend(
                prov_retriever.search_providers(
                    specialty=q.search_params.get("specialty"),
                    city=q.search_params.get("city"),
                    state=q.search_params.get("state"),
                    limit=q.search_params.get("limit", 5),
                )
            )
        elif q.source == "PubMed":
            clinical.extend(
                ev_retriever.search_evidence(
                    topic=q.search_params.get("topic") or q.query_text,
                    limit=q.search_params.get("limit", 5),
                )
            )
        elif q.source == "MedlinePlus":
            education.extend(
                edu_retriever.search_topics(
                    keyword=q.search_params.get("keyword") or q.query_text,
                    limit=q.search_params.get("limit", 3),
                )
            )
        elif q.source == "CMS":
            for p in candidates:
                if p.npi and len(p.npi) == 10:
                    cms.extend(q_retriever.get_provider_quality(npi=p.npi))

    t1 = time.perf_counter()
    return {
        "duration_ms": (t1 - t0) * 1000.0,
        "provider_count": len(candidates),
        "clinical_count": len(clinical),
        "education_count": len(education),
        "cms_count": len(cms),
    }


def run_benchmarks(iterations: int = 5, simulated_io_delay: float = 0.1) -> dict[str, Any]:
    """Run controlled benchmark iterations comparing sequential vs parallel retrieval."""
    search_plan: SearchPlan = {
        "specialty": "Pediatric Dentistry",
        "city": "Houston",
        "state": "TX",
        "evidence_topics": ["pediatric dental anxiety"],
        "intent_description": "Pediatric dentists Houston and dental anxiety",
    }
    query = "Find pediatric dentists in Houston and research pediatric dental anxiety"

    seq_times: list[float] = []
    par_times: list[float] = []

    for i in range(iterations):
        fanout = build_deterministic_fanout(
            request_id=f"bench-{i}",
            original_query=query,
            search_plan=search_plan,
        )

        base_prov = FixtureProviderRetriever()
        base_ev = FixtureEvidenceRetriever()
        base_edu = FixturePatientEducationRetriever()
        base_q = FixtureQualityRetriever()

        prov = SimulatedDelayedRetriever(base_prov, simulated_io_delay)
        ev = SimulatedDelayedRetriever(base_ev, simulated_io_delay)
        edu = SimulatedDelayedRetriever(base_edu, simulated_io_delay)
        q = SimulatedDelayedRetriever(base_q, simulated_io_delay)

        # 1. Sequential run
        res_seq = run_sequential_retrieval(fanout, prov, ev, edu, q)
        seq_times.append(res_seq["duration_ms"])

        # 2. Parallel run
        t0 = time.perf_counter()
        execute_parallel_retrieval(
            fanout_plan=fanout,
            provider_retriever=prov,  # type: ignore[arg-type]
            evidence_retriever=ev,  # type: ignore[arg-type]
            patient_education_retriever=edu,  # type: ignore[arg-type]
            quality_retriever=q,  # type: ignore[arg-type]
            max_workers=4,
        )
        t1 = time.perf_counter()
        par_times.append((t1 - t0) * 1000.0)

    mean_seq = statistics.mean(seq_times)
    mean_par = statistics.mean(par_times)
    reduction = ((mean_seq - mean_par) / mean_seq) * 100.0

    return {
        "iterations": iterations,
        "simulated_io_delay_sec": simulated_io_delay,
        "mean_sequential_ms": round(mean_seq, 2),
        "mean_parallel_ms": round(mean_par, 2),
        "latency_reduction_pct": round(reduction, 2),
        "sequential_runs": [round(x, 2) for x in seq_times],
        "parallel_runs": [round(x, 2) for x in par_times],
    }


if __name__ == "__main__":
    results = run_benchmarks(iterations=5, simulated_io_delay=0.1)
    print("=== M7 RETRIEVAL PERFORMANCE BENCHMARK ===")
    print(f"Iterations: {results['iterations']}")
    print(f"Simulated I/O Delay per Source: {results['simulated_io_delay_sec']}s")
    print(f"Mean Sequential Duration: {results['mean_sequential_ms']} ms")
    print(f"Mean Parallel Duration:   {results['mean_parallel_ms']} ms")
    print(f"Latency Reduction:        {results['latency_reduction_pct']}% (Target: >=25%)")
