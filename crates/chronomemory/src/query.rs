// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
//! Semantic query API (§23 of spec).

use crate::dependency::DepGraph;
use crate::store::Store;
use crate::types::*;

/// Query: what is known about an entity (by label substring)?
pub fn what_is_known<'a>(store: &'a Store, entity: &str) -> Vec<&'a Record> {
    let lower = entity.to_lowercase();
    let all_kinds = [
        RecordKind::Fact,
        RecordKind::Requirement,
        RecordKind::TestCase,
        RecordKind::Decision,
        RecordKind::Constraint,
        RecordKind::Observation,
    ];
    let mut results = Vec::new();
    for kind in &all_kinds {
        for record in store.query_active(*kind) {
            if record.label.to_lowercase().contains(&lower) {
                results.push(record);
            }
        }
    }
    results
}

/// Query: what conflicts with a record?
pub fn what_conflicts_with<'a>(id: &EsdbId, store: &'a Store, dep_graph: &DepGraph) -> Vec<&'a Record> {
    dep_graph
        .what_contradicts(id)
        .iter()
        .filter_map(|cid| store.get(cid))
        .filter(|r| r.is_active())
        .collect()
}

/// Query: what depends on a record (downstream)?
pub fn what_depends_on<'a>(id: &EsdbId, store: &'a Store, dep_graph: &DepGraph) -> Vec<&'a Record> {
    dep_graph
        .what_depends_on(id)
        .iter()
        .filter_map(|did| store.get(did))
        .filter(|r| r.is_active())
        .collect()
}

/// Query: has this work been done? (duplicate check by label)
pub fn has_this_work_been_done(store: &Store, label: &str) -> bool {
    let work_kinds = [RecordKind::Action, RecordKind::WorkItem, RecordKind::SkillRun];
    for kind in &work_kinds {
        for record in store.query_active(*kind) {
            if record.label == label {
                return true;
            }
        }
    }
    false
}

/// Query: what changed since a given epoch?
pub fn what_changed_since<'a>(store: &'a Store, _epoch: u64) -> Vec<&'a Record> {
    // Since we don't store epoch per record, approximate by checking
    // all records with modified_at after a threshold. For now return
    // all active records (the real implementation would track per-record epoch).
    let all_kinds = [
        RecordKind::Fact,
        RecordKind::Requirement,
        RecordKind::TestCase,
        RecordKind::WorkItem,
        RecordKind::Decision,
    ];
    let mut results = Vec::new();
    for kind in &all_kinds {
        results.extend(store.query_active(*kind));
    }
    results
}

/// Query: what requires re-verification?
pub fn what_requires_reverification<'a>(store: &'a Store) -> Vec<&'a Record> {
    store
        .query_all(RecordKind::WorkItem)
        .into_iter()
        .filter(|r| r.status == RecordStatus::Invalidated)
        .collect()
}

/// Query: record counts by kind (for dashboard).
pub fn record_counts(store: &Store) -> Vec<(RecordKind, usize, usize)> {
    let kinds = [
        RecordKind::Fact,
        RecordKind::Hypothesis,
        RecordKind::Requirement,
        RecordKind::TestCase,
        RecordKind::WorkItem,
        RecordKind::Goal,
        RecordKind::Task,
        RecordKind::Skill,
        RecordKind::Action,
        RecordKind::Decision,
        RecordKind::Constraint,
    ];
    kinds
        .iter()
        .map(|k| (*k, store.count_active(*k), store.query_all(*k).len()))
        .collect()
}
