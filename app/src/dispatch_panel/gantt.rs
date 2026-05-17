// dispatch_panel/gantt.rs — Gantt timeline strip
//
// REQ-333: renders a horizontal timeline bar per node, filled as the node
// transitions from pending → running → completed, showing parallelism visually.

use std::collections::HashMap;
use std::time::Instant;

use eframe::egui::{self, Color32, Rect, Stroke, Vec2};

use super::NodeInfo;

pub struct GanttStrip;

impl GanttStrip {
    /// Render the Gantt strip inside a given `ui` region.
    ///
    /// Each node gets a labelled row. The bar spans from `started_at` to
    /// `finished_at` (or the current time if still running). The bar colour
    /// matches the node status colour.
    pub fn show(ui: &mut egui::Ui, nodes: &HashMap<String, NodeInfo>) {
        if nodes.is_empty() {
            ui.label("(no nodes yet)");
            return;
        }

        // Find the earliest start to normalise time axis
        let now = Instant::now();
        let earliest: Option<Instant> = nodes
            .values()
            .filter_map(|n| n.started_at)
            .min();

        let Some(t0) = earliest else {
            ui.label("(waiting for first node to start)");
            return;
        };

        let total_secs = {
            let max_end = nodes
                .values()
                .filter_map(|n| n.finished_at.or(Some(now)))
                .map(|t| t.duration_since(t0).as_secs_f32())
                .fold(0.0_f32, f32::max);
            max_end.max(1.0)
        };

        let available_width = ui.available_width().max(200.0);
        let bar_area_x = 120.0_f32; // label column width
        let bar_area_w = available_width - bar_area_x - 10.0;
        let row_h = 20.0_f32;
        let row_gap = 4.0_f32;

        // Sort nodes by start time for stable display order
        let mut sorted: Vec<&NodeInfo> = nodes.values().collect();
        sorted.sort_by_key(|n| n.started_at.map(|t| t.duration_since(t0).as_millis()));

        for node in sorted {
            ui.horizontal(|ui| {
                // Label
                ui.set_min_width(bar_area_x);
                ui.label(&node.id);

                // Bar region
                let (rect, _) = ui.allocate_exact_size(
                    Vec2::new(bar_area_w, row_h),
                    egui::Sense::hover(),
                );

                let painter = ui.painter_at(rect);

                // Background track
                painter.rect_filled(
                    rect,
                    2.0,
                    Color32::from_gray(40),
                );

                // Filled bar if node has started
                if let Some(start) = node.started_at {
                    let start_frac = start.duration_since(t0).as_secs_f32() / total_secs;
                    let end_t = node.finished_at.unwrap_or(now);
                    let end_frac = end_t.duration_since(t0).as_secs_f32() / total_secs;

                    let bar_x0 = rect.min.x + start_frac * bar_area_w;
                    let bar_x1 = rect.min.x + end_frac * bar_area_w;
                    let bar_rect = Rect::from_min_max(
                        egui::Pos2::new(bar_x0, rect.min.y),
                        egui::Pos2::new(bar_x1.max(bar_x0 + 2.0), rect.max.y),
                    );
                    painter.rect_filled(bar_rect, 2.0, node.status.color());
                    painter.rect_stroke(bar_rect, 2.0, Stroke::new(0.5, Color32::WHITE));
                }
            });
            ui.add_space(row_gap);
        }
    }
}
