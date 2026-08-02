use anyhow::{Context, Result};
use rand::{distributions::Alphanumeric, Rng};
use serde::{Deserialize, Serialize};
use std::{
    env,
    fs,
    net::{Ipv4Addr, SocketAddr, TcpListener},
    path::PathBuf,
    process::{Child, Command},
    sync::Mutex,
    thread,
    time::{Duration, Instant},
};
#[cfg(windows)]
use std::os::windows::process::CommandExt;
use tauri::{Manager, State};
use tauri_plugin_dialog::DialogExt;

const ENGINE_STARTUP_TIMEOUT: Duration = Duration::from_secs(30);
const ENGINE_START_ATTEMPTS: usize = 3;
#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct EngineRuntime {
    base_url: String,
    token: String,
}

#[derive(Default, Deserialize)]
struct PortableConfig {
    version: Option<String>,
    portable: Option<bool>,
    data_path: Option<String>,
    engine_port: Option<u16>,
}

struct EngineProcess(Mutex<Option<Child>>);

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
            let _ = fs::write(path, content);
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

fn application_directory() -> Result<PathBuf> {
    env::current_exe()?
        .parent()
        .map(PathBuf::from)
        .context("Unable to locate the TradeMirror application directory")
}

fn validate_portable_config() -> Result<()> {
    if cfg!(debug_assertions) {
        return Ok(());
    }

    let config_path = application_directory()?.join("config").join("config.json");
    if !config_path.is_file() {
        return Ok(());
    }
    let contents = fs::read_to_string(&config_path)
        .with_context(|| format!("Unable to read portable configuration: {}", config_path.display()))?;
    let config: PortableConfig = serde_json::from_str(&contents)
        .with_context(|| format!("Invalid portable configuration: {}", config_path.display()))?;
    if config.version.as_deref().is_some_and(|version| version != "1.0")
        || config.portable != Some(true)
        || config.data_path.as_deref().is_some_and(|path| !path.is_empty())
        || config.engine_port.is_some_and(|port| port != 0)
    {
        anyhow::bail!("Portable configuration must keep portable=true, data_path empty, and engine_port=0")
    }
    Ok(())
}

fn engine_command() -> Result<Command> {
    if cfg!(debug_assertions) {
        let engine_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../engine")
            .canonicalize()
            .context("Unable to locate the engine source directory")?;
        let mut command = Command::new("python");
        command.args(["-m", "app.main"]).current_dir(engine_dir);
        return Ok(command);
    }

    let engine_path = application_directory()?.join("engine").join("TradeMirrorEngine.exe");
    if !engine_path.is_file() {
        anyhow::bail!("Packaged engine is missing: {}", engine_path.display());
    }
    let mut command = Command::new(&engine_path);
    command.current_dir(engine_path.parent().context("Packaged engine has no parent directory")?);
    Ok(command)
}

fn runtime_directories() -> Result<(PathBuf, PathBuf)> {
    let root = PathBuf::from(env::var_os("APPDATA").context("APPDATA is unavailable")?).join("TradeMirror");
    let data_dir = root.clone();
    let log_dir = root.join("logs").join("engine");
    for directory in [
        data_dir.join("database"),
        data_dir.join("tmf"),
        data_dir.join("cache"),
        data_dir.join("import-previews"),
        log_dir.clone(),
    ] {
        fs::create_dir_all(directory)?;
    }
    Ok((data_dir, log_dir))
}

fn wait_for_engine(child: &mut Child, runtime: &EngineRuntime) -> Result<()> {
    let client = reqwest::blocking::Client::builder().timeout(Duration::from_secs(1)).build()?;
    let started = Instant::now();
    while started.elapsed() < ENGINE_STARTUP_TIMEOUT {
        if let Some(status) = child.try_wait()? {
            anyhow::bail!("The local analysis engine exited before it was ready: {status}");
        }
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
    anyhow::bail!("The local analysis engine did not become ready within 30 seconds")
}

fn stop_engine(child: &mut Child) {
    if child.try_wait().ok().flatten().is_none() {
        let _ = child.kill();
    }
    let _ = child.wait();
}

fn start_engine() -> Result<(EngineRuntime, Child)> {
    validate_portable_config()?;
    let (data_dir, log_dir) = runtime_directories()?;
    let token = launch_token();
    let mut last_error = None;

    for _ in 0..ENGINE_START_ATTEMPTS {
        let port = available_loopback_port()?;
        let runtime = EngineRuntime { base_url: format!("http://127.0.0.1:{port}"), token: token.clone() };
        let mut command = engine_command()?;
        command
            .env("TRADEMIRROR_HOST", "127.0.0.1")
            .env("TRADEMIRROR_PORT", port.to_string())
            .env("TRADEMIRROR_LAUNCH_TOKEN", &token)
            .env("TRADEMIRROR_DATA_DIR", &data_dir)
            .env("TRADEMIRROR_LOG_DIR", &log_dir);
        #[cfg(windows)]
        command.creation_flags(CREATE_NO_WINDOW);

        let mut child = command.spawn().with_context(|| format!("Unable to start the local analysis engine. Check {}", log_dir.display()))?;
        match wait_for_engine(&mut child, &runtime) {
            Ok(()) => return Ok((runtime, child)),
            Err(error) => {
                stop_engine(&mut child);
                last_error = Some(error);
            }
        }
    }

    Err(last_error
        .unwrap_or_else(|| anyhow::anyhow!("No engine startup attempt was made"))
        .context("Unable to start the local analysis engine"))
}

fn shutdown_engine(app_handle: &tauri::AppHandle) {
    if let Some(engine) = app_handle.try_state::<EngineProcess>() {
        if let Ok(mut process) = engine.0.lock() {
            if let Some(mut child) = process.take() {
                stop_engine(&mut child);
            }
        }
    }
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let (runtime, child) = start_engine()?;
            app.manage(runtime);
            app.manage(EngineProcess(Mutex::new(Some(child))));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_engine_runtime, save_tmf_export])
        .plugin(tauri_plugin_dialog::init())
        .build(tauri::generate_context!())
        .expect("error while running TradeMirror")
        .run(|app_handle, event| {
            if matches!(event, tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit) {
                shutdown_engine(app_handle);
            }
        });
}
