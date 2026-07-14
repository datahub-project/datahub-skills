#!/usr/bin/env python3
"""Deterministic helpers for DataHub schema-change certification.

The script is intentionally standard-library only. It never calls DataHub, executes SQL,
or mutates files outside the temporary directory used by ``self-test``. MCP calls remain
under the host agent's explicit approval and tool controls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = SKILL_ROOT / "references" / "policy-v1.json"
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SECRET_KEY = re.compile(
    r"(^|_)(token|password|secret|credential|api_?key|private_?key)($|_)", re.I
)
STRONG_CREDENTIAL_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(
        r"\b(?:datahub_pat_|dh_pat_|dhp_|acryl_pat_)[A-Za-z0-9._-]{20,}\b",
        re.I,
    ),
)
RUNTIME_ASSIGNMENT = re.compile(
    r"(?:^|[\s,;{(])([\"']?)(datahub(?:_gms)?[_ -]?token|"
    r"(?:[a-z][a-z0-9]*[_ -]+)?(?:operator|api)[_ -]?token|"
    r"github[_ -]?(?:pat|token)|"
    r"gh[_ -]?token|personal[_ -]?access[_ -]?token|access[_ -]?token|"
    r"auth(?:orization)?[_ -]?token|operator[_ -]?token|api[_ -]?key|"
    r"client[_ -]?secret|token|credential|secret|password|pat)\1\s*"
    r"(?:=|:)\s*(?:\"([^\"\r\n]*)\"|'([^'\r\n]*)'|([^\s,;}\])]+))",
    re.I | re.M,
)
EXPLICIT_CREDENTIAL_KEY = re.compile(
    r"^(?:datahub|github|gh|personal|access|auth|authorization|operator|api|"
    r"client|[a-z][a-z0-9]*[_ -]+(?:operator|api))",
    re.I,
)


class CertificationError(Exception):
    """A deterministic contract failure with a stable process exit code."""

    def __init__(self, message: str, code: int = 2) -> None:
        super().__init__(message)
        self.code = code


def canonical_bytes(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as error:
        raise CertificationError(f"Value is not canonical JSON: {error}") from error
    return encoded.encode("utf-8")


def digest(value: Any) -> str:
    data = value if isinstance(value, bytes) else canonical_bytes(value)
    return hashlib.sha256(data).hexdigest()


def read_json(path: str | Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CertificationError(f"Cannot read JSON from {path}: {error}") from error


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CertificationError(f"{label} must be a JSON object")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CertificationError(f"{label} must be a non-empty string")
    return value.strip()


def parse_timestamp(value: Any, label: str) -> datetime:
    text = require_text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise CertificationError(f"{label} must be ISO 8601: {text}") from error
    if parsed.tzinfo is None:
        raise CertificationError(f"{label} must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def current_time(value: str | None) -> datetime:
    return parse_timestamp(value, "--now") if value else datetime.now(timezone.utc)


def placeholder_credential(value: Any) -> bool:
    normalized = str(value or "").strip().strip("'\"").strip()
    if not normalized:
        return True
    if re.fullmatch(
        r"(?:<[^>]+>|\$\{[^}]+\}|\$\(.*\)|\*+|x+|redacted|null|none)",
        normalized,
        re.I,
    ):
        return True
    if re.fullmatch(
        r"(?:(?:paste|generate|your)[-_].*(?:token|credential|value|secret).*|"
        r"local[-_]token(?:[-_]only)?|token[-_]here|buraya_.*(?:anahtar|token).*)",
        normalized,
        re.I,
    ):
        return True
    return bool(
        re.search(
            r"(?:your[_ -]?(?:token|secret)|replace[_ -]?me|change[_ -]?me|"
            r"example|placeholder|test-only|secrets\.|process\.env|env\.)",
            normalized,
            re.I,
        )
    )


def token_like_assignment_value(value: Any) -> bool:
    normalized = str(value or "").strip()
    if placeholder_credential(normalized):
        return False
    if not re.fullmatch(r"[A-Za-z0-9._~+/=-]+", normalized):
        return False
    return len(normalized) >= 16 or (
        len(normalized) >= 12
        and bool(re.search(r"[A-Za-z]", normalized))
        and bool(re.search(r"[0-9._~+/=-]", normalized))
    )


def credential_signatures(value: Any) -> list[str]:
    """Return labels only; never return or interpolate matched credential values."""

    content = str(value or "")
    signatures: list[str] = []
    for pattern in STRONG_CREDENTIAL_PATTERNS:
        if pattern.search(content):
            signatures.append("token-pattern")

    bearer = re.compile(r"\bbearer[ \t]+([\"']?)([A-Za-z0-9._~+/=-]{12,})\1", re.I)
    for match in bearer.finditer(content):
        if not placeholder_credential(match.group(2)):
            signatures.append("bearer-credential")

    for match in RUNTIME_ASSIGNMENT.finditer(content):
        key = match.group(2)
        assigned = match.group(3) or match.group(4) or match.group(5) or ""
        if placeholder_credential(assigned):
            continue
        if EXPLICIT_CREDENTIAL_KEY.search(key) or token_like_assignment_value(assigned):
            signatures.append("credential-assignment")
    return sorted(set(signatures))


def assert_no_secrets(value: Any, location: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if SECRET_KEY.search(str(key)):
                raise CertificationError("Credential-shaped key is forbidden")
            assert_no_secrets(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_secrets(item, f"{location}[{index}]")
    elif isinstance(value, str) and credential_signatures(value):
        raise CertificationError(f"Credential-shaped value is forbidden at {location}")


def load_policy(path: str | Path) -> dict[str, Any]:
    policy = require_object(read_json(path), "policy")
    require_text(policy.get("policyVersion"), "policy.policyVersion")
    if not isinstance(policy.get("riskWeights"), dict):
        raise CertificationError("policy.riskWeights must be an object")
    return policy


def tool_inventory_source(payload: Any) -> dict[str, Any]:
    source = require_object(payload, "tool inventory capture")
    assert_no_secrets(
        {
            "captureState": source.get("captureState"),
            "capturedAt": source.get("capturedAt"),
            "mcp": source.get("mcp"),
        }
    )
    if source.get("captureState") != "PASS":
        raise CertificationError("tool inventory captureState must be PASS")
    parse_timestamp(source.get("capturedAt"), "tool inventory capturedAt")
    mcp = require_object(source.get("mcp"), "tool inventory mcp")
    require_text(mcp.get("serverName"), "tool inventory mcp.serverName")
    require_text(mcp.get("protocolVersion"), "tool inventory mcp.protocolVersion")
    if not isinstance(source.get("tools"), list):
        raise CertificationError("tool inventory capture must contain a tools array")
    return source


def tool_inventory(payload: Any) -> dict[str, dict[str, Any] | None]:
    source = tool_inventory_source(payload)
    entries = source["tools"]
    if not isinstance(entries, list):
        raise CertificationError("tool inventory must contain a tools array")

    inventory: dict[str, dict[str, Any] | None] = {}
    for entry in entries:
        if isinstance(entry, str):
            inventory[entry] = None
            continue
        if not isinstance(entry, dict):
            raise CertificationError(
                "every tool inventory entry must be a string or object"
            )
        name = require_text(entry.get("name"), "tool.name")
        schema = entry.get("inputSchema", entry.get("input_schema"))
        inventory[name] = schema if isinstance(schema, dict) else None
    return inventory


def schema_properties(schema: dict[str, Any] | None) -> set[str] | None:
    if schema is None:
        return None
    properties = schema.get("properties")
    return set(properties) if isinstance(properties, dict) else set()


def normalized_property_bindings(payload: Any) -> dict[str, dict[str, str]]:
    if payload is None:
        return {}
    source = require_object(payload, "structured-property bindings")
    bindings = source.get("bindings", source)
    if not isinstance(bindings, dict):
        raise CertificationError("structured-property bindings must be an object")

    normalized: dict[str, dict[str, str]] = {}
    for role, binding in bindings.items():
        item = require_object(binding, f"property binding {role}")
        urn = require_text(item.get("urn"), f"property binding {role}.urn")
        value_type = require_text(
            item.get("valueType"), f"property binding {role}.valueType"
        )
        if not urn.startswith("urn:li:structuredProperty:"):
            raise CertificationError(f"property binding {role} has an invalid URN")
        if item.get("verificationState") != "PASS":
            raise CertificationError(
                f"property binding {role} lacks exact definition verification"
            )
        evidence_hash = require_text(
            item.get("definitionEvidenceHash"),
            f"property binding {role}.definitionEvidenceHash",
        ).lower()
        if not SHA256.fullmatch(evidence_hash):
            raise CertificationError(
                f"property binding {role} has an invalid definition evidence hash"
            )
        normalized[str(role)] = {
            "urn": urn,
            "valueType": value_type,
            "verificationState": "PASS",
            "definitionEvidenceHash": evidence_hash,
        }
    return normalized


def run_preflight(
    inventory_payload: Any,
    property_payload: Any,
    policy: dict[str, Any],
) -> dict[str, Any]:
    source = tool_inventory_source(inventory_payload)
    if property_payload is not None:
        assert_no_secrets(property_payload)
    inventory = tool_inventory(inventory_payload)
    contract = require_object(policy.get("toolContract"), "policy.toolContract")
    expected_schemas = require_object(
        contract.get("requiredParameters"), "policy.toolContract.requiredParameters"
    )

    required_analysis = list(contract.get("analysisTools", []))
    core_mutations = list(contract.get("coreMutationTools", []))
    optional_mutations = list(contract.get("optionalMutationTools", []))
    verification_tools = list(contract.get("verificationTools", []))
    required_tools = required_analysis + core_mutations + verification_tools

    missing = sorted({name for name in required_tools if name not in inventory})
    schema_unverified: list[str] = []
    schema_mismatches: dict[str, list[str]] = {}
    for name in dict.fromkeys(required_tools + optional_mutations):
        if name not in inventory:
            continue
        properties = schema_properties(inventory[name])
        expected = set(expected_schemas.get(name, []))
        if properties is None:
            schema_unverified.append(name)
        else:
            absent = sorted(expected - properties)
            if absent:
                schema_mismatches[name] = absent

    analysis_blockers = sorted(
        set(required_analysis)
        & (set(missing) | set(schema_unverified) | set(schema_mismatches))
    )
    mutation_blockers = sorted(
        set(core_mutations + verification_tools)
        & (set(missing) | set(schema_unverified) | set(schema_mismatches))
    )

    property_errors: list[str] = []
    try:
        property_bindings = normalized_property_bindings(property_payload)
    except CertificationError as error:
        property_bindings = {}
        property_errors.append(str(error))
    expected_roles = require_object(
        policy.get("structuredPropertyRoles"), "policy.structuredPropertyRoles"
    )
    for role, expected_type in expected_roles.items():
        binding = property_bindings.get(role)
        if binding is None:
            property_errors.append(f"missing binding for {role}")
        elif binding["valueType"].lower() != str(expected_type).lower():
            property_errors.append(
                f"{role} expects {expected_type}, got {binding['valueType']}"
            )

    optional_properties_ready = not property_errors
    add_properties_ready = (
        "add_structured_properties" in optional_mutations
        and "add_structured_properties" in inventory
        and "add_structured_properties" not in schema_unverified
        and "add_structured_properties" not in schema_mismatches
        and optional_properties_ready
    )
    analysis_ready = not analysis_blockers
    writeback_ready = analysis_ready and not mutation_blockers

    permitted = []
    if writeback_ready:
        for name in contract.get("safeMutationOrder", []):
            if name == "add_structured_properties" and not add_properties_ready:
                continue
            if name in core_mutations or name in optional_mutations:
                permitted.append(name)

    warnings: list[str] = []
    if schema_unverified:
        warnings.append("tool input schemas were not captured for every named tool")
    if property_errors:
        warnings.append(
            "structured properties are optional and were disabled: "
            + "; ".join(property_errors)
        )
    if "grep_documents" not in inventory:
        warnings.append(
            "grep_documents is unavailable; exact document content must be read with get_entities"
        )

    state = "PASS"
    if not analysis_ready:
        state = "FAIL"
    elif not writeback_ready:
        state = "WARN"
    elif warnings:
        state = "WARN"

    return {
        "state": state,
        "policyVersion": policy["policyVersion"],
        "toolInventoryHash": digest(inventory_payload),
        "propertyBindingsSourceHash": digest(property_payload),
        "mcp": source["mcp"],
        "analysisReady": analysis_ready,
        "writebackState": "PASS" if writeback_ready else "NOT_RUN",
        "runtimeMutationEnabled": all(name in inventory for name in core_mutations),
        "requiredAnalysisTools": required_analysis,
        "coreMutationTools": core_mutations,
        "permittedMutationTools": permitted,
        "missingTools": missing,
        "schemaUnverified": sorted(schema_unverified),
        "schemaMismatches": schema_mismatches,
        "propertyBindings": property_bindings if add_properties_ready else {},
        "propertyBindingErrors": property_errors,
        "warnings": warnings,
    }


def value_strings(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    values: list[str] = []
    for item in items:
        if isinstance(item, str):
            values.append(item)
        elif isinstance(item, dict):
            candidate = item.get("urn", item.get("name", item.get("value")))
            if isinstance(candidate, str):
                values.append(candidate)
    return values


def query_statement(query: dict[str, Any]) -> str:
    direct = query.get(
        "sql",
        query.get("statement", query.get("query", query.get("queryText"))),
    )
    if isinstance(direct, str):
        return direct
    if isinstance(direct, dict) and isinstance(direct.get("sql"), str):
        return direct["sql"]
    properties = query.get("properties")
    if isinstance(properties, dict):
        statement = properties.get("statement")
        if isinstance(statement, str):
            return statement
        if isinstance(statement, dict) and isinstance(statement.get("value"), str):
            return statement["value"]
    return ""


def query_dataset_urn(query: dict[str, Any]) -> str | None:
    direct = query.get("datasetUrn")
    if isinstance(direct, str):
        return direct
    subjects = query.get("subjects")
    if isinstance(subjects, list):
        for subject in subjects:
            if isinstance(subject, str) and subject.startswith("urn:li:dataset:"):
                return subject
            if isinstance(subject, dict):
                direct_urn = subject.get("urn")
                if isinstance(direct_urn, str) and direct_urn.startswith(
                    "urn:li:dataset:"
                ):
                    return direct_urn
                entity = subject.get("entity")
                if isinstance(entity, dict) and isinstance(entity.get("urn"), str):
                    return entity["urn"]
                dataset = subject.get("dataset")
                if isinstance(dataset, dict) and isinstance(dataset.get("urn"), str):
                    return dataset["urn"]
    return None


def nonnegative_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CertificationError(f"{label} must be a non-negative integer")
    return value


def evidence_class(context: dict[str, Any], policy: dict[str, Any]) -> str:
    boundary = require_text(context.get("evidenceBoundary"), "context.evidenceBoundary")
    boundaries = require_object(
        policy.get("evidenceBoundaries"), "policy.evidenceBoundaries"
    )
    mutation_eligible = set(boundaries.get("mutationEligible", []))
    non_live = set(boundaries.get("nonLive", []))
    if boundary in mutation_eligible:
        return "LIVE_VERIFIED"
    if boundary in non_live:
        return "NON_LIVE"
    return "UNKNOWN"


def query_payload_container(payload: Any) -> dict[str, Any]:
    value = require_object(payload, "get_dataset_queries payload")
    result = value.get("result")
    return result if isinstance(result, dict) else value


def normalized_raw_query(item: Any, index: int, target_urn: str) -> dict[str, str]:
    query = require_object(item, f"query record {index}")
    if query_dataset_urn(query) != target_urn:
        raise CertificationError(
            "every query record must be bound to the exact target dataset"
        )
    statement = require_text(query_statement(query), f"query record {index}.statement")
    identifier = query.get(
        "id",
        query.get("queryId", query.get("query_id", query.get("urn"))),
    )
    identifier = str(identifier) if identifier is not None else f"datahub-query-{index}"
    return {"id": identifier, "datasetUrn": target_urn, "statement": statement}


def validate_live_provenance(
    request: dict[str, Any],
    context: dict[str, Any],
    raw_evidence: Any,
    policy: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(raw_evidence, list):
        raise CertificationError("live certification requires raw MCP call evidence")
    assert_no_secrets(raw_evidence, "$rawEvidence")
    provenance = require_object(context.get("provenance"), "context.provenance")
    claimed_hash = require_text(
        provenance.get("rawEvidenceHash"), "context.provenance.rawEvidenceHash"
    ).lower()
    if not SHA256.fullmatch(claimed_hash) or claimed_hash != digest(raw_evidence):
        raise CertificationError("raw MCP evidence hash mismatch")

    calls: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_evidence):
        call = require_object(raw, f"raw evidence call {index}")
        require_text(call.get("tool"), f"raw evidence call {index}.tool")
        if call.get("state") != "PASS":
            raise CertificationError("every captured MCP call must have state PASS")
        require_object(call.get("arguments"), f"raw evidence call {index}.arguments")
        require_object(call.get("payload"), f"raw evidence call {index}.payload")
        calls.append(call)

    tool_types = sorted({str(call["tool"]) for call in calls})
    required_tools = set(policy["toolContract"]["analysisTools"])
    if not required_tools <= set(tool_types):
        raise CertificationError("raw MCP evidence omits required analysis tools")
    if provenance.get("toolTypes") != tool_types:
        raise CertificationError("context MCP tool provenance does not match raw calls")
    if provenance.get("rawCallCount") != len(calls):
        raise CertificationError("context raw call count does not match raw evidence")

    mcp = require_object(provenance.get("mcp"), "context.provenance.mcp")
    if mcp.get("initializationState") != "PASS":
        raise CertificationError("MCP initialization provenance must be PASS")
    require_text(mcp.get("serverName"), "context.provenance.mcp.serverName")
    require_text(mcp.get("protocolVersion"), "context.provenance.mcp.protocolVersion")
    inventory_hash = require_text(
        mcp.get("toolInventoryHash"), "context.provenance.mcp.toolInventoryHash"
    ).lower()
    if not SHA256.fullmatch(inventory_hash):
        raise CertificationError("MCP tool inventory hash is invalid")

    target_urn = request["targetUrn"]
    query_calls = [call for call in calls if call["tool"] == "get_dataset_queries"]
    if not query_calls:
        raise CertificationError("get_dataset_queries did not execute successfully")

    pages: list[dict[str, Any]] = []
    for call in query_calls:
        arguments = call["arguments"]
        if arguments.get("urn") != target_urn:
            raise CertificationError(
                "get_dataset_queries evidence targets another dataset"
            )
        container = query_payload_container(call["payload"])
        if "total" not in container:
            raise CertificationError("get_dataset_queries total is missing")
        total = nonnegative_integer(container["total"], "get_dataset_queries total")
        if "start" not in container:
            raise CertificationError("get_dataset_queries start offset is missing")
        start = nonnegative_integer(container["start"], "get_dataset_queries start")
        candidates = [
            container.get("queries"),
            container.get("results"),
            container.get("searchResults"),
        ]
        items = next(
            (candidate for candidate in candidates if isinstance(candidate, list)), None
        )
        if items is None:
            if total:
                raise CertificationError(
                    "query total is non-zero but structured query records are absent"
                )
            items = []
        if "returned" in container and nonnegative_integer(
            container["returned"], "get_dataset_queries returned"
        ) != len(items):
            raise CertificationError(
                "query returned count does not match structured query records"
            )
        has_more = container.get("hasMore")
        if has_more is not None and not isinstance(has_more, bool):
            raise CertificationError("get_dataset_queries hasMore must be boolean")
        if container.get("truncated") is True:
            raise CertificationError("get_dataset_queries evidence is truncated")
        pages.append(
            {
                "start": start,
                "total": total,
                "items": items,
                "hasMore": has_more,
            }
        )

    pages.sort(key=lambda page: page["start"])
    expected_start = 0
    total = pages[0]["total"]
    raw_items: list[Any] = []
    for index, page in enumerate(pages):
        if page["total"] != total:
            raise CertificationError("query pages disagree on explicit total")
        if page["start"] != expected_start:
            raise CertificationError("query pagination has a gap or duplicate page")
        page_end = page["start"] + len(page["items"])
        if page["hasMore"] is True and page_end >= total:
            raise CertificationError(
                "query hasMore metadata contradicts explicit total"
            )
        if page["hasMore"] is False and index != len(pages) - 1:
            raise CertificationError("query pagination continued after a final page")
        raw_items.extend(page["items"])
        expected_start += len(page["items"])
    if pages[-1]["hasMore"] is True or len(raw_items) != total:
        raise CertificationError("query retrieval is incomplete or truncated")

    normalized_queries = [
        normalized_raw_query(item, index + 1, target_urn)
        for index, item in enumerate(raw_items)
    ]
    query_ids = [item["id"] for item in normalized_queries]
    if len(query_ids) != len(set(query_ids)):
        raise CertificationError("query pagination contains duplicate query records")
    if context.get("queries") != normalized_queries:
        raise CertificationError(
            "normalized query context does not match raw query evidence"
        )
    query_retrieval = {
        "state": "PASS",
        "executed": True,
        "total": total,
        "returned": len(normalized_queries),
        "pageCount": len(pages),
        "paginationComplete": True,
        "truncated": False,
    }
    if provenance.get("queryRetrieval") != query_retrieval:
        raise CertificationError(
            "query retrieval provenance does not match raw query evidence"
        )
    return {
        "rawEvidenceHash": claimed_hash,
        "toolTypes": tool_types,
        "rawCallCount": len(calls),
        "queryRetrieval": query_retrieval,
    }


def run_risk(
    request: dict[str, Any],
    context: dict[str, Any],
    impact: dict[str, Any],
    policy: dict[str, Any],
    now: datetime,
    raw_evidence: Any = None,
) -> dict[str, Any]:
    assert_no_secrets(request)
    assert_no_secrets(context)
    assert_no_secrets(impact)
    validate_request(request, policy)
    target_urn = require_text(request.get("targetUrn"), "request.targetUrn")
    source_field = require_text(request.get("sourceField"), "request.sourceField")
    if not IDENTIFIER.fullmatch(source_field):
        raise CertificationError("request.sourceField is not a safe SQL identifier")

    target = require_object(context.get("target"), "context.target")
    if target.get("urn") != target_urn:
        raise CertificationError("context target does not match request.targetUrn")
    validate_evidence_completeness(request, context, impact)
    boundary_class = evidence_class(context, policy)
    if boundary_class == "LIVE_VERIFIED":
        validate_live_provenance(request, context, raw_evidence, policy)
    impacted = impact.get("impacted", [])
    if not isinstance(impacted, list):
        raise CertificationError("impact.impacted must be an array")
    counts = require_object(impact.get("counts"), "impact.counts")
    total = counts.get("total")
    if not isinstance(total, int) or total < 0 or total != len(impacted):
        raise CertificationError(
            "impact.counts.total must equal the number of impacted entities"
        )

    weights = policy["riskWeights"]
    findings: list[dict[str, Any]] = []

    def add(
        code: str,
        severity: str,
        weight_name: str,
        message: str,
        evidence: list[str],
    ) -> None:
        weight = weights.get(weight_name)
        if not isinstance(weight, int) or weight < 0:
            raise CertificationError(f"invalid policy weight: {weight_name}")
        findings.append(
            {
                "code": code,
                "severity": severity,
                "weight": weight,
                "message": message,
                "evidence": sorted(set(evidence)),
            }
        )

    incidents = target.get("incidents", [])
    active_incidents = [
        item
        for item in incidents
        if isinstance(item, dict) and str(item.get("state", "")).upper() == "ACTIVE"
    ]
    if active_incidents:
        add(
            "ACTIVE_INCIDENT",
            "BLOCKER",
            "activeIncident",
            "The target has an active DataHub incident.",
            [str(item.get("urn", "unknown")) for item in active_incidents],
        )
    if total:
        add(
            "BREAKING_LINEAGE",
            "HIGH",
            "breakingDownstream",
            f"The breaking request reaches {total} downstream entities.",
            [
                str(item.get("urn", "unknown"))
                for item in impacted
                if isinstance(item, dict)
            ],
        )

    sensitive = [
        item
        for item in value_strings(target.get("tags", []))
        + value_strings(target.get("terms", []))
        if re.search(r"pii|personal|email|sensitive", item, re.I)
    ]
    if sensitive:
        add(
            "SENSITIVE_DATA",
            "HIGH",
            "sensitiveData",
            "The target has sensitive-data governance signals.",
            sensitive,
        )

    token = re.compile(
        rf"(?<![A-Za-z0-9_]){re.escape(source_field)}(?![A-Za-z0-9_])", re.I
    )
    query_hits: list[str] = []
    queries = context.get("queries", [])
    if not isinstance(queries, list):
        raise CertificationError("context.queries must be an array")
    for query in queries:
        if not isinstance(query, dict) or query_dataset_urn(query) != target_urn:
            continue
        if token.search(query_statement(query)):
            identifier = query.get("id", query.get("urn", "query-without-id"))
            query_hits.append(str(identifier))
    if query_hits:
        add(
            "LIVE_QUERY_USAGE",
            "HIGH",
            "queryUsage",
            f"{len(query_hits)} observed queries reference the field.",
            query_hits,
        )

    all_assets = [target] + [item for item in impacted if isinstance(item, dict)]
    ownerless = [
        str(item.get("urn", "unknown"))
        for item in all_assets
        if not value_strings(item.get("owners", []))
    ]
    if ownerless:
        add(
            "MISSING_OWNER",
            "MEDIUM",
            "missingOwner",
            f"{len(ownerless)} affected entities have no accountable owner.",
            ownerless,
        )
    if not isinstance(target.get("assertions"), list) or not target.get("assertions"):
        add(
            "NO_ASSERTION_COVERAGE",
            "MEDIUM",
            "missingAssertions",
            "No DataHub assertion protects the target.",
            [target_urn],
        )

    observed_at = parse_timestamp(context.get("observedAt"), "context.observedAt")
    age_hours = (now - observed_at).total_seconds() / 3600
    max_future_minutes = int(policy.get("maxFutureSkewMinutes", 5))
    if (
        age_hours > float(policy["contextMaxAgeHours"])
        or age_hours < -max_future_minutes / 60
    ):
        add(
            "STALE_CONTEXT",
            "HIGH",
            "staleContext",
            "DataHub context is stale, invalid, or unreasonably future-dated.",
            [isoformat(observed_at)],
        )

    score = min(100, sum(item["weight"] for item in findings))
    has_blocker = any(item["severity"] == "BLOCKER" for item in findings)
    if has_blocker or score >= int(policy["blockedScore"]):
        verdict = "BLOCKED"
    elif score >= int(policy["approvalRequiredScore"]):
        verdict = "REVIEW_REQUIRED"
    else:
        verdict = "LOW_RISK"

    result = {
        "policyVersion": policy["policyVersion"],
        "policyHash": digest(policy),
        "evaluatedAt": isoformat(now),
        "evidenceClass": boundary_class,
        "score": score,
        "verdict": verdict,
        "findings": findings,
        "contextAgeHours": max(0, round(age_hours, 6)),
    }
    return {**result, "riskHash": digest(result)}


def safe_file(root: Path, relative: Any, label: str) -> tuple[str, Path]:
    text = require_text(relative, label).replace("\\", "/")
    candidate = Path(text)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise CertificationError(f"{label} must remain inside the artifact root")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise CertificationError(f"{label} escapes the artifact root") from error
    if not resolved.is_file():
        raise CertificationError(f"{label} does not exist: {text}")
    return text, resolved


def file_text(path: Path, label: str) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise CertificationError(f"{label} is not readable UTF-8: {error}") from error
    if not text.strip():
        raise CertificationError(f"{label} is empty")
    return text


def identifier_list(value: Any, label: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise CertificationError(f"{label} must be a non-empty array")
    result: list[str] = []
    for item in value:
        text = require_text(item, label)
        if not IDENTIFIER.fullmatch(text):
            raise CertificationError(f"{label} contains an unsafe identifier: {text}")
        result.append(text)
    if len(result) != len(set(result)):
        raise CertificationError(f"{label} contains duplicate identifiers")
    return result


def contains_identifier(content: str, identifier: str) -> bool:
    return bool(
        re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(identifier)}(?![A-Za-z0-9_])",
            content,
            re.I,
        )
    )


def run_artifact_validation(
    root_path: str, descriptor: dict[str, Any]
) -> dict[str, Any]:
    assert_no_secrets(descriptor)
    root = Path(root_path).resolve()
    if not root.is_dir():
        raise CertificationError(f"artifact root is not a directory: {root}")
    strategy = require_text(descriptor.get("strategy"), "descriptor.strategy")
    if strategy != "expand_migrate_contract":
        raise CertificationError("descriptor.strategy must be expand_migrate_contract")
    summary = require_text(descriptor.get("summary"), "descriptor.summary")
    available_models = set(
        identifier_list(
            descriptor.get("availableModels", []),
            "descriptor.availableModels",
            allow_empty=True,
        )
    )

    files: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    model_columns: dict[str, set[str]] = {}

    def capture(relative: Any, kind: str, label: str) -> tuple[str, str]:
        relative_text, absolute = safe_file(root, relative, label)
        if relative_text in seen_paths:
            raise CertificationError(
                f"artifact path appears more than once: {relative_text}"
            )
        seen_paths.add(relative_text)
        content = file_text(absolute, label)
        assert_no_secrets(content, f"artifact:{relative_text}")
        files.append(
            {
                "path": relative_text,
                "kind": kind,
                "sha256": digest(absolute.read_bytes()),
            }
        )
        return relative_text, content

    models = descriptor.get("models")
    if not isinstance(models, list) or not models:
        raise CertificationError("descriptor.models must be a non-empty array")
    for index, raw in enumerate(models):
        model = require_object(raw, f"descriptor.models[{index}]")
        name = require_text(model.get("name"), f"descriptor.models[{index}].name")
        if not IDENTIFIER.fullmatch(name) or name in model_columns:
            raise CertificationError(
                f"invalid or duplicate generated model name: {name}"
            )
        columns = identifier_list(
            model.get("producedColumns"), f"descriptor.models[{index}].producedColumns"
        )
        _, content = capture(
            model.get("path"), "DBT_MODEL", f"descriptor.models[{index}].path"
        )
        absent = [
            column for column in columns if not contains_identifier(content, column)
        ]
        if absent:
            raise CertificationError(
                f"model {name} does not structurally produce: {', '.join(absent)}"
            )
        model_columns[name] = set(columns)

    allowed_models = available_models | set(model_columns)
    tests = descriptor.get("tests")
    if not isinstance(tests, list) or not tests:
        raise CertificationError("descriptor.tests must be a non-empty array")
    for index, raw in enumerate(tests):
        test = require_object(raw, f"descriptor.tests[{index}]")
        model = require_text(test.get("model"), f"descriptor.tests[{index}].model")
        if model not in model_columns:
            raise CertificationError(
                f"tests reference unknown generated model: {model}"
            )
        columns = identifier_list(
            test.get("columns"), f"descriptor.tests[{index}].columns"
        )
        extra = sorted(set(columns) - model_columns[model])
        if extra:
            raise CertificationError(
                f"tests reference columns not produced by {model}: {', '.join(extra)}"
            )
        _, content = capture(
            test.get("path"), "DBT_TESTS", f"descriptor.tests[{index}].path"
        )
        absent = [
            value
            for value in [model, *columns]
            if not contains_identifier(content, value)
        ]
        if absent:
            raise CertificationError(
                f"test file omits its model or tested columns: {', '.join(absent)}"
            )

    rollbacks = descriptor.get("rollbacks")
    if not isinstance(rollbacks, list) or not rollbacks:
        raise CertificationError("descriptor.rollbacks must be a non-empty array")
    for index, raw in enumerate(rollbacks):
        rollback = require_object(raw, f"descriptor.rollbacks[{index}]")
        references = identifier_list(
            rollback.get("references"), f"descriptor.rollbacks[{index}].references"
        )
        unknown = sorted(set(references) - allowed_models)
        if unknown:
            raise CertificationError(
                "rollback references models that were neither generated nor declared pre-existing: "
                + ", ".join(unknown)
            )
        _, content = capture(
            rollback.get("path"), "ROLLBACK", f"descriptor.rollbacks[{index}].path"
        )
        absent = [name for name in references if not contains_identifier(content, name)]
        if absent:
            raise CertificationError(
                f"rollback file omits declared references: {', '.join(absent)}"
            )

    briefs = descriptor.get("ownerBriefs")
    if not isinstance(briefs, list) or not briefs:
        raise CertificationError("descriptor.ownerBriefs must be a non-empty array")
    for index, raw in enumerate(briefs):
        brief = require_object(raw, f"descriptor.ownerBriefs[{index}]")
        capture(
            brief.get("path"), "OWNER_BRIEF", f"descriptor.ownerBriefs[{index}].path"
        )

    files.sort(key=lambda item: item["path"])
    body = {
        "state": "PASS",
        "strategy": strategy,
        "summary": summary,
        "descriptorHash": digest(descriptor),
        "files": files,
        "models": [
            {"name": name, "producedColumns": sorted(columns)}
            for name, columns in sorted(model_columns.items())
        ],
    }
    return {**body, "artifactManifestHash": digest(body)}


def validate_request(request: dict[str, Any], policy: dict[str, Any]) -> None:
    if request.get("changeType") not in policy.get("supportedChanges", []):
        raise CertificationError("request.changeType is not supported by the policy")
    target_urn = require_text(request.get("targetUrn"), "request.targetUrn")
    if not target_urn.startswith("urn:li:dataset:"):
        raise CertificationError("request.targetUrn must be a dataset URN")
    require_text(request.get("requester"), "request.requester")
    require_text(request.get("rationale"), "request.rationale")
    source = require_text(request.get("sourceField"), "request.sourceField")
    if not IDENTIFIER.fullmatch(source):
        raise CertificationError("request.sourceField is not a safe identifier")
    if request["changeType"] in {"rename_column", "type_change"}:
        destination = require_text(
            request.get("destinationField"), "request.destinationField"
        )
        if not IDENTIFIER.fullmatch(destination):
            raise CertificationError(
                "request.destinationField is not a safe identifier"
            )
        if destination == source:
            raise CertificationError(
                "request.destinationField must differ from request.sourceField"
            )
    if request["changeType"] == "type_change":
        require_text(request.get("destinationType"), "request.destinationType")
    if "resumeExistingMigration" in request and not isinstance(
        request["resumeExistingMigration"], bool
    ):
        raise CertificationError("request.resumeExistingMigration must be boolean")


def validate_evidence_completeness(
    request: dict[str, Any], context: dict[str, Any], impact: dict[str, Any]
) -> None:
    """Reject ambiguous target, schema, pagination, or lineage-path evidence."""

    if context.get("targetMatchCount") != 1:
        raise CertificationError("context must prove exactly one target match")

    schema = require_object(context.get("schemaCoverage"), "context.schemaCoverage")
    if schema.get("hasMore") is not False:
        raise CertificationError("schema pagination is incomplete")
    if schema.get("sourceMatches") != 1:
        raise CertificationError("schema must contain exactly one source-field match")
    if request["changeType"] in {"rename_column", "type_change"}:
        expected_destination_matches = (
            1 if request.get("resumeExistingMigration") is True else 0
        )
        if schema.get("destinationMatches") != expected_destination_matches:
            raise CertificationError(
                "destination-field evidence does not match new or resumed migration state"
            )

    coverage = require_object(impact.get("coverage"), "impact.coverage")
    if coverage.get("hasMore") is not False:
        raise CertificationError("lineage pagination is incomplete")
    missing_paths = coverage.get("missingPathTargets")
    if not isinstance(missing_paths, list) or missing_paths:
        raise CertificationError("every downstream target must have an exact path")

    impacted = impact.get("impacted")
    if not isinstance(impacted, list):
        raise CertificationError("impact.impacted must be an array")
    seen: set[str] = set()
    for index, raw in enumerate(impacted):
        item = require_object(raw, f"impact.impacted[{index}]")
        urn = require_text(item.get("urn"), f"impact.impacted[{index}].urn")
        if urn in seen:
            raise CertificationError(f"duplicate impacted entity: {urn}")
        seen.add(urn)
        path = item.get("shortestPath")
        if (
            not isinstance(path, list)
            or len(path) < 2
            or path[0] != request["targetUrn"]
            or path[-1] != urn
        ):
            raise CertificationError(
                f"impact.impacted[{index}].shortestPath has invalid endpoints"
            )


def validate_scope(scope: dict[str, Any]) -> None:
    claimed = require_text(scope.get("scopeHash"), "scope.scopeHash")
    body = {key: value for key, value in scope.items() if key != "scopeHash"}
    if claimed != digest(body):
        raise CertificationError("scope hash does not match its canonical body", 4)


def run_scope(
    request: dict[str, Any],
    context: dict[str, Any],
    impact: dict[str, Any],
    risk: dict[str, Any],
    artifacts: dict[str, Any],
    artifact_root: str,
    artifact_descriptor: dict[str, Any],
    preflight: dict[str, Any],
    inventory_payload: Any,
    property_payload: Any,
    raw_evidence: Any,
    writeback_plan: dict[str, Any],
    policy: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    for value in (
        request,
        context,
        impact,
        risk,
        artifacts,
        artifact_descriptor,
        preflight,
        property_payload,
        raw_evidence,
        writeback_plan,
    ):
        assert_no_secrets(value)
    validate_request(request, policy)
    target_urn = request["targetUrn"]
    if context.get("target", {}).get("urn") != target_urn:
        raise CertificationError("context target does not match request")
    evaluated_at = parse_timestamp(risk.get("evaluatedAt"), "risk.evaluatedAt")
    skew = timedelta(minutes=int(policy.get("maxFutureSkewMinutes", 5)))
    if evaluated_at > now + skew:
        raise CertificationError("risk evaluation is unreasonably future-dated")
    expected_risk = run_risk(
        request, context, impact, policy, evaluated_at, raw_evidence
    )
    if risk != expected_risk:
        raise CertificationError(
            "risk result does not match deterministic recomputation"
        )
    observed_at = parse_timestamp(context.get("observedAt"), "context.observedAt")
    context_age = now - observed_at
    if context_age > timedelta(hours=float(policy["contextMaxAgeHours"])):
        raise CertificationError("context became stale before scope construction")
    if context_age < -skew:
        raise CertificationError("context is unreasonably future-dated")
    if any(item.get("code") == "STALE_CONTEXT" for item in risk["findings"]):
        raise CertificationError("stale context cannot enter an approval scope")
    expected_artifacts = run_artifact_validation(artifact_root, artifact_descriptor)
    if artifacts != expected_artifacts:
        raise CertificationError(
            "artifact manifest does not match current descriptor and file contents"
        )
    if expected_artifacts.get("strategy") != policy["migrationStrategy"]:
        raise CertificationError(
            "only expand_migrate_contract artifacts may enter certification"
        )
    model_columns = [
        set(item.get("producedColumns", []))
        for item in expected_artifacts.get("models", [])
        if isinstance(item, dict)
    ]
    required_fields = {request["sourceField"]}
    if request["changeType"] in {"rename_column", "type_change"}:
        required_fields.add(request["destinationField"])
    if not any(required_fields <= columns for columns in model_columns):
        raise CertificationError(
            "no generated compatibility model retains every request-bound field"
        )
    expected_preflight = run_preflight(inventory_payload, property_payload, policy)
    if preflight != expected_preflight:
        raise CertificationError(
            "preflight result does not match captured tool schemas and property evidence"
        )
    if expected_preflight.get("analysisReady") is not True:
        raise CertificationError("MCP analysis preflight is not ready")

    boundary = require_text(context.get("evidenceBoundary"), "context.evidenceBoundary")
    boundary_class = evidence_class(context, policy)
    if boundary_class == "LIVE_VERIFIED":
        context_mcp = require_object(
            context.get("provenance", {}).get("mcp"), "context.provenance.mcp"
        )
        inventory_source = tool_inventory_source(inventory_payload)
        if context_mcp.get("toolInventoryHash") != digest(inventory_payload):
            raise CertificationError(
                "live context is not bound to the captured tool inventory"
            )
        if (
            context_mcp.get("serverName") != inventory_source["mcp"]["serverName"]
            or context_mcp.get("protocolVersion")
            != inventory_source["mcp"]["protocolVersion"]
        ):
            raise CertificationError(
                "live context MCP provenance does not match tool inventory capture"
            )

    if boundary_class != "LIVE_VERIFIED":
        mutation_eligibility = {
            "state": "NOT_RUN",
            "boundary": boundary,
            "reason": "EVIDENCE_BOUNDARY_NOT_MUTATION_ELIGIBLE",
        }
    elif expected_preflight.get("writebackState") != "PASS":
        mutation_eligibility = {
            "state": "NOT_RUN",
            "boundary": boundary,
            "reason": "MUTATION_PREFLIGHT_NOT_READY",
        }
    else:
        mutation_eligibility = {
            "state": "PASS",
            "boundary": boundary,
            "reason": "LIVE_BOUNDARY_AND_PREFLIGHT_VERIFIED",
        }

    operations = writeback_plan.get("operations")
    if not isinstance(operations, list):
        raise CertificationError("writeback plan operations must be an array")
    if writeback_plan.get("retryMode") != "VERIFY_THEN_SKIP":
        raise CertificationError("writeback retryMode must be VERIFY_THEN_SKIP")
    permitted = (
        list(expected_preflight.get("permittedMutationTools", []))
        if mutation_eligibility["state"] == "PASS"
        else []
    )
    actual_tools = [item.get("tool") for item in operations if isinstance(item, dict)]
    if len(actual_tools) != len(operations) or actual_tools != permitted:
        raise CertificationError(
            "writeback plan must exactly match the preflight-permitted ordered tool set"
        )
    scope_valid_until = now + timedelta(hours=int(policy["passportValidityHours"]))
    templates = require_object(
        policy.get("writebackTemplates"), "policy.writebackTemplates"
    )
    for index, operation in enumerate(operations):
        if operation.get("targetUrn") != target_urn:
            raise CertificationError(
                f"writeback operation {index} targets another entity"
            )
        arguments = require_object(
            operation.get("arguments"), f"writeback operation {index}.arguments"
        )
        tool = operation["tool"]
        expected_parameters = set(
            policy["toolContract"]["requiredParameters"].get(tool, [])
        )
        argument_names = set(arguments)
        if argument_names != expected_parameters:
            raise CertificationError(
                f"writeback operation {index} arguments do not match the approved template schema"
            )
        if tool == "save_document":
            if (
                arguments.get("document_type") != templates["documentType"]
                or arguments.get("related_assets") != [target_urn]
                or arguments.get("title") != templates["documentTitle"]
                or arguments.get("content") != templates["documentContent"]
            ):
                raise CertificationError(
                    "save_document must use the passport template and exact related asset"
                )
        elif tool == "add_structured_properties":
            if arguments.get("entity_urns") != [target_urn]:
                raise CertificationError(
                    "add_structured_properties must target only the certified entity"
                )
            property_values = require_object(
                arguments.get("property_values"),
                "add_structured_properties.property_values",
            )
            expected_urns = {
                binding["urn"]
                for binding in expected_preflight.get("propertyBindings", {}).values()
            }
            if set(property_values) != expected_urns:
                raise CertificationError(
                    "structured-property values must exactly match preflight role bindings"
                )
            bindings_by_role = expected_preflight.get("propertyBindings", {})
            expected_values = {
                bindings_by_role["status"]["urn"]: ["CERTIFIED"],
                bindings_by_role["riskScore"]["urn"]: [risk["score"]],
                bindings_by_role["passportId"]["urn"]: ["${PASSPORT_ID}"],
                bindings_by_role["validUntil"]["urn"]: [
                    isoformat(scope_valid_until).split("T", 1)[0]
                ],
            }
            if property_values != expected_values:
                raise CertificationError(
                    "structured-property values do not match the approved semantic roles"
                )
        elif tool == "update_description":
            if (
                arguments.get("entity_urn") != target_urn
                or arguments.get("operation") != templates["descriptionOperation"]
                or arguments.get("description") != templates["description"]
            ):
                raise CertificationError(
                    "update_description must append one passport marker to the exact target"
                )

    body = {
        "scopeVersion": policy["scopeVersion"],
        "createdAt": isoformat(now),
        "validUntil": isoformat(scope_valid_until),
        "targetUrn": target_urn,
        "evidenceBoundary": boundary,
        "evidenceClass": boundary_class,
        "mutationEligibility": mutation_eligibility,
        "requestHash": digest(request),
        "contextHash": digest(context),
        "rawEvidenceHash": (
            context.get("provenance", {}).get("rawEvidenceHash")
            if boundary_class == "LIVE_VERIFIED"
            else None
        ),
        "impactHash": digest(impact),
        "riskHash": risk["riskHash"],
        "artifactManifestHash": expected_artifacts["artifactManifestHash"],
        "artifactDescriptorHash": expected_artifacts["descriptorHash"],
        "preflightHash": digest(expected_preflight),
        "toolInventoryHash": expected_preflight["toolInventoryHash"],
        "writebackPlanHash": digest(writeback_plan),
        "policy": {
            "version": policy["policyVersion"],
            "sha256": digest(policy),
        },
        "risk": {"score": risk["score"], "verdict": risk["verdict"]},
        "migration": {
            "strategy": expected_artifacts["strategy"],
            "summary": expected_artifacts["summary"],
            "files": expected_artifacts["files"],
        },
        "plannedMutations": writeback_plan,
    }
    return {**body, "scopeHash": digest(body)}


def run_passport(
    scope: dict[str, Any],
    approval: dict[str, Any],
    policy: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    assert_no_secrets(scope)
    assert_no_secrets(approval)
    validate_scope(scope)
    if scope.get("policy") != {
        "version": policy["policyVersion"],
        "sha256": digest(policy),
    }:
        raise CertificationError(
            "scope policy binding does not match the active policy"
        )
    decision = require_text(approval.get("decision"), "approval.decision").upper()
    if decision not in {"APPROVE", "REJECT"}:
        raise CertificationError("approval.decision must be APPROVE or REJECT")
    require_text(approval.get("reviewer"), "approval.reviewer")
    require_text(approval.get("note"), "approval.note")
    if approval.get("scopeHash") != scope["scopeHash"]:
        raise CertificationError("approval is not bound to the exact scope hash")
    if decision == "APPROVE" and approval.get("scopeAccepted") is not True:
        raise CertificationError("APPROVE requires scopeAccepted=true")
    if decision == "REJECT" and approval.get("scopeAccepted") is True:
        raise CertificationError("REJECT cannot accept the staged scope")
    identity_verification = approval.get("identityVerification", "SELF_ASSERTED")
    if identity_verification not in {"SELF_ASSERTED", "AUTHENTICATED"}:
        raise CertificationError(
            "approval.identityVerification must be SELF_ASSERTED or AUTHENTICATED"
        )
    decided_at = parse_timestamp(approval.get("decidedAt"), "approval.decidedAt")
    scope_created = parse_timestamp(scope.get("createdAt"), "scope.createdAt")
    skew = timedelta(minutes=int(policy.get("maxFutureSkewMinutes", 5)))
    if decided_at < scope_created - skew or decided_at > now + skew:
        raise CertificationError(
            "approval timestamp is outside the permitted decision window"
        )

    valid_until = parse_timestamp(scope.get("validUntil"), "scope.validUntil")
    if valid_until <= now:
        raise CertificationError("approved scope is already expired")
    body = {
        "passportVersion": policy["passportVersion"],
        "status": "CERTIFIED" if decision == "APPROVE" else "REJECTED",
        "createdAt": isoformat(now),
        "validUntil": isoformat(valid_until),
        "scope": scope,
        "approval": {
            "decision": decision,
            "reviewer": approval["reviewer"],
            "note": approval["note"],
            "scopeHash": approval["scopeHash"],
            "scopeAccepted": approval.get("scopeAccepted") is True,
            "decidedAt": isoformat(decided_at),
            "identityVerification": identity_verification,
        },
    }
    manifest_hash = digest(body)
    return {
        **body,
        "passportId": f"dhscp_{manifest_hash[:20]}",
        "manifestHash": manifest_hash,
    }


def run_verify_passport(
    passport: dict[str, Any], policy: dict[str, Any], now: datetime
) -> dict[str, Any]:
    try:
        assert_no_secrets(passport)
    except CertificationError:
        return {
            "valid": False,
            "state": "FAIL",
            "passportId": None,
            "manifestHash": None,
            "errors": ["credential-shaped passport content rejected"],
        }
    errors: list[str] = []
    passport_id = passport.get("passportId")
    manifest_hash = passport.get("manifestHash")
    body = {
        key: value
        for key, value in passport.items()
        if key not in {"passportId", "manifestHash"}
    }
    expected = digest(body)
    if manifest_hash != expected:
        errors.append("manifest hash mismatch")
    if passport_id != f"dhscp_{expected[:20]}":
        errors.append("passport ID mismatch")
    try:
        scope = require_object(passport.get("scope"), "passport.scope")
        validate_scope(scope)
    except CertificationError as error:
        errors.append(str(error))
        scope = {}
    if scope.get("policy") != {
        "version": policy["policyVersion"],
        "sha256": digest(policy),
    }:
        errors.append("active policy mismatch")
    approval = passport.get("approval")
    if not isinstance(approval, dict) or approval.get("scopeHash") != scope.get(
        "scopeHash"
    ):
        errors.append("approval scope binding mismatch")
    if passport.get("status") == "CERTIFIED" and (
        not isinstance(approval, dict)
        or approval.get("decision") != "APPROVE"
        or approval.get("scopeAccepted") is not True
    ):
        errors.append("certified passport lacks an exact APPROVE decision")
    if passport.get("status") == "REJECTED" and (
        not isinstance(approval, dict)
        or approval.get("decision") != "REJECT"
        or approval.get("scopeAccepted") is True
    ):
        errors.append("rejected passport lacks an exact REJECT decision")
    if passport.get("status") not in {"CERTIFIED", "REJECTED"}:
        errors.append("passport status is invalid")
    try:
        created_at = parse_timestamp(passport.get("createdAt"), "passport.createdAt")
        rebuilt = run_passport(
            scope,
            require_object(approval, "passport.approval"),
            policy,
            created_at,
        )
        if rebuilt != passport:
            errors.append("passport does not match deterministic reconstruction")
    except CertificationError as error:
        errors.append(str(error))
    try:
        passport_valid_until = parse_timestamp(
            passport.get("validUntil"), "passport.validUntil"
        )
        if passport_valid_until <= now:
            errors.append("passport expired")
        if scope and passport_valid_until != parse_timestamp(
            scope.get("validUntil"), "scope.validUntil"
        ):
            errors.append("passport validity does not match its approved scope")
    except CertificationError as error:
        errors.append(str(error))
    return {
        "valid": not errors,
        "state": "PASS" if not errors else "FAIL",
        "passportId": passport_id,
        "manifestHash": expected,
        "errors": errors,
    }


def emit(value: Any) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def self_test(policy: dict[str, Any]) -> dict[str, Any]:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)

    def must_reject(action: Any, label: str, forbidden_echo: str | None = None) -> None:
        try:
            action()
        except CertificationError as error:
            if forbidden_echo and forbidden_echo in str(error):
                raise CertificationError(
                    f"self-test leaked rejected credential content for {label}", 4
                ) from error
            return
        raise CertificationError(f"self-test accepted {label}", 4)

    if digest({"b": 2, "a": 1}) != digest({"a": 1, "b": 2}):
        raise CertificationError("canonical hashing is order-dependent", 4)

    required_parameters = policy["toolContract"]["requiredParameters"]
    tools = [
        {"name": name, "inputSchema": {"properties": {key: {} for key in parameters}}}
        for name, parameters in required_parameters.items()
    ]
    bindings = {
        "bindings": {
            role: {
                "urn": f"urn:li:structuredProperty:example.{role}",
                "valueType": value_type,
                "verificationState": "PASS",
                "definitionEvidenceHash": digest(
                    {"role": role, "valueType": value_type}
                ),
            }
            for role, value_type in policy["structuredPropertyRoles"].items()
        }
    }
    inventory_payload = {
        "captureState": "PASS",
        "capturedAt": isoformat(now),
        "mcp": {"serverName": "datahub", "protocolVersion": "2025-03-26"},
        "tools": tools,
    }
    preflight = run_preflight(inventory_payload, bindings, policy)
    if not preflight["analysisReady"] or preflight["writebackState"] != "PASS":
        raise CertificationError("preflight self-test failed", 4)

    target = "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.gold,PROD)"
    request = {
        "targetUrn": target,
        "changeType": "rename_column",
        "sourceField": "customer_email",
        "destinationField": "contact_email",
        "requester": "self-test",
        "rationale": "validate deterministic helper",
    }
    raw_evidence = [
        {
            "tool": "get_entities",
            "state": "PASS",
            "arguments": {"urns": [target]},
            "payload": {"result": [{"urn": target}]},
        },
        {
            "tool": "list_schema_fields",
            "state": "PASS",
            "arguments": {"urn": target},
            "payload": {"fields": ["customer_email"], "hasMore": False},
        },
        {
            "tool": "get_lineage",
            "state": "PASS",
            "arguments": {
                "urn": target,
                "upstream": False,
                "max_hops": 5,
                "max_results": 100,
            },
            "payload": {"total": 1, "hasMore": False},
        },
        {
            "tool": "get_lineage_paths_between",
            "state": "PASS",
            "arguments": {
                "source_urn": target,
                "target_urn": "urn:li:dashboard:downstream",
            },
            "payload": {"total": 1, "hasMore": False},
        },
        {
            "tool": "get_dataset_queries",
            "state": "PASS",
            "arguments": {"urn": target},
            "payload": {
                "start": 0,
                "total": 1,
                "returned": 1,
                "hasMore": False,
                "queries": [
                    {
                        "id": "query-1",
                        "datasetUrn": target,
                        "statement": "select customer_email from gold",
                    }
                ],
            },
        },
    ]
    query_retrieval = {
        "state": "PASS",
        "executed": True,
        "total": 1,
        "returned": 1,
        "pageCount": 1,
        "paginationComplete": True,
        "truncated": False,
    }
    context = {
        "observedAt": isoformat(now),
        "evidenceBoundary": "LIVE_DATAHUB_MCP_NORMALIZED",
        "targetMatchCount": 1,
        "schemaCoverage": {
            "hasMore": False,
            "sourceMatches": 1,
            "destinationMatches": 0,
        },
        "target": {
            "urn": target,
            "owners": [],
            "tags": ["PII"],
            "terms": [],
            "incidents": [],
            "assertions": [],
        },
        "queries": [
            {
                "id": "query-1",
                "datasetUrn": target,
                "statement": "select customer_email from gold",
            }
        ],
        "provenance": {
            "rawEvidenceHash": digest(raw_evidence),
            "rawCallCount": len(raw_evidence),
            "toolTypes": sorted({item["tool"] for item in raw_evidence}),
            "queryRetrieval": query_retrieval,
            "mcp": {
                "initializationState": "PASS",
                "serverName": "datahub",
                "protocolVersion": "2025-03-26",
                "toolInventoryHash": digest(inventory_payload),
            },
        },
    }
    impact = {
        "counts": {"total": 1},
        "impacted": [
            {
                "urn": "urn:li:dashboard:downstream",
                "owners": [],
                "shortestPath": [target, "urn:li:dashboard:downstream"],
            }
        ],
        "coverage": {"hasMore": False, "missingPathTargets": []},
    }
    risk = run_risk(request, context, impact, policy, now, raw_evidence)
    incomplete_context = json.loads(json.dumps(context))
    incomplete_context["schemaCoverage"]["hasMore"] = True
    must_reject(
        lambda: run_risk(
            request, incomplete_context, impact, policy, now, raw_evidence
        ),
        "incomplete schema evidence",
    )
    incomplete_impact = json.loads(json.dumps(impact))
    incomplete_impact["coverage"]["missingPathTargets"] = [
        "urn:li:dashboard:downstream"
    ]
    must_reject(
        lambda: run_risk(
            request, context, incomplete_impact, policy, now, raw_evidence
        ),
        "incomplete lineage-path evidence",
    )

    zero_query_evidence = json.loads(json.dumps(raw_evidence))
    zero_query_evidence[-1]["payload"] = {
        "start": 0,
        "total": 0,
        "returned": 0,
        "hasMore": False,
        "queries": [],
    }
    zero_query_context = json.loads(json.dumps(context))
    zero_query_context["queries"] = []
    zero_query_context["provenance"]["rawEvidenceHash"] = digest(zero_query_evidence)
    zero_query_context["provenance"]["queryRetrieval"] = {
        "state": "PASS",
        "executed": True,
        "total": 0,
        "returned": 0,
        "pageCount": 1,
        "paginationComplete": True,
        "truncated": False,
    }
    run_risk(
        request,
        zero_query_context,
        impact,
        policy,
        now,
        zero_query_evidence,
    )

    missing_query_evidence = [
        item for item in raw_evidence if item["tool"] != "get_dataset_queries"
    ]
    missing_query_context = json.loads(json.dumps(context))
    missing_query_context["queries"] = []
    missing_query_context["provenance"]["rawEvidenceHash"] = digest(
        missing_query_evidence
    )
    missing_query_context["provenance"]["rawCallCount"] = len(missing_query_evidence)
    missing_query_context["provenance"]["toolTypes"] = sorted(
        {item["tool"] for item in missing_query_evidence}
    )
    must_reject(
        lambda: run_risk(
            request,
            missing_query_context,
            impact,
            policy,
            now,
            missing_query_evidence,
        ),
        "live evidence without a successful query call",
    )

    hash_tampered_context = json.loads(json.dumps(context))
    hash_tampered_context["provenance"]["rawEvidenceHash"] = "0" * 64
    must_reject(
        lambda: run_risk(
            request,
            hash_tampered_context,
            impact,
            policy,
            now,
            raw_evidence,
        ),
        "raw evidence hash tampering",
    )

    truncated_query_evidence = json.loads(json.dumps(raw_evidence))
    truncated_query_evidence[-1]["payload"]["hasMore"] = True
    truncated_context = json.loads(json.dumps(context))
    truncated_context["provenance"]["rawEvidenceHash"] = digest(
        truncated_query_evidence
    )
    must_reject(
        lambda: run_risk(
            request,
            truncated_context,
            impact,
            policy,
            now,
            truncated_query_evidence,
        ),
        "truncated query evidence",
    )

    for safe_value in (
        "Never paste a token or credential into this rationale.",
        "token=<redacted>",
        "Authorization: Bearer <generate-a-random-token>",
        target,
        "Approve only the exact staged migration for customer_email.",
    ):
        assert_no_secrets({"value": safe_value})

    credential_samples = [
        "_".join(["github", "pat", "A1" * 16]),
        ".".join(["eyJ" + "a" * 12, "eyJ" + "b" * 12, "C3" * 14]),
        "Authorization: Bearer " + "D4" + "e" * 28,
        "token=" + "abcdefghijklmnop",
        "-----BEGIN " + "PRIVATE KEY-----",
    ]
    for sample in credential_samples:
        must_reject(
            lambda sample=sample: assert_no_secrets({"value": sample}),
            "credential-shaped string value",
            sample,
        )
    secret_request = json.loads(json.dumps(request))
    secret_request["rationale"] = credential_samples[0]
    must_reject(
        lambda: run_risk(secret_request, context, impact, policy, now, raw_evidence),
        "credential in request rationale",
        credential_samples[0],
    )

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "model.sql").write_text(
            "select customer_email, customer_email as contact_email from gold\n",
            encoding="utf-8",
        )
        (root / "model.yml").write_text(
            "models:\n  - name: gold_compat\n    columns:\n      - name: customer_email\n      - name: contact_email\n",
            encoding="utf-8",
        )
        (root / "rollback.sql").write_text(
            "select * from gold_compat\n", encoding="utf-8"
        )
        (root / "owners.md").write_text("# Owners\nSynthetic.\n", encoding="utf-8")
        descriptor = {
            "strategy": "expand_migrate_contract",
            "summary": "Add contact_email while retaining customer_email.",
            "availableModels": ["gold"],
            "models": [
                {
                    "name": "gold_compat",
                    "path": "model.sql",
                    "producedColumns": ["customer_email", "contact_email"],
                }
            ],
            "tests": [
                {
                    "model": "gold_compat",
                    "path": "model.yml",
                    "columns": ["customer_email", "contact_email"],
                }
            ],
            "rollbacks": [{"path": "rollback.sql", "references": ["gold_compat"]}],
            "ownerBriefs": [{"path": "owners.md"}],
        }
        artifacts = run_artifact_validation(str(root), descriptor)

    scope_temporary = tempfile.TemporaryDirectory()
    scope_root = Path(scope_temporary.name)
    (scope_root / "model.sql").write_text(
        "select customer_email, customer_email as contact_email from gold\n",
        encoding="utf-8",
    )
    (scope_root / "model.yml").write_text(
        "models:\n  - name: gold_compat\n    columns:\n      - name: customer_email\n      - name: contact_email\n",
        encoding="utf-8",
    )
    (scope_root / "rollback.sql").write_text(
        "select * from gold_compat\n", encoding="utf-8"
    )
    (scope_root / "owners.md").write_text("# Owners\nSynthetic.\n", encoding="utf-8")
    if run_artifact_validation(str(scope_root), descriptor) != artifacts:
        raise CertificationError("artifact recreation changed its manifest", 4)

    operations = []
    for tool in preflight["permittedMutationTools"]:
        if tool == "save_document":
            arguments = {
                "document_type": "Decision",
                "title": "Schema Change Passport ${PASSPORT_ID}",
                "content": "${PASSPORT_JSON}",
                "related_assets": [target],
            }
        elif tool == "add_structured_properties":
            by_role = preflight["propertyBindings"]
            arguments = {
                "property_values": {
                    by_role["status"]["urn"]: ["CERTIFIED"],
                    by_role["riskScore"]["urn"]: [risk["score"]],
                    by_role["passportId"]["urn"]: ["${PASSPORT_ID}"],
                    by_role["validUntil"]["urn"]: ["2026-07-15"],
                },
                "entity_urns": [target],
            }
        else:
            arguments = {
                "entity_urn": target,
                "operation": "append",
                "description": "Schema change passport ${PASSPORT_ID}",
            }
        operations.append(
            {
                "tool": tool,
                "targetUrn": target,
                "arguments": arguments,
            }
        )
    writeback = {"operations": operations, "retryMode": "VERIFY_THEN_SKIP"}
    scope = run_scope(
        request,
        context,
        impact,
        risk,
        artifacts,
        str(scope_root),
        descriptor,
        preflight,
        inventory_payload,
        bindings,
        raw_evidence,
        writeback,
        policy,
        now,
    )
    if scope["mutationEligibility"]["state"] != "PASS":
        raise CertificationError("verified live scope lost mutation eligibility", 4)

    empty_writeback = {"operations": [], "retryMode": "VERIFY_THEN_SKIP"}
    for boundary in ("FIXTURE", "UNAVAILABLE", "UNRECOGNIZED_BOUNDARY"):
        non_live_context = json.loads(json.dumps(context))
        non_live_context["evidenceBoundary"] = boundary
        non_live_risk = run_risk(
            request,
            non_live_context,
            impact,
            policy,
            now,
            raw_evidence,
        )
        non_live_scope = run_scope(
            request,
            non_live_context,
            impact,
            non_live_risk,
            artifacts,
            str(scope_root),
            descriptor,
            preflight,
            inventory_payload,
            bindings,
            raw_evidence,
            empty_writeback,
            policy,
            now,
        )
        if (
            non_live_scope["mutationEligibility"]["state"] != "NOT_RUN"
            or non_live_scope["plannedMutations"]["operations"]
        ):
            raise CertificationError(
                "non-live or unknown boundary became mutation eligible", 4
            )
        must_reject(
            lambda non_live_context=non_live_context, non_live_risk=non_live_risk: (
                run_scope(
                    request,
                    non_live_context,
                    impact,
                    non_live_risk,
                    artifacts,
                    str(scope_root),
                    descriptor,
                    preflight,
                    inventory_payload,
                    bindings,
                    raw_evidence,
                    writeback,
                    policy,
                    now,
                )
            ),
            f"mutation plan under {boundary} boundary",
        )

    forged_risk = json.loads(json.dumps(risk))
    forged_risk["score"] = 0
    forged_risk_body = {
        key: value for key, value in forged_risk.items() if key != "riskHash"
    }
    forged_risk["riskHash"] = digest(forged_risk_body)
    must_reject(
        lambda: run_scope(
            request,
            context,
            impact,
            forged_risk,
            artifacts,
            str(scope_root),
            descriptor,
            preflight,
            inventory_payload,
            bindings,
            raw_evidence,
            writeback,
            policy,
            now,
        ),
        "self-consistently forged risk",
    )
    forged_preflight = json.loads(json.dumps(preflight))
    forged_preflight["permittedMutationTools"] = []
    forged_preflight["toolInventoryHash"] = digest({"forged": True})
    must_reject(
        lambda: run_scope(
            request,
            context,
            impact,
            risk,
            artifacts,
            str(scope_root),
            descriptor,
            forged_preflight,
            inventory_payload,
            bindings,
            raw_evidence,
            writeback,
            policy,
            now,
        ),
        "caller-forged preflight result",
    )
    forged_artifacts = json.loads(json.dumps(artifacts))
    forged_artifacts["summary"] = "Caller-forged artifact summary."
    forged_artifact_body = {
        key: value
        for key, value in forged_artifacts.items()
        if key != "artifactManifestHash"
    }
    forged_artifacts["artifactManifestHash"] = digest(forged_artifact_body)
    must_reject(
        lambda: run_scope(
            request,
            context,
            impact,
            risk,
            forged_artifacts,
            str(scope_root),
            descriptor,
            preflight,
            inventory_payload,
            bindings,
            raw_evidence,
            writeback,
            policy,
            now,
        ),
        "self-consistently forged artifact result",
    )
    original_model = (scope_root / "model.sql").read_text(encoding="utf-8")
    (scope_root / "model.sql").write_text(
        original_model + "-- unapproved content drift\n", encoding="utf-8"
    )
    must_reject(
        lambda: run_scope(
            request,
            context,
            impact,
            risk,
            artifacts,
            str(scope_root),
            descriptor,
            preflight,
            inventory_payload,
            bindings,
            raw_evidence,
            writeback,
            policy,
            now,
        ),
        "artifact file drift after manifest generation",
    )
    (scope_root / "model.sql").write_text(original_model, encoding="utf-8")
    extra_argument_plan = json.loads(json.dumps(writeback))
    extra_argument_plan["operations"][0]["arguments"]["unexpected"] = True
    must_reject(
        lambda: run_scope(
            request,
            context,
            impact,
            risk,
            artifacts,
            str(scope_root),
            descriptor,
            preflight,
            inventory_payload,
            bindings,
            raw_evidence,
            extra_argument_plan,
            policy,
            now,
        ),
        "write-back arguments outside the approved template",
    )
    template_drift_plan = json.loads(json.dumps(writeback))
    template_drift_plan["operations"][0]["arguments"]["title"] = (
        "Unapproved passport title ${PASSPORT_ID}"
    )
    must_reject(
        lambda: run_scope(
            request,
            context,
            impact,
            risk,
            artifacts,
            str(scope_root),
            descriptor,
            preflight,
            inventory_payload,
            bindings,
            raw_evidence,
            template_drift_plan,
            policy,
            now,
        ),
        "write-back template drift",
    )
    secret_descriptor = json.loads(json.dumps(descriptor))
    secret_descriptor["summary"] = credential_samples[1]
    must_reject(
        lambda: run_artifact_validation(str(scope_root), secret_descriptor),
        "credential in artifact summary",
        credential_samples[1],
    )
    original_brief = (scope_root / "owners.md").read_text(encoding="utf-8")
    (scope_root / "owners.md").write_text(credential_samples[2], encoding="utf-8")
    must_reject(
        lambda: run_artifact_validation(str(scope_root), descriptor),
        "credential in generated artifact content",
        credential_samples[2],
    )
    (scope_root / "owners.md").write_text(original_brief, encoding="utf-8")
    approval = {
        "decision": "APPROVE",
        "reviewer": "self-test-reviewer",
        "note": "Approve the exact scope hash.",
        "scopeHash": scope["scopeHash"],
        "scopeAccepted": True,
        "decidedAt": isoformat(now),
    }
    secret_approval = {**approval, "note": credential_samples[3]}
    must_reject(
        lambda: run_passport(scope, secret_approval, policy, now),
        "credential in approval note",
        credential_samples[3],
    )
    passport = run_passport(scope, approval, policy, now)
    secret_passport = json.loads(json.dumps(passport))
    secret_passport["approval"]["note"] = credential_samples[4]
    secret_verification = run_verify_passport(secret_passport, policy, now)
    if (
        secret_verification["valid"]
        or secret_verification["manifestHash"] is not None
        or credential_samples[4] in json.dumps(secret_verification)
    ):
        raise CertificationError(
            "passport verification hashed or echoed credential content", 4
        )
    unbound_approval = {**approval, "scopeHash": "0" * 64}
    must_reject(
        lambda: run_passport(scope, unbound_approval, policy, now),
        "approval bound to another scope",
    )
    verification = run_verify_passport(passport, policy, now)
    if not verification["valid"]:
        raise CertificationError("passport self-test failed", 4)
    if run_verify_passport(passport, policy, now + timedelta(hours=25))["valid"]:
        raise CertificationError("expired passport passed verification", 4)
    tampered = json.loads(json.dumps(passport))
    tampered["scope"]["targetUrn"] = "urn:li:dataset:tampered"
    if run_verify_passport(tampered, policy, now)["valid"]:
        raise CertificationError("tampered passport passed verification", 4)
    scope_temporary.cleanup()
    return {
        "state": "PASS",
        "checks": [
            "canonical hashing",
            "tool and property preflight",
            "deterministic risk",
            "complete target, schema, and lineage evidence",
            "live raw evidence and query provenance",
            "successful inspected zero-query evidence",
            "live-boundary mutation whitelist",
            "artifact structural validation",
            "forged-risk rejection",
            "forged preflight and artifact rejection",
            "exact write-back templates",
            "credential value rejection without echo",
            "scope-bound approval",
            "passport verification",
            "passport expiry rejection",
            "tamper rejection",
        ],
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Deterministic DataHub schema-change certification helpers."
    )
    result.add_argument(
        "--policy", default=str(DEFAULT_POLICY), help="Versioned policy JSON path."
    )
    subcommands = result.add_subparsers(dest="command", required=True)

    preflight = subcommands.add_parser(
        "preflight", help="Validate captured MCP tool schemas and property bindings."
    )
    preflight.add_argument(
        "--inventory", required=True, help="Captured MCP tools/list envelope JSON."
    )
    preflight.add_argument(
        "--property-bindings",
        help="Optional role-to-structured-property binding JSON.",
    )

    risk = subcommands.add_parser(
        "evaluate-risk", help="Calculate versioned deterministic risk."
    )
    risk.add_argument("--request", required=True)
    risk.add_argument("--context", required=True)
    risk.add_argument("--impact", required=True)
    risk.add_argument(
        "--raw-evidence",
        help="Private raw MCP call evidence JSON; required by a live boundary.",
    )
    risk.add_argument("--now", help="ISO 8601 clock override for reproducible runs.")

    artifacts = subcommands.add_parser(
        "validate-artifacts",
        help="Validate generated dbt package structure and hashes.",
    )
    artifacts.add_argument("--root", required=True, help="Artifact root directory.")
    artifacts.add_argument(
        "--descriptor", required=True, help="Package descriptor JSON."
    )

    scope = subcommands.add_parser(
        "build-scope",
        help="Bind evidence, artifacts, preflight, and mutations for approval.",
    )
    for name in (
        "request",
        "context",
        "impact",
        "risk",
        "artifacts",
        "preflight",
        "writeback-plan",
    ):
        scope.add_argument(f"--{name}", required=True)
    scope.add_argument("--artifact-root", required=True)
    scope.add_argument("--artifact-descriptor", required=True)
    scope.add_argument("--tool-inventory", required=True)
    scope.add_argument("--property-bindings")
    scope.add_argument(
        "--raw-evidence",
        help="Private raw MCP call evidence JSON; required by a live boundary.",
    )
    scope.add_argument("--now", help="ISO 8601 clock override.")

    passport = subcommands.add_parser(
        "build-passport", help="Create a scope-bound decision passport."
    )
    passport.add_argument("--scope", required=True)
    passport.add_argument("--approval", required=True)
    passport.add_argument("--now", help="ISO 8601 clock override.")

    verify = subcommands.add_parser(
        "verify-passport", help="Recompute and verify a passport before write-back."
    )
    verify.add_argument("--passport", required=True)
    verify.add_argument("--now", help="ISO 8601 clock override.")

    subcommands.add_parser(
        "self-test", help="Run deterministic in-process contract tests."
    )
    return result


def main() -> int:
    arguments = parser().parse_args()
    try:
        policy = load_policy(arguments.policy)
        if arguments.command == "preflight":
            result = run_preflight(
                read_json(arguments.inventory),
                read_json(arguments.property_bindings)
                if arguments.property_bindings
                else None,
                policy,
            )
        elif arguments.command == "evaluate-risk":
            result = run_risk(
                require_object(read_json(arguments.request), "request"),
                require_object(read_json(arguments.context), "context"),
                require_object(read_json(arguments.impact), "impact"),
                policy,
                current_time(arguments.now),
                read_json(arguments.raw_evidence) if arguments.raw_evidence else None,
            )
        elif arguments.command == "validate-artifacts":
            result = run_artifact_validation(
                arguments.root,
                require_object(read_json(arguments.descriptor), "descriptor"),
            )
        elif arguments.command == "build-scope":
            result = run_scope(
                require_object(read_json(arguments.request), "request"),
                require_object(read_json(arguments.context), "context"),
                require_object(read_json(arguments.impact), "impact"),
                require_object(read_json(arguments.risk), "risk"),
                require_object(read_json(arguments.artifacts), "artifacts"),
                arguments.artifact_root,
                require_object(
                    read_json(arguments.artifact_descriptor), "artifact descriptor"
                ),
                require_object(read_json(arguments.preflight), "preflight"),
                read_json(arguments.tool_inventory),
                read_json(arguments.property_bindings)
                if arguments.property_bindings
                else None,
                read_json(arguments.raw_evidence) if arguments.raw_evidence else None,
                require_object(read_json(arguments.writeback_plan), "writeback plan"),
                policy,
                current_time(arguments.now),
            )
        elif arguments.command == "build-passport":
            result = run_passport(
                require_object(read_json(arguments.scope), "scope"),
                require_object(read_json(arguments.approval), "approval"),
                policy,
                current_time(arguments.now),
            )
        elif arguments.command == "verify-passport":
            result = run_verify_passport(
                require_object(read_json(arguments.passport), "passport"),
                policy,
                current_time(arguments.now),
            )
            emit(result)
            return 0 if result["valid"] else 4
        else:
            result = self_test(policy)
        emit(result)
        return 0
    except CertificationError as error:
        emit({"state": "FAIL", "error": str(error), "exitCode": error.code})
        print(f"certify_change: {error}", file=sys.stderr)
        return error.code


if __name__ == "__main__":
    raise SystemExit(main())
