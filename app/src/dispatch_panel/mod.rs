// dispatch_panel/mod.rs — Kairos DispatchPanelView
//
// REQ-332: live DAG graph subscribed to SSE, nodes coloured by status.
// REQ-333: Gantt timeline strip showing parallelism (see gantt.rs).
// REQ-334: Retry / Abort action buttons per node (see controls.rs).

pub mod controls;
pub mod gantt;

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use eframe::egui::{self, Color32, Pos2, Rect, Sense, Stroke, Vec2};
use serde::{Deserialize, Serialize};
use tracing::info;

pub use controls::ControlsPanel;
pub use gantt::GanttStrip;

// ---------------------------------------------------------------------------
// Data model
// ---------------------------------------------------------------------------

/// Mirrors the Python DispatchEvent dataclass.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct DispatchEvent {
    pub dag_id: String,
    pub event_type: String,
    pub node_id: String,
    pub ts: String,
    pub payload: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq)]
pub enum NodeStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Blocked,
}

impl NodeStatus {
    pub fn color(&self) -> Color32 {
        match self {
            NodeStatus::Pending   => Color32::from_rgb(100, 100, 100),  // grey
            NodeStatus::Running   => Color32::from_rgb(30,  120, 220),  // blue
            NodeStatus::Completed => Color32::from_rgb(34,  160,  74),  // green
            NodeStatus::Failed    => Color32::from_rgb(200,  50,  50),  // red
            NodeStatus::Blocked   => Color32::from_rgb(200, 140,  30),  // amber
        }
    }

    pub fn label(&self) -> &'static str {
        match self {
            NodeStatus::Pending   => "pending",
            NodeStatus::Running   => "running",
            NodeStatus::Completed => "completed",
            NodeStatus::Failed    => "failed",
            NodeStatus::Blocked   => "blocked",
        }
    }
}

#[derive(Debug, Clone)]
pub struct NodeInfo {
    pub id: String,
    pub role: String,
    pub status: NodeStatus,
    pub summary: String,
    pub esdb_record_id: Option<String>,
    pub started_at: Option<Instant>,
    pub finished_at: Option<Instant>,
    pub error: Option<String>,
}

impl NodeInfo {
    pub fn new(id: &str, role: &str) -> Self {
        Self {
            id: id.to_string(),
            role: role.to_string(),
            status: NodeStatus::Pending,
            summary: String::new(),
            esdb_record_id: None,
            started_at: None,
            finished_at: None,
            error: None,
        }
    }
}

// ---------------------------------------------------------------------------
// Shared state (written by SSE thread, read by UI thread)
// ---------------------------------------------------------------------------

#[derive(Debug, Default)]
pub struct DispatchState {
    pub dag_id: String,
    pub nodes: HashMap<String, NodeInfo>,
    pub events: Vec<DispatchEvent>,
    pub selected_node: Option<String>,
    pub dag_done: bool,
}

impl DispatchState {
    pub fn apply_event(&mut self, evt: &DispatchEvent) {
        match evt.event_type.as_str() {
            "node_started" => {
                let role = evt.payload.get("role")
                    .and_then(|v| v.as_str())
                    .unwrap_or("unknown")
                    .to_string();
                let node = self.nodes.entry(evt.node_id.clone())
                    .or_insert_with(|| NodeInfo::new(&evt.node_id, &role));
                node.status = NodeStatus::Running;
                node.started_at = Some(Instant::now());
            }
            "node_completed" => {
                if let Some(node) = self.nodes.get_mut(&evt.node_id) {
                    node.status = NodeStatus::Completed;
                    node.finished_at = Some(Instant::now());
                    node.summary = evt.payload.get("summary")
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .to_string();
                    node.esdb_record_id = evt.payload.get("esdb_record_id")
                        .and_then(|v| v.as_str())
                        .map(|s| s.to_string());
                }
            }
            "node_failed" => {
                if let Some(node) = self.nodes.get_mut(&evt.node_id) {
                    node.status = NodeStatus::Failed;
                    node.finished_at = Some(Instant::now());
                    node.error = evt.payload.get("error")
                        .and_then(|v| v.as_str())
                        .map(|s| s.to_string());
                }
            }
            "node_blocked" => {
                if let Some(node) = self.nodes.get_mut(&evt.node_id) {
                    node.status = NodeStatus::Blocked;
                }
            }
            "dag_done" => {
                self.dag_done = true;
            }
            _ => {}
        }
        self.events.push(evt.clone());
    }
}

// ---------------------------------------------------------------------------
// DispatchApp
// ---------------------------------------------------------------------------

pub struct DispatchApp {
    server_url: String,
    state: Arc<Mutex<DispatchState>>,
    dag_id_input: String,
    current_dag_id: Option<String>,
    side_panel_open: bool,
    selected_node_id: Option<String>,
}

impl DispatchApp {
    pub fn new(
        _cc: &eframe::CreationContext<'_>,
        server_url: String,
        initial_dag_id: Option<String>,
    ) -> Self {
        let state = Arc::new(Mutex::new(DispatchState::default()));

        let mut app = Self {
            server_url,
            state,
            dag_id_input: String::new(),
            current_dag_id: None,
            side_panel_open: false,
            selected_node_id: None,
        };

        if let Some(dag_id) = initial_dag_id {
            app.dag_id_input = dag_id.clone();
            app.connect_sse(dag_id);
        }

        app
    }

    /// Spawn a background thread that consumes the SSE stream for `dag_id`.
    fn connect_sse(&mut self, dag_id: String) {
        let url = format!(
            "{}/api/dispatch/events?dag_id={}",
            self.server_url, dag_id
        );
        let state = Arc::clone(&self.state);
        self.current_dag_id = Some(dag_id.clone());
        {
            let mut s = state.lock().unwrap();
            s.dag_id = dag_id.clone();
            s.nodes.clear();
            s.events.clear();
            s.dag_done = false;
        }

        thread::spawn(move || {
            info!("SSE connecting to {}", url);
            // Use blocking reqwest to consume SSE line by line
            let client = reqwest::blocking::Client::new();
            match client
                .get(&url)
                .timeout(Duration::from_secs(300))
                .send()
            {
                Err(e) => {
                    tracing::error!("SSE connect error: {e}");
                }
                Ok(mut resp) => {
                    use std::io::{BufRead, BufReader};
                    let reader = BufReader::new(&mut resp);
                    for line in reader.lines() {
                        match line {
                            Ok(l) if l.starts_with("data: ") => {
                                let json_str = &l["data: ".len()..];
                                if let Ok(evt) =
                                    serde_json::from_str::<DispatchEvent>(json_str)
                                {
                                    let done = evt.event_type == "dag_done";
                                    state.lock().unwrap().apply_event(&evt);
                                    if done {
                                        break;
                                    }
                                }
                            }
                            _ => {}
                        }
                    }
                    info!("SSE stream ended for dag_id={dag_id}");
                }
            }
        });
    }

    fn post_action(&self, endpoint: &str, dag_id: &str, node_id: &str) {
        let url = format!("{}/api/dispatch/{}", self.server_url, endpoint);
        let body = serde_json::json!({ "dag_id": dag_id, "node_id": node_id });
        let _ = reqwest::blocking::Client::new()
            .post(&url)
            .json(&body)
            .send();
    }
}

impl eframe::App for DispatchApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Poll continuously while a run is active
        ctx.request_repaint_after(Duration::from_millis(200));

        let state = self.state.lock().unwrap().clone_for_ui();

        // ── Top bar ──────────────────────────────────────────────────────
        egui::TopBottomPanel::top("top_bar").show(ctx, |ui| {
            ui.horizontal(|ui| {
                ui.heading("Kairos");
                ui.separator();
                ui.label("DAG ID:");
                ui.text_edit_singleline(&mut self.dag_id_input);
                if ui.button("Connect").clicked() && !self.dag_id_input.is_empty() {
                    let id = self.dag_id_input.trim().to_string();
                    self.connect_sse(id);
                }
                if let Some(did) = &state.dag_id {
                    ui.separator();
                    ui.label(format!("▶ {did}"));
                    if state.dag_done {
                        ui.label("✓ done");
                    }
                }
            });
        });

        // ── Side panel — node detail ─────────────────────────────────────
        if self.side_panel_open {
            egui::SidePanel::right("node_detail").show(ctx, |ui| {
                if let Some(nid) = &self.selected_node_id {
                    if let Some(node) = state.nodes.get(nid) {
                        ui.heading(&node.id);
                        ui.label(format!("Role: {}", node.role));
                        ui.label(format!("Status: {}", node.status.label()));
                        if !node.summary.is_empty() {
                            ui.separator();
                            ui.label(&node.summary);
                        }
                        if let Some(rid) = &node.esdb_record_id {
                            ui.label(format!("ESDB: {rid}"));
                        }
                        if let Some(err) = &node.error {
                            ui.colored_label(Color32::RED, err);
                        }
                        ui.separator();
                        // Controls (REQ-334)
                        if let Some(dag_id) = &state.dag_id {
                            ControlsPanel::show(ui, node, dag_id, |action, dag, nid| {
                                self.post_action(action, dag, nid);
                            });
                        }
                    }
                }
                if ui.button("✕ close").clicked() {
                    self.side_panel_open = false;
                }
            });
        }

        // ── Gantt strip (REQ-333) ────────────────────────────────────────
        egui::TopBottomPanel::bottom("gantt").resizable(true).show(ctx, |ui| {
            ui.heading("Timeline");
            GanttStrip::show(ui, &state.nodes);
        });

        // ── Main DAG panel (REQ-332) ─────────────────────────────────────
        egui::CentralPanel::default().show(ctx, |ui| {
            if state.nodes.is_empty() {
                ui.centered_and_justified(|ui| {
                    ui.label("Connect to a dag_id to see the dispatch graph.");
                });
                return;
            }
            self.render_dag(ui, &state);
        });
    }
}

impl DispatchApp {
    /// Render the SVG-style DAG using egui painter.
    fn render_dag(&mut self, ui: &mut egui::Ui, state: &UiState) {
        let available = ui.available_size();
        let (response, painter) =
            ui.allocate_painter(available, Sense::click());

        let node_w = 140.0_f32;
        let node_h = 40.0_f32;
        let nodes: Vec<&NodeInfo> = state.nodes.values().collect();
        let n = nodes.len() as f32;
        let col_gap = 200.0_f32;
        let row_gap = 80.0_f32;

        // Simple layout: evenly distribute nodes left→right, top→bottom
        let cols = (n.sqrt().ceil() as usize).max(1);
        let mut positions: HashMap<String, Pos2> = HashMap::new();
        for (i, node) in nodes.iter().enumerate() {
            let col = (i % cols) as f32;
            let row = (i / cols) as f32;
            let x = response.rect.min.x + 20.0 + col * col_gap;
            let y = response.rect.min.y + 20.0 + row * row_gap;
            positions.insert(node.id.clone(), Pos2::new(x, y));
        }

        // Draw nodes
        for node in &nodes {
            let pos = positions[&node.id];
            let rect = Rect::from_min_size(pos, Vec2::new(node_w, node_h));
            let color = node.status.color();
            painter.rect_filled(rect, 6.0, color);
            painter.rect_stroke(rect, 6.0, Stroke::new(1.5, Color32::WHITE));
            painter.text(
                rect.center(),
                egui::Align2::CENTER_CENTER,
                &node.id,
                egui::FontId::proportional(12.0),
                Color32::WHITE,
            );

            // Click to open detail panel
            if response.clicked() {
                let pointer = ui.ctx().pointer_latest_pos().unwrap_or_default();
                if rect.contains(pointer) {
                    self.selected_node_id = Some(node.id.clone());
                    self.side_panel_open = true;
                }
            }
        }

        // Highlight selected node
        if let Some(sel) = &self.selected_node_id {
            if let Some(pos) = positions.get(sel) {
                let rect = Rect::from_min_size(*pos, Vec2::new(node_w, node_h));
                painter.rect_stroke(rect, 6.0, Stroke::new(3.0, Color32::YELLOW));
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Cloneable UI snapshot (avoids holding the mutex during rendering)
// ---------------------------------------------------------------------------

pub struct UiState {
    pub dag_id: Option<String>,
    pub nodes: HashMap<String, NodeInfo>,
    pub dag_done: bool,
}

impl DispatchState {
    pub fn clone_for_ui(&self) -> UiState {
        UiState {
            dag_id: if self.dag_id.is_empty() { None } else { Some(self.dag_id.clone()) },
            nodes: self.nodes.clone(),
            dag_done: self.dag_done,
        }
    }
}
