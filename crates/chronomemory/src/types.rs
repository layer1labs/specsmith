// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
//! Core ESDB types — record types, IDs, status, and epistemic primitives.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Deterministic ID
// ---------------------------------------------------------------------------

/// 128-bit deterministic ID for all ESDB records.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub struct EsdbId(pub Uuid);

impl EsdbId {
    pub fn new() -> Self {
        Self(Uuid::new_v4())
    }

    pub fn from_bytes(bytes: [u8; 16]) -> Self {
        Self(Uuid::from_bytes(bytes))
    }

    pub fn nil() -> Self {
        Self(Uuid::nil())
    }

    pub fn as_bytes(&self) -> &[u8; 16] {
        self.0.as_bytes()
    }
}

impl Default for EsdbId {
    fn default() -> Self {
        Self::new()
    }
}

impl std::fmt::Display for EsdbId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

// ---------------------------------------------------------------------------
// Record status (Invariant 2: no silent disappearance)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum RecordStatus {
    Active,
    Superseded,
    Archived,
    Invalidated,
    Tombstoned,
}

impl Default for RecordStatus {
    fn default() -> Self {
        Self::Active
    }
}

// ---------------------------------------------------------------------------
// Confidence
// ---------------------------------------------------------------------------

/// Epistemic confidence score (0.0–1.0).
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct Confidence(pub f64);

impl Confidence {
    pub fn new(val: f64) -> Self {
        Self(val.clamp(0.0, 1.0))
    }

    pub fn value(&self) -> f64 {
        self.0
    }

    pub fn decay(&self, factor: f64) -> Self {
        Self::new(self.0 * factor)
    }
}

impl Default for Confidence {
    fn default() -> Self {
        Self(0.7)
    }
}

// ---------------------------------------------------------------------------
// Dependency edge types
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EdgeType {
    DependsOn,
    DerivedFrom,
    ValidatedBy,
    GeneratedFrom,
    Assumes,
    Contradicts,
    Supports,
    Supersedes,
    Invalidates,
}

// ---------------------------------------------------------------------------
// Record type discriminator
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub enum RecordKind {
    Fact,
    Hypothesis,
    Claim,
    Belief,
    Source,
    Evidence,
    Goal,
    Task,
    Requirement,
    TestCase,
    WorkItem,
    Decision,
    Constraint,
    Skill,
    SkillRun,
    Action,
    Observation,
    WorldState,
    StateDelta,
    DependencyEdge,
    ContextPack,
    TokenMetric,
    StopCondition,
    RollbackEvent,
    StateEpoch,
}

// ---------------------------------------------------------------------------
// Universal record envelope
// ---------------------------------------------------------------------------

/// Every ESDB record is wrapped in this envelope for uniform storage.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Record {
    pub id: EsdbId,
    pub kind: RecordKind,
    pub status: RecordStatus,
    pub confidence: Confidence,
    pub created_at: DateTime<Utc>,
    pub modified_at: DateTime<Utc>,
    pub source_ids: Vec<EsdbId>,
    /// Human-readable label (requirement title, fact statement, etc.)
    pub label: String,
    /// Free-form JSON payload for kind-specific data.
    pub data: serde_json::Value,
}

impl Record {
    pub fn new(kind: RecordKind, label: impl Into<String>) -> Self {
        let now = Utc::now();
        Self {
            id: EsdbId::new(),
            kind,
            status: RecordStatus::Active,
            confidence: Confidence::default(),
            created_at: now,
            modified_at: now,
            source_ids: Vec::new(),
            label: label.into(),
            data: serde_json::Value::Null,
        }
    }

    pub fn with_confidence(mut self, c: f64) -> Self {
        self.confidence = Confidence::new(c);
        self
    }

    pub fn with_sources(mut self, sources: Vec<EsdbId>) -> Self {
        self.source_ids = sources;
        self
    }

    pub fn with_data(mut self, data: serde_json::Value) -> Self {
        self.data = data;
        self
    }

    pub fn is_active(&self) -> bool {
        self.status == RecordStatus::Active
    }
}

// ---------------------------------------------------------------------------
// Dependency edge record
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DepEdge {
    pub from: EsdbId,
    pub to: EsdbId,
    pub edge_type: EdgeType,
    pub confidence: Confidence,
    pub created_at: DateTime<Utc>,
}

// ---------------------------------------------------------------------------
// Context pack output
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextPackOutput {
    pub id: EsdbId,
    pub task_id: EsdbId,
    pub entries: Vec<PackEntry>,
    pub token_count: u64,
    pub freshness_epoch: u64,
    pub hash: [u8; 32],
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackEntry {
    pub record_id: EsdbId,
    pub kind: RecordKind,
    pub label: String,
    pub confidence: f64,
    pub estimated_tokens: u64,
}

// ---------------------------------------------------------------------------
// Token metrics
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenMetricData {
    pub task_id: EsdbId,
    pub context_tokens: u64,
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub tool_calls: u32,
    pub elapsed_ms: u64,
    pub success: bool,
    pub duplicates_blocked: u32,
    pub claims_rejected: u32,
}

// ---------------------------------------------------------------------------
// Projection decision
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProjectionDecision {
    Accept,
    Reject { reason: String },
    DowngradeToHypothesis { reason: String },
    RequestClarification { question: String },
    Stop { reason: String },
}

impl ProjectionDecision {
    pub fn is_accepted(&self) -> bool {
        matches!(self, Self::Accept)
    }
}

// ---------------------------------------------------------------------------
// Stop condition
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StopConditionData {
    pub kind: String,
    pub triggered: bool,
    pub reason: String,
    pub threshold: f64,
    pub current_value: f64,
}
