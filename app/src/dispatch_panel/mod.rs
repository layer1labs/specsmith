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
    /// Dependency edges from node_started payload — used for topological layout.
    pub depends_on: Vec<String>,
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
            depends_on: Vec::new(),
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
                let deps: Vec<String> = evt.payload.get("depends_on")
                    .and_then(|v| v.as_array())
                    .map(|arr| arr.iter()
                        .filter_map(|s| s.as_str().map(|s| s.to_string()))
                        .collect())
                    .unwrap_or_default();
                let node = self.nodes.entry(evt.node_id.clone())
                    .or_insert_with(|| NodeInfo::new(&evt.node_id, &role));
                node.status = NodeStatus::Running;
                node.started_at = Some(Instant::now());
                node.depends_on = deps;
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
        // Spawn a background thread so we never block the egui main loop.
        let url = format!("{}/api/dispatch/{}", self.server_url, endpoint);
        let body = serde_json::json!({ "dag_id": dag_id, "node_id": node_id });
        std::thread::spawn(move || {
            let _ = reqwest::blocking::Client::new()
                .post(&url)
                .timeout(std::time::Duration::from_secs(10))
                .json(&body)
                .send();
        });
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
    /// Compute topological level for each node (level = max(level of deps) + 1).
    /// Root nodes (no deps, or deps not yet seen) are level 0.
    fn compute_levels(nodes: &HashMap<String, NodeInfo>) -> HashMap<String, usize> {
        let mut levels: HashMap<String, usize> = HashMap::new();
        // Iteratively assign levels until stable (handles partial DAGs during live runs)
        let mut changed = true;
        while changed {
            changed = false;
            for node in nodes.values() {
                let max_dep_level = node.depends_on.iter()
                    .filter_map(|dep| levels.get(dep).copied())
                    .max()
                    .unwrap_or(0);
                let new_level = if node.depends_on.is_empty() {
                    0
                } else {
                    max_dep_level + 1
                };
                let entry = levels.entry(node.id.clone()).or_insert(0);
                if *entry != new_level {
                    *entry = new_level;
                    changed = true;
                }
            }
        }
        levels
    }

    /// Render the DAG using egui painter — topological layout with dependency edges.
    fn render_dag(&mut self, ui: &mut egui::Ui, state: &UiState) {
        let available = ui.available_size();
        let (response, painter) =
            ui.allocate_painter(available, Sense::click());

        let node_w = 140.0_f32;
        let node_h = 40.0_f32;
        let level_gap_x = 200.0_f32;  // horizontal gap between levels
        let node_gap_y = 80.0_f32;    // vertical gap between nodes in the same level
        let origin_x = response.rect.min.x + 20.0;
        let origin_y = response.rect.min.y + 20.0;

        // Compute topological levels
        let levels = Self::compute_levels(&state.nodes);

        // Group nodes by level
        let mut by_level: HashMap<usize, Vec<&NodeInfo>> = HashMap::new();
        for node in state.nodes.values() {
            let level = *levels.get(&node.id).unwrap_or(&0);
            by_level.entry(level).or_default().push(node);
        }

        // Sort nodes within each level deterministically
        for nodes in by_level.values_mut() {
            nodes.sort_by_key(|n| n.id.as_str());
        }

        // Assign positions: x by level, y evenly spread within level
        let mut positions: HashMap<String, Pos2> = HashMap::new();
        let max_level = by_level.keys().max().copied().unwrap_or(0);
        for level in 0..=max_level {
            let nodes_at_level = by_level.get(&level).map(|v| v.as_slice()).unwrap_or(&[]);
            let n = nodes_at_level.len();
            let total_height = (n as f32) * (node_h + node_gap_y) - node_gap_y;
            let start_y = origin_y + (available.y - total_height).max(0.0) / 2.0;
            for (i, node) in nodes_at_level.iter().enumerate() {
                let x = origin_x + (level as f32) * level_gap_x;
                let y = start_y + (i as f32) * (node_h + node_gap_y);
                positions.insert(node.id.clone(), Pos2::new(x, y));
            }
        }

        // Draw dependency edges FIRST (behind nodes)
        let edge_color = Color32::from_rgba_premultiplied(180, 180, 180, 140);
        for node in state.nodes.values() {
            if let Some(child_pos) = positions.get(&node.id) {
                let child_left = Pos2::new(child_pos.x, child_pos.y + node_h / 2.0);
                for dep_id in &node.depends_on {
                    if let Some(dep_pos) = positions.get(dep_id) {
                        // Arrow from right edge of parent to left edge of child
                        let parent_right = Pos2::new(
                            dep_pos.x + node_w,
                            dep_pos.y + node_h / 2.0,
                        );
                        // Bezier control points for a smooth curve
                        let mid_x = (parent_right.x + child_left.x) / 2.0;
                        let cp1 = Pos2::new(mid_x, parent_right.y);
                        let cp2 = Pos2::new(mid_x, child_left.y);
                        // Approximate bezier with line segments
                        let steps = 12;
                        let mut pts: Vec<Pos2> = Vec::with_capacity(steps + 1);
                        for k in 0..=steps {
                            let t = k as f32 / steps as f32;
                            let u = 1.0 - t;
                            let px = u*u*u*parent_right.x + 3.0*u*u*t*cp1.x
                                   + 3.0*u*t*t*cp2.x + t*t*t*child_left.x;
                            let py = u*u*u*parent_right.y + 3.0*u*u*t*cp1.y
                                   + 3.0*u*t*t*cp2.y + t*t*t*child_left.y;
                            pts.push(Pos2::new(px, py));
                        }
                        for w in pts.windows(2) {
                            painter.line_segment([w[0], w[1]], Stroke::new(1.5, edge_color));
                        }
                        // Arrowhead at child_left
                        let arrow_size = 6.0;
                        let tip = child_left;
                        painter.line_segment(
                            [tip, Pos2::new(tip.x - arrow_size, tip.y - arrow_size / 2.0)],
                            Stroke::new(1.5, edge_color),
                        );
                        painter.line_segment(
                            [tip, Pos2::new(tip.x - arrow_size, tip.y + arrow_size / 2.0)],
                            Stroke::new(1.5, edge_color),
                        );
                    }
                }
            }
        }

        // Draw nodes on top
        for node in state.nodes.values() {
            if let Some(pos) = positions.get(&node.id) {
                let rect = Rect::from_min_size(*pos, Vec2::new(node_w, node_h));
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
