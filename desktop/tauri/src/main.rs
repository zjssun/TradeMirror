use anyhow::{Context, Result};
use rand::{distributions::Alphanumeric, Rng};
use serde::Serialize;
use std::{
    net::{Ipv4Addr, SocketAddr, TcpListener},
    path::PathBuf,
    process::{Child, Command},
    sync::Mutex,
    thread,
    time::Duration,
};
use tauri::{Manager, State};
use tauri_plugin_dialog::DialogExt;

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct EngineRuntime {
    base_url: String,
    token: String,
}

struct EngineProcess(Mutex<Child>);

#[tauri::command]
fn get_engine_runtime(runtime: State<'_, EngineRuntime>) -> EngineRuntime {
    runtime.inner().clone()
}

#[tauri::command]
fn save_tmf_export(app: tauri::AppHandle, runtime: State<'_, EngineRuntime>, export_id: String) -> Result<(), String> {
    if export_id.len() != 32 || !export_id.chars().all(|character| character.is_ascii_hexdigit()) {
        return Err("Invalid export identifier".into());
    }
    let runtime = runtime.inner().clone();
    app.dialog().file().add_filter("TradeMirror 文件", &["tmf"]).set_file_name("trademirror-export.tmf").save_file(move |destination| {
        let Some(destination) = destination else { return };
        let Ok(response) = reqwest::blocking::Client::new()
            .get(format!("{}/exports/{export_id}/download", runtime.base_url))
            .header("X-TradeMirror-Token", runtime.token)
            .send() else { return };
        let Ok(content) = response.error_for_status().and_then(|reply| reply.bytes()) else { return };
        if let Some(path) = destination.as_path() {
            let _ = std::fs::write(path, content);
        }
    });
    Ok(())
}

fn available_loopback_port() -> Result<u16> {
    let listener = TcpListener::bind(SocketAddr::from((Ipv4Addr::LOCALHOST, 0)))?;
    Ok(listener.local_addr()?.port())
}

fn launch_token() -> String {
    rand::thread_rng()
        .sample_iter(&Alphanumeric)
        .take(48)
        .map(char::from)
        .collect()
}

fn engine_working_directory() -> Result<PathBuf> {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    manifest_dir
        .join("../../engine")
        .canonicalize()
        .context("Unable to locate the engine source directory")
}

fn start_engine(app: &tauri::App) -> Result<(EngineRuntime, Child)> {
    let port = available_loopback_port()?;
    let token = launch_token();
    let data_dir = app.path().app_data_dir()?.join("data");
    let log_dir = app.path().app_log_dir()?.join("engine");
    std::fs::create_dir_all(&data_dir)?;
    std::fs::create_dir_all(&log_dir)?;

    let child = Command::new("python")
        .args(["-m", "app.main"])
        .current_dir(engine_working_directory()?)
        .env("TRADEMIRROR_HOST", "127.0.0.1")
        .env("TRADEMIRROR_PORT", port.to_string())
        .env("TRADEMIRROR_LAUNCH_TOKEN", &token)
        .env("TRADEMIRROR_DATA_DIR", data_dir)
        .env("TRADEMIRROR_LOG_DIR", log_dir)
        .spawn()
        .context("Unable to start the local analysis engine. Ensure Python 3.12+ is available.")?;

    let runtime = EngineRuntime {
        base_url: format!("http://127.0.0.1:{port}"),
        token,
    };
    wait_for_engine(&runtime)?;
    Ok((runtime, child))
}

fn wait_for_engine(runtime: &EngineRuntime) -> Result<()> {
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(1))
        .build()?;

    for _ in 0..30 {
        if let Ok(response) = client
            .get(format!("{}/health", runtime.base_url))
            .header("X-TradeMirror-Token", &runtime.token)
            .send()
        {
            if response.status().is_success() {
                return Ok(());
            }
        }
        thread::sleep(Duration::from_millis(250));
    }

    anyhow::bail!("The local analysis engine did not become ready within 8 seconds")
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let (runtime, child) = start_engine(app)?;
            app.manage(runtime);
            app.manage(EngineProcess(Mutex::new(child)));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_engine_runtime, save_tmf_export])
        .plugin(tauri_plugin_dialog::init())
        .build(tauri::generate_context!())
        .expect("error while running TradeMirror")
        .run(|app_handle, event| {
            if matches!(event, tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit) {
                if let Some(engine) = app_handle.try_state::<EngineProcess>() {
                    if let Ok(mut child) = engine.0.lock() {
                        let _ = child.kill();
                    }
                }
            }
        });
}
