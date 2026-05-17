// Kairos — specsmith live dispatch UI
// REQ-332: renders a live DAG graph subscribed to SSE dispatch events.
// REQ-333: renders a Gantt timeline strip alongside the graph.
// REQ-334: provides Retry and Abort action buttons per node.

mod dispatch_panel;

use clap::Parser;
use eframe::egui;
use dispatch_panel::DispatchApp;

#[derive(Parser, Debug)]
#[command(name = "kairos", about = "Kairos — specsmith live dispatch UI")]
struct Args {
    /// specsmith serve base URL (default: http://127.0.0.1:8421)
    #[arg(long, default_value = "http://127.0.0.1:8421")]
    server: String,

    /// DAG run ID to open immediately (optional)
    #[arg(long)]
    dag_id: Option<String>,
}

fn main() -> eframe::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let args = Args::parse();

    let native_options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("Kairos — specsmith dispatch")
            .with_inner_size([1200.0, 720.0]),
        ..Default::default()
    };

    eframe::run_native(
        "kairos",
        native_options,
        Box::new(move |cc| -> Box<dyn eframe::App> {
            Box::new(DispatchApp::new(
                cc,
                args.server.clone(),
                args.dag_id.clone(),
            ))
        }),
    )
}
