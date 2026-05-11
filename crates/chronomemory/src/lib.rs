// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
//! ChronoMemory ESDB — Epistemic State Database engine.
//!
//! "A governed epistemic cognition substrate for autonomous intelligence."

pub mod context_pack;
pub mod dependency;
pub mod metrics;
pub mod projection;
pub mod query;
pub mod replay;
pub mod rollback;
pub mod store;
pub mod types;
pub mod wal;

use dependency::DepGraph;
use metrics::AggregateMetrics;
use projection::{Proposal, ProjectionConfig};
use store::Store;
use types::*;
use wal::{EventType, WalWriter};

use std::path::{Path, PathBuf};

/// Top-level ESDB handle.
pub struct Esdb {
    wal: WalWriter,
    pub store: Store,
    pub dep_graph: DepGraph,
    pub metrics: AggregateMetrics,
    pub projection_config: ProjectionConfig,
    path: PathBuf,
}

impl Esdb {
    /// Open or create an ESDB at the given directory.
    pub fn open(dir: impl AsRef<Path>) -> Result<Self, EsdbError> {
        let dir = dir.as_ref();
        std::fs::create_dir_all(dir).map_err(EsdbError::Io)?;

        let wal_path = dir.join("events.wal");

        let mut store = Store::new();
        let mut dep_graph = DepGraph::new();

        // Replay WAL to rebuild materialized state BEFORE opening writer
        // (writer also reads WAL to find last seq, but doesn't replay).
        if wal_path.exists() {
            let reader = wal::WalReader::open(&wal_path).map_err(EsdbError::Wal)?;
            let entries = reader.read_all().map_err(EsdbError::Wal)?;
            replay::replay_full(&entries, &mut store, &mut dep_graph);
        }

        let wal = WalWriter::open(&wal_path).map_err(EsdbError::Wal)?;

        Ok(Self {
            wal,
            store,
            dep_graph,
            metrics: AggregateMetrics::default(),
            projection_config: ProjectionConfig::default(),
            path: dir.to_path_buf(),
        })
    }

    /// Project a proposal through the projection engine.
    pub fn project(&self, proposal: &Proposal) -> ProjectionDecision {
        projection::project(proposal, &self.store, &self.dep_graph, &self.projection_config)
    }

    /// Commit an accepted record to the ESDB (WAL + materialized state).
    pub fn commit(&mut self, record: Record) -> Result<EsdbId, EsdbError> {
        let id = record.id;
        let payload = bincode::serialize(&record).map_err(EsdbError::Serialize)?;
        self.wal
            .append(EventType::Insert, id, &payload)
            .map_err(EsdbError::Wal)?;
        self.store.upsert(record);
        Ok(id)
    }

    /// Add a dependency edge.
    pub fn add_edge(
        &mut self,
        from: EsdbId,
        to: EsdbId,
        edge_type: EdgeType,
    ) -> Result<(), EsdbError> {
        let edge = DepEdge {
            from,
            to,
            edge_type,
            confidence: Confidence::default(),
            created_at: chrono::Utc::now(),
        };
        let payload = bincode::serialize(&edge).map_err(EsdbError::Serialize)?;
        self.wal
            .append(EventType::AddEdge, from, &payload)
            .map_err(EsdbError::Wal)?;
        self.dep_graph.add_edge(from, to, edge_type);
        Ok(())
    }

    /// Execute a rollback with dependency-aware cascade.
    pub fn rollback(
        &mut self,
        id: &EsdbId,
        reason: &str,
    ) -> Result<rollback::RollbackResult, EsdbError> {
        let result = rollback::rollback(id, reason, &mut self.store, &self.dep_graph);

        // Write rollback event to WAL
        let payload = bincode::serialize(&result.invalidated_ids).map_err(EsdbError::Serialize)?;
        self.wal
            .append(EventType::Rollback, *id, &payload)
            .map_err(EsdbError::Wal)?;

        // Write individual invalidation events for each cascaded record
        for inv_id in &result.invalidated_ids {
            self.wal
                .append(EventType::Invalidate, *inv_id, &[])
                .map_err(EsdbError::Wal)?;
        }

        Ok(result)
    }

    /// Compile a minimal verified context pack for a task.
    pub fn context_pack(
        &self,
        request: &context_pack::ContextPackRequest,
    ) -> ContextPackOutput {
        context_pack::compile(request, &self.store, &self.dep_graph)
    }

    /// Record a token metric.
    pub fn record_metric(&mut self, metric: TokenMetricData) -> Result<(), EsdbError> {
        let payload = bincode::serialize(&metric).map_err(EsdbError::Serialize)?;
        self.wal
            .append(EventType::RecordMetric, metric.task_id, &payload)
            .map_err(EsdbError::Wal)?;
        self.metrics.record(&metric);
        Ok(())
    }

    /// Verify WAL chain integrity.
    pub fn verify_chain(&self) -> Result<bool, EsdbError> {
        let wal_path = self.path.join("events.wal");
        let reader = wal::WalReader::open(&wal_path).map_err(EsdbError::Wal)?;
        reader.verify_chain().map_err(EsdbError::Wal)
    }

    /// Get the current WAL sequence number.
    pub fn wal_seq(&self) -> u64 {
        self.wal.seq()
    }

    /// Get the store epoch.
    pub fn epoch(&self) -> u64 {
        self.store.epoch()
    }

    /// Get the ESDB directory path.
    pub fn path(&self) -> &Path {
        &self.path
    }
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

#[derive(Debug, thiserror::Error)]
pub enum EsdbError {
    #[error("IO error: {0}")]
    Io(std::io::Error),
    #[error("WAL error: {0}")]
    Wal(wal::WalError),
    #[error("Serialization error: {0}")]
    Serialize(bincode::Error),
}
