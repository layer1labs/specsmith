// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
//! Dependency graph engine — tracks epistemic relationships (§13 of spec).

use crate::types::*;
use std::collections::{HashMap, HashSet};

/// In-memory directed graph of epistemic dependencies.
#[derive(Debug, Default)]
pub struct DepGraph {
    /// Forward edges: from -> [(to, edge_type)]
    forward: HashMap<EsdbId, Vec<(EsdbId, EdgeType)>>,
    /// Reverse edges: to -> [(from, edge_type)]
    reverse: HashMap<EsdbId, Vec<(EsdbId, EdgeType)>>,
}

impl DepGraph {
    pub fn new() -> Self {
        Self::default()
    }

    /// Add a dependency edge.
    pub fn add_edge(&mut self, from: EsdbId, to: EsdbId, edge_type: EdgeType) {
        self.forward
            .entry(from)
            .or_default()
            .push((to, edge_type));
        self.reverse
            .entry(to)
            .or_default()
            .push((from, edge_type));
    }

    /// What does `id` depend on? (upstream dependencies)
    pub fn what_does_it_depend_on(&self, id: &EsdbId) -> Vec<EsdbId> {
        self.forward
            .get(id)
            .map(|edges| {
                edges
                    .iter()
                    .filter(|(_, et)| matches!(et, EdgeType::DependsOn | EdgeType::Assumes | EdgeType::DerivedFrom))
                    .map(|(to, _)| *to)
                    .collect()
            })
            .unwrap_or_default()
    }

    /// What depends on `id`? (downstream dependents)
    pub fn what_depends_on(&self, id: &EsdbId) -> Vec<EsdbId> {
        self.reverse
            .get(id)
            .map(|edges| {
                edges
                    .iter()
                    .filter(|(_, et)| matches!(et, EdgeType::DependsOn | EdgeType::Assumes | EdgeType::DerivedFrom))
                    .map(|(from, _)| *from)
                    .collect()
            })
            .unwrap_or_default()
    }

    /// What contradicts `id`?
    pub fn what_contradicts(&self, id: &EsdbId) -> Vec<EsdbId> {
        let mut result = Vec::new();
        if let Some(edges) = self.forward.get(id) {
            for (to, et) in edges {
                if *et == EdgeType::Contradicts {
                    result.push(*to);
                }
            }
        }
        if let Some(edges) = self.reverse.get(id) {
            for (from, et) in edges {
                if *et == EdgeType::Contradicts {
                    result.push(*from);
                }
            }
        }
        result
    }

    /// What assumptions underlie `id`?
    pub fn what_assumes(&self, id: &EsdbId) -> Vec<EsdbId> {
        self.forward
            .get(id)
            .map(|edges| {
                edges
                    .iter()
                    .filter(|(_, et)| *et == EdgeType::Assumes)
                    .map(|(to, _)| *to)
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Transitive downstream closure — all records that transitively depend on `id`.
    pub fn transitive_dependents(&self, id: &EsdbId) -> HashSet<EsdbId> {
        let mut visited = HashSet::new();
        let mut stack = vec![*id];
        while let Some(current) = stack.pop() {
            if !visited.insert(current) {
                continue;
            }
            for dep in self.what_depends_on(&current) {
                if !visited.contains(&dep) {
                    stack.push(dep);
                }
            }
        }
        visited.remove(id); // don't include the root itself
        visited
    }

    /// Total edge count.
    pub fn edge_count(&self) -> usize {
        self.forward.values().map(|v| v.len()).sum()
    }

    /// Clear all edges (used for replay from genesis).
    pub fn clear(&mut self) {
        self.forward.clear();
        self.reverse.clear();
    }
}
