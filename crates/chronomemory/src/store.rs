// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
//! Materialized state store — in-memory state rebuilt from WAL.

use crate::types::*;
use std::collections::BTreeMap;

/// In-memory materialized state of the ESDB.
#[derive(Debug, Default)]
pub struct Store {
    records: BTreeMap<EsdbId, Record>,
    /// Index: kind -> set of record IDs
    by_kind: BTreeMap<RecordKind, Vec<EsdbId>>,
    /// Monotonic epoch counter (incremented on every mutation).
    epoch: u64,
}

impl Store {
    pub fn new() -> Self {
        Self::default()
    }

    /// Insert or replace a record in the materialized state.
    pub fn upsert(&mut self, record: Record) {
        let id = record.id;
        let kind = record.kind;
        self.records.insert(id, record);
        self.by_kind.entry(kind).or_default().push(id);
        self.epoch += 1;
    }

    /// Get a record by ID.
    pub fn get(&self, id: &EsdbId) -> Option<&Record> {
        self.records.get(id)
    }

    /// Get a mutable record by ID.
    pub fn get_mut(&mut self, id: &EsdbId) -> Option<&mut Record> {
        self.records.get_mut(id)
    }

    /// Query all active records of a given kind.
    pub fn query_active(&self, kind: RecordKind) -> Vec<&Record> {
        self.by_kind
            .get(&kind)
            .map(|ids| {
                ids.iter()
                    .filter_map(|id| self.records.get(id))
                    .filter(|r| r.is_active())
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Query all records of a given kind (any status).
    pub fn query_all(&self, kind: RecordKind) -> Vec<&Record> {
        self.by_kind
            .get(&kind)
            .map(|ids| ids.iter().filter_map(|id| self.records.get(id)).collect())
            .unwrap_or_default()
    }

    /// Query active records above a confidence threshold.
    pub fn query_above_confidence(&self, kind: RecordKind, min_confidence: f64) -> Vec<&Record> {
        self.query_active(kind)
            .into_iter()
            .filter(|r| r.confidence.value() >= min_confidence)
            .collect()
    }

    /// Count active records of a kind.
    pub fn count_active(&self, kind: RecordKind) -> usize {
        self.query_active(kind).len()
    }

    /// Count all records (any status).
    pub fn count_total(&self) -> usize {
        self.records.len()
    }

    /// Get the current epoch.
    pub fn epoch(&self) -> u64 {
        self.epoch
    }

    /// All record IDs.
    pub fn all_ids(&self) -> Vec<EsdbId> {
        self.records.keys().copied().collect()
    }

    /// Mark a record as invalidated (Invariant 2: never delete).
    pub fn invalidate(&mut self, id: &EsdbId) -> bool {
        if let Some(record) = self.records.get_mut(id) {
            record.status = RecordStatus::Invalidated;
            record.modified_at = chrono::Utc::now();
            self.epoch += 1;
            true
        } else {
            false
        }
    }

    /// Mark a record as superseded.
    pub fn supersede(&mut self, id: &EsdbId) -> bool {
        if let Some(record) = self.records.get_mut(id) {
            record.status = RecordStatus::Superseded;
            record.modified_at = chrono::Utc::now();
            self.epoch += 1;
            true
        } else {
            false
        }
    }

    /// Clear all state (used for replay from genesis).
    pub fn clear(&mut self) {
        self.records.clear();
        self.by_kind.clear();
        self.epoch = 0;
    }
}
