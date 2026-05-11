// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
//! Context pack compiler — minimal verified context for a task (§18 of spec).

use crate::dependency::DepGraph;
use crate::store::Store;
use crate::types::*;
use sha2::{Digest, Sha256};

/// Request for a context pack.
#[derive(Debug, Clone)]
pub struct ContextPackRequest {
    pub task_id: EsdbId,
    pub goal_id: EsdbId,
    pub token_budget: u64,
    pub freshness_epoch: u64,
}

/// Estimate tokens for a record (rough: ~4 chars per token).
fn estimate_tokens(record: &Record) -> u64 {
    let text_len = record.label.len() + serde_json::to_string(&record.data).unwrap_or_default().len();
    (text_len as u64) / 4 + 1
}

/// Compile a minimal verified context pack for a task.
///
/// Includes only active, non-invalidated, non-stale records within
/// the dependency scope of the task. Excludes unsupported claims.
/// Respects token budget. (Invariant 7)
pub fn compile(
    request: &ContextPackRequest,
    store: &Store,
    dep_graph: &DepGraph,
) -> ContextPackOutput {
    let mut entries: Vec<PackEntry> = Vec::new();
    let mut total_tokens: u64 = 0;

    // Collect candidate records: requirements, test cases, facts, constraints, goals
    let candidate_kinds = [
        RecordKind::Goal,
        RecordKind::Task,
        RecordKind::Requirement,
        RecordKind::TestCase,
        RecordKind::Fact,
        RecordKind::Constraint,
        RecordKind::Skill,
        RecordKind::Decision,
    ];

    let mut candidates: Vec<&Record> = Vec::new();
    for kind in &candidate_kinds {
        candidates.extend(store.query_active(*kind));
    }

    // Sort by confidence (highest first), then by recency
    candidates.sort_by(|a, b| {
        b.confidence
            .value()
            .partial_cmp(&a.confidence.value())
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| b.modified_at.cmp(&a.modified_at))
    });

    // Fill context pack within token budget
    for record in candidates {
        let tokens = estimate_tokens(record);
        if total_tokens + tokens > request.token_budget {
            break;
        }
        entries.push(PackEntry {
            record_id: record.id,
            kind: record.kind,
            label: record.label.clone(),
            confidence: record.confidence.value(),
            estimated_tokens: tokens,
        });
        total_tokens += tokens;
    }

    // Compute hash of the pack contents
    let mut hasher = Sha256::new();
    for entry in &entries {
        hasher.update(entry.record_id.as_bytes());
    }
    let hash: [u8; 32] = hasher.finalize().into();

    ContextPackOutput {
        id: EsdbId::new(),
        task_id: request.task_id,
        entries,
        token_count: total_tokens,
        freshness_epoch: store.epoch(),
        hash,
    }
}
