// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
//! Replay engine — deterministic state reconstruction from WAL (Invariant 8).

use crate::dependency::DepGraph;
use crate::store::Store;
use crate::types::*;
use crate::wal::{EventType, WalEntry, WalReader};

/// Replay result.
#[derive(Debug)]
pub struct ReplayResult {
    pub entries_replayed: u64,
    pub records_materialized: usize,
    pub edges_rebuilt: usize,
    pub chain_valid: bool,
}

/// Replay all WAL entries into a fresh store + dependency graph.
///
/// Determinism guarantee: same WAL → identical materialized state.
pub fn replay_full(
    entries: &[WalEntry],
    store: &mut Store,
    dep_graph: &mut DepGraph,
) -> ReplayResult {
    store.clear();
    dep_graph.clear();

    let mut count = 0u64;

    for entry in entries {
        match entry.event_type {
            EventType::Insert => {
                if let Ok(record) = bincode::deserialize::<Record>(&entry.payload) {
                    store.upsert(record);
                }
            }
            EventType::Modify => {
                if let Ok(record) = bincode::deserialize::<Record>(&entry.payload) {
                    store.upsert(record);
                }
            }
            EventType::Invalidate => {
                store.invalidate(&entry.record_id);
            }
            EventType::Tombstone => {
                if let Some(record) = store.get_mut(&entry.record_id) {
                    record.status = RecordStatus::Tombstoned;
                }
            }
            EventType::AddEdge => {
                if let Ok(edge) = bincode::deserialize::<DepEdge>(&entry.payload) {
                    dep_graph.add_edge(edge.from, edge.to, edge.edge_type);
                }
            }
            EventType::Rollback => {
                // Rollback entries are informational — the individual
                // Invalidate events handle the actual state changes.
            }
            EventType::Checkpoint | EventType::RecordMetric => {
                // Checkpoints and metrics don't affect materialized state.
            }
        }
        count += 1;
    }

    ReplayResult {
        entries_replayed: count,
        records_materialized: store.count_total(),
        edges_rebuilt: dep_graph.edge_count(),
        chain_valid: true, // caller should verify separately
    }
}

/// Verify replay integrity: replay from WAL file and compare chain.
pub fn verify_replay(wal_path: &str) -> Result<ReplayResult, crate::wal::WalError> {
    let reader = WalReader::open(wal_path)?;
    let chain_valid = reader.verify_chain()?;
    let entries = reader.read_all()?;

    let mut store = Store::new();
    let mut dep_graph = DepGraph::new();
    let mut result = replay_full(&entries, &mut store, &mut dep_graph);
    result.chain_valid = chain_valid;
    Ok(result)
}
