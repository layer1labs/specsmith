// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
//! Projection engine — gates all canonical state transitions (Invariant 1, 3, 4, 5).

use crate::dependency::DepGraph;
use crate::store::Store;
use crate::types::*;

/// Proposal submitted to the projection engine.
#[derive(Debug, Clone)]
pub struct Proposal {
    pub record: Record,
    pub sources: Vec<EsdbId>,
    pub assumed_deps: Vec<EsdbId>,
    pub is_destructive: bool,
    pub destructive_approved: bool,
}

/// Configuration for projection thresholds.
#[derive(Debug, Clone)]
pub struct ProjectionConfig {
    pub min_confidence: f64,
    pub require_source: bool,
    pub check_contradictions: bool,
    pub check_duplicates: bool,
    pub check_stale: bool,
}

impl Default for ProjectionConfig {
    fn default() -> Self {
        Self {
            min_confidence: 0.3,
            require_source: true,
            check_contradictions: true,
            check_duplicates: true,
            check_stale: true,
        }
    }
}

/// Run the projection engine on a proposal.
///
/// Returns a `ProjectionDecision` indicating whether the proposal is
/// accepted into canonical state or rejected.
pub fn project(
    proposal: &Proposal,
    store: &Store,
    dep_graph: &DepGraph,
    config: &ProjectionConfig,
) -> ProjectionDecision {
    // 1. Source support (Invariant 1: unsupported claims may never become fact)
    if config.require_source && proposal.sources.is_empty() {
        if proposal.record.kind == RecordKind::Fact {
            return ProjectionDecision::DowngradeToHypothesis {
                reason: "No source provided — facts require at least one source".into(),
            };
        }
    }

    // 2. Confidence threshold
    if proposal.record.confidence.value() < config.min_confidence {
        return ProjectionDecision::Reject {
            reason: format!(
                "Confidence {:.3} below minimum {:.3}",
                proposal.record.confidence.value(),
                config.min_confidence
            ),
        };
    }

    // 3. Contradiction detection (Invariant 5)
    if config.check_contradictions {
        let contradictions = dep_graph.what_contradicts(&proposal.record.id);
        let active_contradictions: Vec<_> = contradictions
            .iter()
            .filter(|id| store.get(id).map_or(false, |r| r.is_active()))
            .collect();
        if !active_contradictions.is_empty() {
            return ProjectionDecision::Reject {
                reason: format!(
                    "Contradicts {} active record(s)",
                    active_contradictions.len()
                ),
            };
        }
    }

    // 4. Stale-state detection (Invariant 4)
    if config.check_stale {
        let existing = store.query_active(proposal.record.kind);
        for existing_rec in &existing {
            if existing_rec.label == proposal.record.label
                && existing_rec.modified_at > proposal.record.created_at
            {
                return ProjectionDecision::Reject {
                    reason: "Fresher canonical state already exists".into(),
                };
            }
        }
    }

    // 5. Duplicate-work detection (Invariant 3)
    if config.check_duplicates
        && matches!(
            proposal.record.kind,
            RecordKind::Action | RecordKind::WorkItem | RecordKind::SkillRun
        )
    {
        let existing = store.query_active(proposal.record.kind);
        for existing_rec in &existing {
            if existing_rec.label == proposal.record.label {
                return ProjectionDecision::Reject {
                    reason: "Equivalent work already completed".into(),
                };
            }
        }
    }

    // 6. Dependency validity — all assumed deps must still be active
    for dep_id in &proposal.assumed_deps {
        if let Some(dep_record) = store.get(dep_id) {
            if !dep_record.is_active() {
                return ProjectionDecision::Reject {
                    reason: format!("Assumed dependency {} is no longer active", dep_id),
                };
            }
        }
    }

    // 7. Destructive action gate (Invariant 6)
    if proposal.is_destructive && !proposal.destructive_approved {
        return ProjectionDecision::Stop {
            reason: "Destructive action requires explicit approval".into(),
        };
    }

    ProjectionDecision::Accept
}
