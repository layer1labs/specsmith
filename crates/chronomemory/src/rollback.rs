// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
//! Rollback engine — dependency-aware cascade invalidation (Invariant 2, 9).

use crate::dependency::DepGraph;
use crate::store::Store;
use crate::types::*;

/// Result of a rollback operation.
#[derive(Debug, Clone)]
pub struct RollbackResult {
    pub root_id: EsdbId,
    pub reason: String,
    pub invalidated_ids: Vec<EsdbId>,
    pub confidence_degraded: Vec<(EsdbId, f64, f64)>, // (id, old, new)
}

/// Confidence decay factor per edge distance from rollback root.
const CONFIDENCE_DECAY_PER_HOP: f64 = 0.85;

/// Execute a rollback: invalidate `root_id` and cascade to all transitive dependents.
///
/// Invariant 2: records are marked Invalidated, never deleted.
/// Invariant 9: all removals create replay-visible tombstones (via WAL).
pub fn rollback(
    root_id: &EsdbId,
    reason: &str,
    store: &mut Store,
    dep_graph: &DepGraph,
) -> RollbackResult {
    let mut invalidated = Vec::new();
    let mut degraded = Vec::new();

    // Mark root as invalidated
    if store.invalidate(root_id) {
        invalidated.push(*root_id);
    }

    // Cascade to transitive dependents
    let dependents = dep_graph.transitive_dependents(root_id);
    for dep_id in &dependents {
        if store.invalidate(dep_id) {
            invalidated.push(*dep_id);
        }

        // Degrade confidence on dependent records
        if let Some(record) = store.get_mut(dep_id) {
            let old_conf = record.confidence.value();
            // Decay proportional to graph distance (simplified: uniform decay)
            let new_conf = old_conf * CONFIDENCE_DECAY_PER_HOP;
            record.confidence = Confidence::new(new_conf);
            degraded.push((*dep_id, old_conf, new_conf));
        }
    }

    RollbackResult {
        root_id: *root_id,
        reason: reason.to_owned(),
        invalidated_ids: invalidated,
        confidence_degraded: degraded,
    }
}
