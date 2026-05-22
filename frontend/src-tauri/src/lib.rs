// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandEvent;
use tauri::Emitter;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn run_pulpit_ink_sidecar(
    app: tauri::AppHandle,
    args: Vec<String>,
) -> Result<String, String> {
    let shell = app.shell();
    
    // Create sidecar command with specified arguments
    let sidecar = shell
        .sidecar("pulpit-ink-sidecar")
        .map_err(|e| e.to_string())?
        .args(args);

    // Spawn sidecar process
    let (mut rx, _child) = sidecar.spawn().map_err(|e| e.to_string())?;

    // Spawn asynchronous thread to pipe stdout/stderr to the frontend UI
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    if let Ok(text) = String::from_utf8(line) {
                        let _ = app.emit("sidecar-stdout", text);
                    }
                }
                CommandEvent::Stderr(line) => {
                    if let Ok(text) = String::from_utf8(line) {
                        let _ = app.emit("sidecar-stderr", text);
                    }
                }
                CommandEvent::Terminated(payload) => {
                    let _ = app.emit("sidecar-terminated", payload.code);
                }
                _ => {}
            }
        }
    });

    Ok("Sidecar spawned successfully".to_string())
}

#[tauri::command]
async fn run_pulpit_ink_sidecar_sync(
    app: tauri::AppHandle,
    args: Vec<String>,
) -> Result<String, String> {
    let shell = app.shell();
    
    let sidecar = shell
        .sidecar("pulpit-ink-sidecar")
        .map_err(|e| e.to_string())?
        .args(args);

    let output = sidecar.output().await.map_err(|e| e.to_string())?;
    
    if output.status.success() {
        let text = String::from_utf8(output.stdout).map_err(|e| e.to_string())?;
        Ok(text)
    } else {
        let err_text = String::from_utf8(output.stderr).map_err(|e| e.to_string())?;
        Err(err_text)
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            run_pulpit_ink_sidecar,
            run_pulpit_ink_sidecar_sync
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
