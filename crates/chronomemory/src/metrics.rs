// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
//! Token metrics and optimizer (§19, §20 of spec).

use crate::types::*;

/// Aggregated metrics across all tasks.
#[derive(Debug, Clone, Default)]
pub struct AggregateMetrics {
    pub total_tasks: u64,
    pub successful_tasks: u64,
    pub total_tokens: u64,
    pub total_context_tokens: u64,
    pub total_duplicates_blocked: u64,
    pub total_claims_rejected: u64,
}

impl AggregateMetrics {
    /// Primary optimization metric: minimum verified tokens per successful task.
    pub fn tokens_per_success(&self) -> f64 {
        if self.successful_tasks == 0 {
            return f64::INFINITY;
        }
        self.total_tokens as f64 / self.successful_tasks as f64
    }

    /// Context pack cache effectiveness.
    pub fn context_efficiency(&self) -> f64 {
        if self.total_tokens == 0 {
            return 0.0;
        }
        self.total_context_tokens as f64 / self.total_tokens as f64
    }

    /// Duplicate prevention rate.
    pub fn duplicate_prevention_rate(&self) -> f64 {
        if self.total_tasks == 0 {
            return 0.0;
        }
        self.total_duplicates_blocked as f64 / self.total_tasks as f64
    }

    /// Record a completed task metric.
    pub fn record(&mut self, metric: &TokenMetricData) {
        self.total_tasks += 1;
        if metric.success {
            self.successful_tasks += 1;
        }
        self.total_tokens += metric.input_tokens + metric.output_tokens;
        self.total_context_tokens += metric.context_tokens;
        self.total_duplicates_blocked += metric.duplicates_blocked as u64;
        self.total_claims_rejected += metric.claims_rejected as u64;
    }

    /// Serialize to JSON for the REST API.
    pub fn to_json(&self) -> serde_json::Value {
        serde_json::json!({
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "total_tokens": self.total_tokens,
            "tokens_per_success": self.tokens_per_success(),
            "context_efficiency": self.context_efficiency(),
            "duplicate_prevention_rate": self.duplicate_prevention_rate(),
            "total_duplicates_blocked": self.total_duplicates_blocked,
            "total_claims_rejected": self.total_claims_rejected,
        })
    }
}
