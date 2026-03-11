#!/usr/bin/env python3
"""Extract claims from research paper abstracts using Claude CLI.

Reads all papers from research/domains/*.json, fetches abstracts from
PubMed or Semantic Scholar, then calls `claude -p` to extract structured
claims. Results are written to research/claims/{paper_id}.json and progress
is tracked in research/claims_manifest.json.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

RESEARCH_DIR = Path(__file__).parent
DOMAINS_DIR = RESEARCH_DIR / "domains"
CLAIMS_DIR = RESEARCH_DIR / "claims"
MANIFEST_PATH = RESEARCH_DIR / "claims_manifest.json"

MAX_PAPERS = 10
SEMANTIC_SCHOLAR_DELAY = 1.5  # seconds between requests (rate limit)


def load_all_papers() -> list[dict]:
    """Load all papers from domain JSON files, attaching domain_id to each."""
    papers = []
    for domain_file in sorted(DOMAINS_DIR.glob("*.json")):
        with open(domain_file) as f:
            domain = json.load(f)
        domain_id = domain["domain_id"]
        for paper in domain.get("papers", []):
            paper_with_domain = {**paper, "domain_id": domain_id}
            papers.append(paper_with_domain)
    return papers


def load_manifest() -> dict:
    """Load or create the claims manifest."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    manifest = {}
    save_manifest(manifest)
    return manifest


def save_manifest(manifest: dict) -> None:
    """Write manifest to disk."""
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)


def fetch_abstract_pubmed(pubmed_id: str) -> str | None:
    """Fetch abstract text from PubMed efetch XML API."""
    url = (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&id={pubmed_id}&retmode=xml"
    )
    try:
        req = Request(url, headers={"User-Agent": "PaceAI/1.0"})
        with urlopen(req, timeout=15) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        # Abstract can be in multiple <AbstractText> elements
        abstract_parts = []
        for elem in root.iter("AbstractText"):
            label = elem.get("Label", "")
            text = "".join(elem.itertext()).strip()
            if text:
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
        if abstract_parts:
            return " ".join(abstract_parts)
        return None
    except (HTTPError, URLError, ET.ParseError) as e:
        print(f"    PubMed fetch failed: {e}")
        return None


def fetch_abstract_semantic_scholar(doi: str) -> str | None:
    """Fetch abstract from Semantic Scholar API."""
    url = f"https://api.semanticscholar.org/graph/v1/paper/{doi}?fields=abstract"
    try:
        req = Request(url, headers={"User-Agent": "PaceAI/1.0"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        abstract = data.get("abstract")
        if abstract and abstract.strip():
            return abstract.strip()
        return None
    except (HTTPError, URLError, json.JSONDecodeError) as e:
        print(f"    Semantic Scholar fetch failed: {e}")
        return None


def fetch_abstract(paper: dict) -> str | None:
    """Fetch abstract using priority: PubMed > Semantic Scholar."""
    pubmed_id = paper.get("pubmed_id")
    doi = paper.get("doi")

    if pubmed_id:
        print(f"    Trying PubMed (PMID {pubmed_id})...")
        abstract = fetch_abstract_pubmed(pubmed_id)
        if abstract:
            return abstract
        print("    PubMed returned no abstract.")

    if doi:
        print(f"    Trying Semantic Scholar (DOI {doi})...")
        time.sleep(SEMANTIC_SCHOLAR_DELAY)
        abstract = fetch_abstract_semantic_scholar(doi)
        if abstract:
            return abstract
        print("    Semantic Scholar returned no abstract.")

    return None


def build_claude_prompt(abstract: str, paper: dict) -> str:
    """Build the prompt for Claude CLI claim extraction."""
    metadata = {
        "title": paper.get("title", ""),
        "authors": paper.get("authors", []),
        "year": paper.get("year", ""),
        "journal": paper.get("journal", ""),
        "study_type": paper.get("study_type", ""),
        "population": paper.get("population", []),
        "domain_id": paper.get("domain_id", ""),
    }

    return f"""You are extracting structured claims from a research paper abstract for a running coaching knowledge base.

Paper metadata:
{json.dumps(metadata, indent=2)}

Abstract:
{abstract}

Extract all factual, actionable claims from this abstract. Return ONLY a valid JSON array with no other text, no markdown fencing, no explanation.

Each claim object must have exactly these fields:
- "text": string — the claim stated clearly and specifically (one sentence)
- "specific_value": string or null — any specific number, percentage, threshold, or dose mentioned (e.g. "0.8-1.3 ACWR", "208 - 0.7 × age", "2-3% body mass loss"). null if the claim is qualitative
- "category": "{paper.get('domain_id', '')}" — use this exact string for all claims from this paper
- "population": string — who the finding applies to (e.g. "elite athletes", "recreational runners", "trained endurance athletes", "general population")
- "confidence": number 0.0-1.0 — how strong the evidence is (1.0 = large RCT/meta-analysis with clear result, 0.8 = solid study, 0.6 = moderate evidence, 0.4 = preliminary/pilot, 0.2 = case study/expert opinion)
- "school_of_thought": string — the training philosophy or scientific school this aligns with (e.g. "Daniels", "Lydiard", "Seiler polarized", "Gabbett load management", "IOC consensus", "general sports science", "sports nutrition consensus", "injury prevention"). Use "general sports science" if no specific school applies.

Guidelines:
- Extract 3-8 claims per abstract depending on density
- Each claim should be independently useful — a coach should be able to act on it
- Be specific: include numbers, effect sizes, and thresholds when available
- Do NOT include meta-claims about the study itself (e.g. "this study found...")
- Population should reflect the actual study population, not a generic label"""


def extract_claims_with_claude(abstract: str, paper: dict) -> list[dict] | None:
    """Call claude -p to extract claims from an abstract."""
    prompt = build_claude_prompt(abstract, paper)

    try:
        # Remove CLAUDECODE env vars so claude CLI doesn't refuse to run
        env = {k: v for k, v in __import__("os").environ.items() if "CLAUDE" not in k.upper()}
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        if result.returncode != 0:
            print(f"    Claude CLI failed (exit {result.returncode}): {result.stderr[:200]}")
            return None

        # Parse the outer JSON wrapper from --output-format json
        try:
            wrapper = json.loads(result.stdout)
            raw_text = wrapper.get("result", result.stdout)
        except json.JSONDecodeError:
            raw_text = result.stdout

        # Strip markdown fencing if present
        text = raw_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        claims = json.loads(text)
        if not isinstance(claims, list):
            print(f"    Claude returned non-array: {type(claims)}")
            return None

        return claims

    except subprocess.TimeoutExpired:
        print("    Claude CLI timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"    Failed to parse Claude output as JSON: {e}")
        print(f"    Raw output (first 300 chars): {raw_text[:300]}")
        return None


def main() -> None:
    """Main entry point."""
    CLAIMS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading papers from domain files...")
    all_papers = load_all_papers()
    print(f"  Found {len(all_papers)} total papers across all domains")

    manifest = load_manifest()
    print(f"  Manifest has {len(manifest)} entries")

    # Filter to pending papers
    pending = []
    for paper in all_papers:
        paper_id = paper["id"]
        entry = manifest.get(paper_id, {})
        if entry.get("status") in ("complete", "failed"):
            continue
        pending.append(paper)

    print(f"  {len(pending)} papers pending")
    to_process = pending[:MAX_PAPERS]
    print(f"  Processing {len(to_process)} papers this session\n")

    completed = 0
    failed = 0

    for i, paper in enumerate(to_process, 1):
        paper_id = paper["id"]
        domain_id = paper["domain_id"]
        print(f"[{i}/{len(to_process)}] {paper_id}")
        print(f"  Domain: {domain_id}")
        print(f"  Title: {paper.get('title', 'N/A')[:80]}")

        # Fetch abstract
        abstract = fetch_abstract(paper)
        if not abstract:
            print("  FAILED: No abstract available from any source")
            manifest[paper_id] = {
                "status": "failed",
                "domain_id": domain_id,
                "reason": "no_abstract",
            }
            save_manifest(manifest)
            failed += 1
            print()
            continue

        print(f"  Abstract fetched ({len(abstract)} chars)")

        # Extract claims via Claude
        claims = extract_claims_with_claude(abstract, paper)
        if claims is None:
            print("  FAILED: Claude extraction failed")
            manifest[paper_id] = {
                "status": "failed",
                "domain_id": domain_id,
                "reason": "claude_extraction_failed",
            }
            save_manifest(manifest)
            failed += 1
            print()
            continue

        # Write claims file
        output_path = CLAIMS_DIR / f"{paper_id}.json"
        with open(output_path, "w") as f:
            json.dump(claims, f, indent=2)

        manifest[paper_id] = {
            "status": "complete",
            "domain_id": domain_id,
            "claims_count": len(claims),
            "output_path": str(output_path.relative_to(RESEARCH_DIR)),
        }
        save_manifest(manifest)
        completed += 1
        print(f"  OK: {len(claims)} claims → {output_path.name}")
        print()

    print("=" * 60)
    print(f"Session complete: {completed} succeeded, {failed} failed")
    print(f"Total in manifest: {len(manifest)} papers")
    remaining = len(pending) - len(to_process)
    if remaining > 0:
        print(f"Remaining: {remaining} papers still pending")


if __name__ == "__main__":
    main()
