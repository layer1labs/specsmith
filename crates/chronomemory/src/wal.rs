// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
//! Append-only Write-Ahead Log with SHA-256 hash chain (Invariant 8).

use crate::types::EsdbId;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::{File, OpenOptions};
use std::io::{BufReader, Read, Write};
use std::path::{Path, PathBuf};

// ---------------------------------------------------------------------------
// WAL entry
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EventType {
    Insert,
    Modify,
    Invalidate,
    Tombstone,
    Rollback,
    Checkpoint,
    AddEdge,
    RecordMetric,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalEntry {
    pub seq: u64,
    pub timestamp: DateTime<Utc>,
    pub event_type: EventType,
    pub record_id: EsdbId,
    pub payload: Vec<u8>,
    pub prev_hash: [u8; 32],
    pub hash: [u8; 32],
}

impl WalEntry {
    fn compute_hash(prev_hash: &[u8; 32], payload: &[u8]) -> [u8; 32] {
        let mut hasher = Sha256::new();
        hasher.update(prev_hash);
        hasher.update(payload);
        hasher.finalize().into()
    }
}

// ---------------------------------------------------------------------------
// WAL magic header
// ---------------------------------------------------------------------------

const WAL_MAGIC: &[u8; 8] = b"ESDB_WAL";
const WAL_VERSION: u32 = 1;

// ---------------------------------------------------------------------------
// WAL writer
// ---------------------------------------------------------------------------

pub struct WalWriter {
    path: PathBuf,
    seq: u64,
    prev_hash: [u8; 32],
}

impl WalWriter {
    /// Open or create a WAL file.
    pub fn open(path: impl AsRef<Path>) -> Result<Self, WalError> {
        let path = path.as_ref().to_path_buf();

        if path.exists() {
            // Read existing WAL to get last seq + hash
            let reader = WalReader::open(&path)?;
            let entries = reader.read_all()?;
            let (seq, prev_hash) = if let Some(last) = entries.last() {
                (last.seq, last.hash)
            } else {
                (0, [0u8; 32])
            };
            Ok(Self {
                path,
                seq,
                prev_hash,
            })
        } else {
            // Create new WAL with header
            if let Some(parent) = path.parent() {
                std::fs::create_dir_all(parent).map_err(WalError::Io)?;
            }
            let mut file = File::create(&path).map_err(WalError::Io)?;
            file.write_all(WAL_MAGIC).map_err(WalError::Io)?;
            file.write_all(&WAL_VERSION.to_le_bytes())
                .map_err(WalError::Io)?;
            file.flush().map_err(WalError::Io)?;
            Ok(Self {
                path,
                seq: 0,
                prev_hash: [0u8; 32],
            })
        }
    }

    /// Append an event to the WAL.
    pub fn append(
        &mut self,
        event_type: EventType,
        record_id: EsdbId,
        payload: &[u8],
    ) -> Result<WalEntry, WalError> {
        self.seq += 1;
        let hash = WalEntry::compute_hash(&self.prev_hash, payload);
        let entry = WalEntry {
            seq: self.seq,
            timestamp: Utc::now(),
            event_type,
            record_id,
            payload: payload.to_vec(),
            prev_hash: self.prev_hash,
            hash,
        };

        let encoded = bincode::serialize(&entry).map_err(WalError::Encode)?;
        let len = (encoded.len() as u32).to_le_bytes();

        let mut file = OpenOptions::new()
            .append(true)
            .open(&self.path)
            .map_err(WalError::Io)?;

        file.write_all(&len).map_err(WalError::Io)?;
        file.write_all(&encoded).map_err(WalError::Io)?;
        file.flush().map_err(WalError::Io)?;

        self.prev_hash = hash;
        Ok(entry)
    }

    pub fn seq(&self) -> u64 {
        self.seq
    }

    pub fn prev_hash(&self) -> [u8; 32] {
        self.prev_hash
    }
}

// ---------------------------------------------------------------------------
// WAL reader
// ---------------------------------------------------------------------------

pub struct WalReader {
    path: PathBuf,
}

impl WalReader {
    pub fn open(path: impl AsRef<Path>) -> Result<Self, WalError> {
        let path = path.as_ref().to_path_buf();
        if !path.exists() {
            return Err(WalError::NotFound(path.display().to_string()));
        }
        Ok(Self { path })
    }

    /// Read all entries from the WAL.
    pub fn read_all(&self) -> Result<Vec<WalEntry>, WalError> {
        let file = File::open(&self.path).map_err(WalError::Io)?;
        let mut reader = BufReader::new(file);

        // Read and verify header
        let mut magic = [0u8; 8];
        reader.read_exact(&mut magic).map_err(WalError::Io)?;
        if &magic != WAL_MAGIC {
            return Err(WalError::InvalidMagic);
        }
        let mut ver_bytes = [0u8; 4];
        reader.read_exact(&mut ver_bytes).map_err(WalError::Io)?;

        let mut entries = Vec::new();
        loop {
            let mut len_bytes = [0u8; 4];
            match reader.read_exact(&mut len_bytes) {
                Ok(()) => {}
                Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => break,
                Err(e) => return Err(WalError::Io(e)),
            }
            let len = u32::from_le_bytes(len_bytes) as usize;
            let mut buf = vec![0u8; len];
            reader.read_exact(&mut buf).map_err(WalError::Io)?;
            let entry: WalEntry = bincode::deserialize(&buf).map_err(WalError::Decode)?;
            entries.push(entry);
        }

        Ok(entries)
    }

    /// Verify the hash chain integrity (Invariant 8).
    pub fn verify_chain(&self) -> Result<bool, WalError> {
        let entries = self.read_all()?;
        let mut expected_prev = [0u8; 32];
        for entry in &entries {
            if entry.prev_hash != expected_prev {
                return Ok(false);
            }
            let computed = WalEntry::compute_hash(&entry.prev_hash, &entry.payload);
            if entry.hash != computed {
                return Ok(false);
            }
            expected_prev = entry.hash;
        }
        Ok(true)
    }
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

#[derive(Debug, thiserror::Error)]
pub enum WalError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("WAL not found: {0}")]
    NotFound(String),
    #[error("Invalid WAL magic bytes")]
    InvalidMagic,
    #[error("Encode error: {0}")]
    Encode(bincode::Error),
    #[error("Decode error: {0}")]
    Decode(bincode::Error),
}
