// dispatch_panel/controls.rs — per-node Retry and Abort action buttons
//
// REQ-334: Retry button for FAILED/BLOCKED nodes; Abort button for RUNNING nodes.
//          Both are disabled (greyed-out) when not applicable to the current status.

use eframe::egui;

use super::{NodeInfo, NodeStatus};

pub struct ControlsPanel;

impl ControlsPanel {
    /// Render Retry / Abort buttons for a node.
    ///
    /// `on_action(endpoint, dag_id, node_id)` is called when the user clicks a button.
    /// `endpoint` is either `"retry"` or `"abort"`.
    pub fn show<F>(ui: &mut egui::Ui, node: &NodeInfo, dag_id: &str, mut on_action: F)
    where
        F: FnMut(&str, &str, &str),
    {
        ui.horizontal(|ui| {
            // Retry — enabled for FAILED and BLOCKED (REQ-334)
            let can_retry = matches!(
                node.status,
                NodeStatus::Failed | NodeStatus::Blocked
            );
            ui.add_enabled_ui(can_retry, |ui| {
                if ui
                    .button("⟳ Retry")
                    .on_disabled_hover_text("Only available for failed or blocked nodes")
                    .clicked()
                {
                    on_action("retry", dag_id, &node.id);
                }
            });

            ui.add_space(8.0);

            // Abort — enabled for RUNNING (REQ-334)
            let can_abort = node.status == NodeStatus::Running;
            ui.add_enabled_ui(can_abort, |ui| {
                if ui
                    .button("⏹ Abort")
                    .on_disabled_hover_text("Only available for running nodes")
                    .clicked()
                {
                    on_action("abort", dag_id, &node.id);
                }
            });
        });
    }
}
