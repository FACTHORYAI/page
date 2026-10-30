//! Facthory's updater: part of the Facthory patch set (`facthory/update/`), not of upstream.
//! `facthory/rebrand.py` copies it into the app and calls it from `main.rs` (`brand.toml`).
//!
//! Once a day it reads the update feed of our releases (`latest.json`, which
//! `facthory/release.py` writes). When the feed names a newer version, it downloads this
//! platform's file in the background and checks its size and SHA-256 against the feed and, on
//! macOS and Windows, that the system accepts its signature and that the same developer signed it
//! as this app. The new version then installs when the app quits; "Restart now" quits and opens it:
//!
//! - macOS: the new app bundle replaces this one, when its folder is writable.
//! - Windows: the MSI upgrades the app it installed, for the current account (its default,
//!   under `%LOCALAPPDATA%\Programs`) or for everyone (under Program Files).
//! - Linux: the new AppImage replaces this one (`$APPIMAGE`), when its folder is writable.
//!
//! A .deb or .rpm install gets a notice that the system's updates install the new version (from
//! our apt and dnf repositories, `facthory/packages.py`); any other copy (the portable zips and
//! tarballs, a read-only folder, an unsigned build) gets a notice with a link to the release. Builds without
//! `FACTHORY_UPDATE_FEED` (every build but our release workflow's) never check, nor do runs
//! without preferences, with `FACTHORY_UPDATES=off`, or with `"enabled": false` in `update.json`
//! in the settings folder.
//!
//! Downloads go through the system's `curl`, which macOS, Windows 10 and later, and Linux
//! desktops ship, so the app carries no TLS stack of its own; SHA-256 is here too, so the module
//! needs no dependency beyond egui, serde_json and log, which every app has.

use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::sync::{Mutex, MutexGuard, OnceLock, PoisonError};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

/// The update feed, set by the release workflow; builds without it never check.
const FEED: Option<&str> = option_env!("FACTHORY_UPDATE_FEED");
/// This build's version, which the feed's must exceed.
const VERSION: &str = env!("CARGO_PKG_VERSION");
/// Seconds between two reads of the feed, across restarts.
const INTERVAL: u64 = 24 * 60 * 60;
/// The largest feed and file read; the feed states each file's size, which is checked.
const FEED_MAX: u64 = 64 * 1024;
const FILE_MAX: u64 = 2 * 1024 * 1024 * 1024;

#[derive(Clone, Debug, PartialEq)]
enum Phase {
    Idle,
    /// A newer version this copy can't install itself: the notice links to its release.
    /// `packaged`: the system's package manager updates this copy (a .deb or .rpm install).
    Available {
        version: String,
        page: String,
        packaged: bool,
    },
    /// Downloaded and checked: installs when the app quits.
    Ready {
        version: String,
        install: Install,
    },
}

#[derive(Clone, Debug, PartialEq)]
enum Install {
    /// Put the app bundle `staged` in the place of `bundle` (macOS).
    Bundle { staged: PathBuf, bundle: PathBuf },
    /// Run the MSI, which upgrades the installed app `exe` (Windows); `machine`: installed for
    /// everyone, not only for the current account.
    Msi { msi: PathBuf, exe: PathBuf, machine: bool },
    /// Put the AppImage `staged` in the place of `target` (Linux).
    AppImage { staged: PathBuf, target: PathBuf },
}

/// How this copy of the app can update itself, if it can.
#[derive(Clone, Debug, PartialEq)]
enum Method {
    Bundle(PathBuf),
    Msi { exe: PathBuf, machine: bool },
    AppImage(PathBuf),
}

struct Shared {
    name: &'static str,
    settings: PathBuf,
    /// The window's context, from the first frame: the check repaints it when it finds an update.
    ctx: Option<egui::Context>,
    phase: Phase,
    /// The notice was closed for this run.
    hidden: bool,
    /// "Restart now": open the new version once it is installed.
    restart: bool,
}

static SHARED: OnceLock<Mutex<Shared>> = OnceLock::new();

fn shared() -> Option<MutexGuard<'static, Shared>> {
    SHARED.get().map(|m| m.lock().unwrap_or_else(PoisonError::into_inner))
}

/// Starts the daily check, unless this build or run doesn't update (see the module docs).
/// `name` is the app's name; `settings` its settings folder, `None` for a run without preferences.
pub fn start(name: &'static str, settings: Option<PathBuf>) {
    let (Some(feed), Some(settings)) = (FEED, settings) else { return };
    if std::env::var("FACTHORY_UPDATES").is_ok_and(|v| v.eq_ignore_ascii_case("off")) || !Saved::load(&settings).enabled {
        log::info!("updates: off");
        return;
    }
    let state = Shared { name, settings: settings.clone(), ctx: None, phase: Phase::Idle, hidden: false, restart: false };
    if SHARED.set(Mutex::new(state)).is_err() {
        return;
    }
    if let Err(e) = std::thread::Builder::new().name("updates".into()).spawn(move || run(name, feed, &settings)) {
        log::warn!("updates: {e}");
    }
}

/// Shows the notice of an update, when there is one; call every frame.
pub fn ui(ctx: &egui::Context) {
    let Some(mut s) = shared() else { return };
    if s.ctx.is_none() {
        s.ctx = Some(ctx.clone());
    }
    if s.hidden || s.phase == Phase::Idle {
        return;
    }
    let name = s.name;
    let mut action = None;
    egui::Window::new("updates")
        .id(egui::Id::unique("facthory-update"))
        .title_bar(false)
        .resizable(false)
        .collapsible(false)
        .anchor(egui::Align2::RIGHT_BOTTOM, [-16.0, -48.0])
        .show(ctx, |ui| {
            ui.set_max_width(320.0);
            match &s.phase {
                Phase::Idle => {}
                Phase::Ready { version, .. } => {
                    ui.label(egui::RichText::new(format!("{name} {version} is ready")).strong());
                    ui.label(format!("It installs when you quit {name}."));
                    ui.horizontal(|ui| {
                        if ui.button("Restart now").clicked() {
                            action = Some(Action::Restart);
                        }
                        if ui.button("Later").clicked() {
                            action = Some(Action::Hide);
                        }
                    });
                }
                Phase::Available { version, page, packaged } => {
                    ui.label(egui::RichText::new(format!("{name} {version} is available")).strong());
                    ui.label(if *packaged { "Your system's software updates install it." } else { "Download it from its release page." });
                    ui.horizontal(|ui| {
                        if ui.button(if *packaged { "What's new" } else { "Download" }).clicked() {
                            action = Some(Action::Open(page.clone()));
                        }
                        if ui.button("Skip this version").clicked() {
                            action = Some(Action::Skip(version.clone()));
                        }
                        if ui.button("Later").clicked() {
                            action = Some(Action::Hide);
                        }
                    });
                }
            }
        });
    let Some(action) = action else { return };
    s.hidden = true;
    match action {
        Action::Hide => {}
        // The app's own close: it asks about unsaved documents, then quits, and `on_exit`
        // installs.
        Action::Restart => {
            s.restart = true;
            ctx.send_viewport_cmd(egui::ViewportCommand::Close);
        }
        Action::Open(url) => open_link(&url),
        Action::Skip(version) => Saved::update(&s.settings, |saved| saved.skip = Some(version)),
    }
}

enum Action {
    Hide,
    Restart,
    Open(String),
    Skip(String),
}

/// Installs a downloaded update, if there is one; call as the app quits, once it has saved.
pub fn on_exit() {
    let Some(mut s) = shared() else { return };
    let Phase::Ready { version, install } = std::mem::replace(&mut s.phase, Phase::Idle) else { return };
    match finish(&install, s.restart) {
        Ok(()) => log::info!("updates: installing {} {version}", s.name),
        Err(e) => log::warn!("updates: {e}"),
    }
}

// ---------------------------------------------------------------------------------------------
// The check, on its own thread.

fn run(name: &str, feed: &str, settings: &Path) {
    let downloads = settings.join("updates");
    // What an earlier run downloaded or staged: installed by now, or abandoned.
    let _ = std::fs::remove_dir_all(&downloads);
    match Method::for_this_copy(name) {
        Some(Method::Bundle(bundle)) => remove_any(&staged_beside(&bundle)),
        Some(Method::AppImage(target)) => remove_any(&staged_beside(&target)),
        _ => {}
    }
    loop {
        let wait = Saved::load(settings).wait(now());
        if wait > 0 {
            std::thread::sleep(Duration::from_secs(wait));
            continue;
        }
        let checked = check(name, feed, settings, &downloads);
        Saved::update(settings, |saved| saved.last_check = now());
        match checked {
            Ok(Phase::Idle) => {}
            Ok(phase) => {
                let ready = matches!(phase, Phase::Ready { .. });
                if let Some(mut s) = shared() {
                    s.phase = phase;
                    s.hidden = false;
                    if let Some(ctx) = &s.ctx {
                        ctx.request_repaint();
                    }
                }
                if ready {
                    return;
                }
            }
            Err(e) => log::warn!("updates: {e}"),
        }
    }
}

fn check(name: &str, feed_url: &str, settings: &Path, downloads: &Path) -> Result<Phase, String> {
    let bytes = fetch(feed_url, FEED_MAX, None, "=https")?;
    let feed = Feed::parse(&bytes, feed_url, platform())?;
    if !newer(&feed.version, VERSION) || Saved::load(settings).skip.as_deref() == Some(feed.version.as_str()) {
        return Ok(Phase::Idle);
    }
    log::info!("updates: {name} {} is available", feed.version);
    let available = Phase::Available { version: feed.version.clone(), page: feed.page.clone(), packaged: packaged() };
    let (Some(asset), Some(method)) = (feed.asset, Method::for_this_copy(name)) else { return Ok(available) };
    std::fs::create_dir_all(downloads).map_err(|e| format!("{}: {e}", downloads.display()))?;
    let file = downloads.join(&asset.name);
    download(&asset, &file, "=https")?;
    match method.prepare(&file, downloads) {
        Ok(install) => Ok(Phase::Ready { version: feed.version, install }),
        Err(e) => {
            log::warn!("updates: {name} {} can't install itself here: {e}", feed.version);
            Ok(available)
        }
    }
}

/// A copy the system's package manager installed (.deb, .rpm, from our repositories): it updates
/// with the system, so the notice only says a new version exists.
fn packaged() -> bool {
    std::env::consts::OS == "linux"
        && std::env::var_os("APPIMAGE").is_none()
        && std::env::current_exe().is_ok_and(|exe| exe.starts_with("/usr/") || exe.starts_with("/opt/"))
}

/// The feed's entry for this platform (`release.py`), or `None` where the app can't update itself.
fn platform() -> Option<&'static str> {
    match (std::env::consts::OS, std::env::consts::ARCH) {
        ("macos", _) => Some("macos-universal"),
        ("windows", "x86_64") => Some("windows-x64"),
        ("windows", "aarch64") => Some("windows-arm64"),
        ("linux", "x86_64") => Some("linux-x86_64"),
        ("linux", "aarch64") => Some("linux-aarch64"),
        _ => None,
    }
}

#[derive(Debug, PartialEq)]
struct Feed {
    version: String,
    /// The release's page, for a copy that can't install the update itself.
    page: String,
    asset: Option<Asset>,
}

#[derive(Debug, PartialEq)]
struct Asset {
    name: String,
    url: String,
    sha256: String,
    size: u64,
}

impl Feed {
    /// Reads the feed fetched from `feed_url`. Only files of the same repository's releases are
    /// taken, under plain file names, and the release page is made from the version.
    fn parse(bytes: &[u8], feed_url: &str, platform: Option<&str>) -> Result<Feed, String> {
        // `https://github.com/<owner>/<repo>/`, from `…/releases/latest/download/latest.json`.
        let repo = feed_url
            .strip_prefix("https://")
            .and_then(|rest| rest.find("/releases/"))
            .and_then(|i| feed_url.get(..8 + i + 1))
            .ok_or_else(|| format!("not a release feed: {feed_url}"))?;
        let v: serde_json::Value = serde_json::from_slice(bytes).map_err(|e| format!("the feed: {e}"))?;
        let version = v.get("version").and_then(|v| v.as_str()).filter(|s| parse_version(s).is_some());
        let version = version.ok_or("the feed names no version")?.to_owned();
        let asset = platform.and_then(|p| v.get("assets")?.get(p)).and_then(|a| {
            let name = a.get("name")?.as_str()?;
            let url = a.get("url")?.as_str()?;
            let sha256 = a.get("sha256")?.as_str()?.to_ascii_lowercase();
            let size = a.get("size")?.as_u64()?;
            let plain = !name.starts_with('.') && name.len() < 200 && name.chars().all(|c| c.is_ascii_alphanumeric() || "._+-".contains(c));
            let ours = url.starts_with(&format!("{repo}releases/download/")) && url.ends_with(&format!("/{name}"));
            let sum = sha256.len() == 64 && sha256.chars().all(|c| c.is_ascii_hexdigit());
            (plain && ours && sum && size > 0 && size <= FILE_MAX).then(|| Asset { name: name.into(), url: url.into(), sha256, size })
        });
        Ok(Feed { page: format!("{repo}releases/tag/v{version}"), version, asset })
    }
}

/// `major.minor.patch`, the only form our releases take; anything else never counts as newer.
fn parse_version(s: &str) -> Option<(u64, u64, u64)> {
    let mut parts = s.split('.').map(|p| if p.chars().all(|c| c.is_ascii_digit()) { p.parse().ok() } else { None });
    let v = (parts.next()??, parts.next()??, parts.next()??);
    parts.next().is_none().then_some(v)
}

fn newer(candidate: &str, current: &str) -> bool {
    matches!((parse_version(candidate), parse_version(current)), (Some(a), Some(b)) if a > b)
}

// ---------------------------------------------------------------------------------------------
// What `update.json` in the settings folder keeps.

#[derive(Debug, PartialEq)]
struct Saved {
    enabled: bool,
    /// Seconds since 1970 of the last read of the feed.
    last_check: u64,
    /// The version the user chose to skip.
    skip: Option<String>,
}

impl Saved {
    fn path(settings: &Path) -> PathBuf {
        settings.join("update.json")
    }

    fn load(settings: &Path) -> Saved {
        let v: serde_json::Value = std::fs::read(Self::path(settings)).ok().and_then(|b| serde_json::from_slice(&b).ok()).unwrap_or_default();
        Saved {
            enabled: v.get("enabled").and_then(|e| e.as_bool()).unwrap_or(true),
            last_check: v.get("last_check").and_then(|t| t.as_u64()).unwrap_or(0),
            skip: v.get("skip").and_then(|s| s.as_str()).map(str::to_owned),
        }
    }

    /// Reads, changes and writes the file, so the check and the notice don't undo each other.
    fn update(settings: &Path, change: impl FnOnce(&mut Saved)) {
        let mut saved = Saved::load(settings);
        change(&mut saved);
        let json = serde_json::json!({"enabled": saved.enabled, "last_check": saved.last_check, "skip": saved.skip});
        let path = Self::path(settings);
        let tmp = settings.join(format!(".update.json.{}.tmp", std::process::id()));
        let written =
            std::fs::create_dir_all(settings).and_then(|()| std::fs::write(&tmp, json.to_string())).and_then(|()| std::fs::rename(&tmp, &path));
        if let Err(e) = written {
            let _ = std::fs::remove_file(&tmp);
            log::warn!("updates: {}: {e}", path.display());
        }
    }

    /// Seconds until the next check is due; a clock set back waits at most one interval.
    fn wait(&self, now: u64) -> u64 {
        self.last_check.saturating_add(INTERVAL).saturating_sub(now).min(INTERVAL)
    }
}

// The desktop apps only; never in a web build, where the clock traps (some upstream clippy.toml
// files disallow it for that).
#[allow(clippy::disallowed_methods)]
fn now() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0)
}

// ---------------------------------------------------------------------------------------------
// Downloads.

/// Fetches `url` over the protocols `proto` allows (curl's `--proto`): into `to`, or returned.
fn fetch(url: &str, max: u64, to: Option<&Path>, proto: &str) -> Result<Vec<u8>, String> {
    let mut cmd = Command::new(tool("curl"));
    cmd.args(["--fail", "--location", "--silent", "--show-error", "--connect-timeout", "30"])
        // A stalled transfer gives up after a minute below 1 kB/s.
        .args(["--speed-limit", "1024", "--speed-time", "60"])
        .args(["--proto", proto, "--proto-redir", proto])
        .arg("--max-filesize")
        .arg(max.to_string())
        .arg("--user-agent")
        .arg(format!("facthory-update/{VERSION}"));
    if let Some(to) = to {
        cmd.arg("--output").arg(to);
    }
    let out = output(cmd.arg(url))?;
    if out.stdout.len() as u64 > max {
        return Err(format!("{url}: larger than {max} bytes"));
    }
    Ok(out.stdout)
}

/// Downloads the asset to `file`, which holds it only once its size and SHA-256 match the feed.
fn download(asset: &Asset, file: &Path, proto: &str) -> Result<(), String> {
    let part = file.with_file_name(format!("{}.part", asset.name));
    let _ = std::fs::remove_file(&part);
    fetch(&asset.url, asset.size, Some(&part), proto)?;
    let checked = sha256_file(&part).and_then(|(size, sum)| {
        if size != asset.size {
            Err(format!("{}: {size} bytes, the feed says {}", asset.name, asset.size))
        } else if sum != asset.sha256 {
            Err(format!("{}: SHA-256 {sum}, the feed says {}", asset.name, asset.sha256))
        } else {
            std::fs::rename(&part, file).map_err(|e| format!("{}: {e}", file.display()))
        }
    });
    if checked.is_err() {
        let _ = std::fs::remove_file(&part);
    }
    checked
}

fn sha256_file(path: &Path) -> Result<(u64, String), String> {
    use std::io::Read;
    let mut f = std::fs::File::open(path).map_err(|e| format!("{}: {e}", path.display()))?;
    let (mut hasher, mut buf, mut size) = (Sha256::new(), vec![0u8; 1 << 16], 0u64);
    loop {
        let n = f.read(&mut buf).map_err(|e| format!("{}: {e}", path.display()))?;
        let Some(chunk) = buf.get(..n).filter(|c| !c.is_empty()) else { break };
        hasher.update(chunk);
        size += n as u64;
    }
    Ok((size, hasher.finish().iter().map(|b| format!("{b:02x}")).collect()))
}

/// SHA-256 (FIPS 180-4).
struct Sha256 {
    state: [u32; 8],
    /// The bytes of an unfinished block.
    pending: Vec<u8>,
    len: u64,
}

const K: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

impl Sha256 {
    fn new() -> Sha256 {
        let state = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
        Sha256 { state, pending: Vec::with_capacity(64), len: 0 }
    }

    fn update(&mut self, data: &[u8]) {
        self.len = self.len.wrapping_add(data.len() as u64);
        let (head, rest) = data.split_at((64 - self.pending.len()).min(data.len()));
        self.pending.extend_from_slice(head);
        if self.pending.len() < 64 {
            return;
        }
        if let Ok(block) = <[u8; 64]>::try_from(self.pending.as_slice()) {
            self.block(&block);
        }
        self.pending.clear();
        let (blocks, remainder) = rest.as_chunks::<64>();
        for b in blocks {
            self.block(b);
        }
        self.pending.extend_from_slice(remainder);
    }

    fn finish(mut self) -> [u8; 32] {
        let bits = self.len.wrapping_mul(8);
        let mut tail = std::mem::take(&mut self.pending);
        tail.push(0x80);
        while tail.len() % 64 != 56 {
            tail.push(0);
        }
        tail.extend_from_slice(&bits.to_be_bytes());
        for b in tail.as_chunks::<64>().0 {
            self.block(b);
        }
        let mut out = [0u8; 32];
        for (o, s) in out.as_chunks_mut::<4>().0.iter_mut().zip(self.state) {
            *o = s.to_be_bytes();
        }
        out
    }

    fn block(&mut self, block: &[u8; 64]) {
        let mut w = [0u32; 64];
        for (wi, c) in w.iter_mut().zip(block.as_chunks::<4>().0) {
            *wi = u32::from_be_bytes(*c);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16].wrapping_add(s0).wrapping_add(w[i - 7]).wrapping_add(s1);
        }
        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut h] = self.state;
        for (k, wi) in K.iter().zip(w) {
            let t1 = h
                .wrapping_add(e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25))
                .wrapping_add((e & f) ^ (!e & g))
                .wrapping_add(*k)
                .wrapping_add(wi);
            let t2 = (a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22)).wrapping_add((a & b) ^ (a & c) ^ (b & c));
            (h, g, f, e, d, c, b, a) = (g, f, e, d.wrapping_add(t1), c, b, a, t1.wrapping_add(t2));
        }
        for (s, v) in self.state.iter_mut().zip([a, b, c, d, e, f, g, h]) {
            *s = s.wrapping_add(v);
        }
    }
}

// ---------------------------------------------------------------------------------------------
// Installing, per platform.

impl Method {
    fn for_this_copy(name: &str) -> Option<Method> {
        let exe = std::env::current_exe().ok()?;
        match std::env::consts::OS {
            "macos" => {
                // `…/Facthory Page.app/Contents/MacOS/<binary>`; a copy macOS runs from a random
                // read-only path (App Translocation) can't replace itself.
                let bundle = exe.parent()?.parent()?.parent()?.to_path_buf();
                let ok = bundle.extension().is_some_and(|e| e == "app") && !bundle.to_string_lossy().contains("/AppTranslocation/");
                ok.then_some(Method::Bundle(bundle))
            }
            "windows" => {
                // The installer's own record decides: it writes the folder under HKLM for a copy
                // installed for everyone, under HKCU for the current account's, wherever it is.
                let recorded = [("HKLM", true), ("HKCU", false)]
                    .into_iter()
                    .find(|(hive, _)| recorded_install_dir(hive, name).is_some_and(|dir| exe.starts_with(dir)))
                    .map(|(_, machine)| machine);
                let program_files: Vec<PathBuf> = ["ProgramFiles", "ProgramW6432"].into_iter().filter_map(std::env::var_os).map(PathBuf::from).collect();
                let local = std::env::var_os("LOCALAPPDATA").map(PathBuf::from);
                recorded.or_else(|| msi_scope(&exe, &program_files, local.as_deref())).map(|machine| Method::Msi { exe, machine })
            }
            "linux" => {
                let target = PathBuf::from(std::env::var_os("APPIMAGE")?);
                target.is_file().then_some(Method::AppImage(target))
            }
            _ => None,
        }
    }

    /// Checks the downloaded `file` and readies it to install at quit.
    fn prepare(&self, file: &Path, downloads: &Path) -> Result<Install, String> {
        match self {
            Method::Bundle(bundle) => prepare_bundle(file, bundle, downloads),
            Method::Msi { exe, machine } => {
                windows_same_signer(file, exe)?;
                Ok(Install::Msi { msi: file.to_path_buf(), exe: exe.clone(), machine: *machine })
            }
            Method::AppImage(target) => {
                let staged = staged_beside(target);
                std::fs::copy(file, &staged).map_err(|e| format!("{}: {e}", staged.display()))?;
                make_executable(&staged)?;
                Ok(Install::AppImage { staged, target: target.clone() })
            }
        }
    }
}

/// The folder the installer recorded for `product` (`Software\<product>`, value `InstallDir`) in
/// `hive`: `HKLM` for a copy installed for everyone, `HKCU` for the current account's.
fn recorded_install_dir(hive: &str, product: &str) -> Option<PathBuf> {
    let key = format!(r"{hive}\Software\{product}");
    let out = output(Command::new(windows_tool("reg.exe")).args(["query", &key, "/v", "InstallDir"])).ok()?;
    reg_value(&String::from_utf8_lossy(&out.stdout), "InstallDir").map(PathBuf::from)
}

/// A string value in `reg query`'s output, whose line reads `    <name>    REG_SZ    <value>`.
fn reg_value(text: &str, name: &str) -> Option<String> {
    text.lines().find_map(|line| {
        let rest = line.trim_start().strip_prefix(name)?.trim_start();
        let value = rest.strip_prefix("REG_EXPAND_SZ").or_else(|| rest.strip_prefix("REG_SZ"))?.trim();
        (!value.is_empty()).then(|| value.to_owned())
    })
}

/// Opens a web page in the person's browser through the system, which works in every app (egui's
/// own link opening needs a feature not every app is built with). Only https addresses.
fn open_link(url: &str) {
    if !url.starts_with("https://") {
        return;
    }
    let mut cmd = match std::env::consts::OS {
        "macos" => Command::new(tool("open")),
        "windows" => {
            let mut c = Command::new(windows_tool("rundll32.exe"));
            c.arg("url.dll,FileProtocolHandler");
            c
        }
        _ => Command::new("xdg-open"),
    };
    if let Err(e) = detach(cmd.arg(url)) {
        log::warn!("updates: {e}");
    }
}

/// How the MSI installed `exe` by where it is, when the installer's record does not say: for everyone (`Some(true)`, under Program Files) or for the current
/// account (`Some(false)`, under `%LOCALAPPDATA%\Programs`, the installer's default). Any other copy,
/// a portable zip, isn't the MSI's to upgrade (`None`).
fn msi_scope(exe: &Path, program_files: &[PathBuf], local_app_data: Option<&Path>) -> Option<bool> {
    if program_files.iter().any(|d| exe.starts_with(d)) {
        return Some(true);
    }
    local_app_data.filter(|d| exe.starts_with(d.join("Programs"))).map(|_| false)
}

/// Where the new version waits, hidden beside the one it replaces, so the swap is a rename.
fn staged_beside(path: &Path) -> PathBuf {
    let name = path.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
    path.with_file_name(format!(".{name}.update"))
}

fn remove_any(path: &Path) {
    let _ = if path.is_dir() { std::fs::remove_dir_all(path) } else { std::fs::remove_file(path) };
}

/// Mounts the disk image, checks the app in it and copies it beside this one.
fn prepare_bundle(dmg: &Path, bundle: &Path, downloads: &Path) -> Result<Install, String> {
    let name = bundle.file_name().ok_or("no app bundle")?;
    let mount = downloads.join("mount");
    std::fs::create_dir_all(&mount).map_err(|e| format!("{}: {e}", mount.display()))?;
    let mut attach = Command::new("/usr/bin/hdiutil");
    output(attach.args(["attach", "-nobrowse", "-readonly", "-noautoopen", "-mountpoint"]).arg(&mount).arg(dmg))?;
    let staged = staged_beside(bundle);
    let copied = copy_checked_app(&mount.join(name), bundle, &staged);
    let _ = output(Command::new("/usr/bin/hdiutil").args(["detach", "-quiet"]).arg(&mount));
    if copied.is_err() {
        remove_any(&staged);
    }
    copied.map(|()| Install::Bundle { staged, bundle: bundle.to_path_buf() })
}

/// The new app passes macOS's strict signature check, has this app's Apple team, and is copied
/// to `staged`.
fn copy_checked_app(new_app: &Path, bundle: &Path, staged: &Path) -> Result<(), String> {
    output(Command::new("/usr/bin/codesign").args(["--verify", "--deep", "--strict"]).arg(new_app))?;
    let (theirs, ours) = (team_id(new_app)?, team_id(bundle)?);
    if theirs != ours {
        return Err(format!("the update is signed by team {theirs}, this app by {ours}"));
    }
    remove_any(staged);
    output(Command::new("/usr/bin/ditto").arg(new_app).arg(staged)).map(|_| ())
}

/// The Apple team that signed an app (`codesign -dv`); an unsigned app has none, and so no update.
fn team_id(app: &Path) -> Result<String, String> {
    let out = output(Command::new("/usr/bin/codesign").args(["-dv", "--verbose=2"]).arg(app))?;
    let text = String::from_utf8_lossy(&out.stderr);
    text.lines()
        .find_map(|l| l.strip_prefix("TeamIdentifier="))
        .map(str::trim)
        .filter(|t| !t.is_empty() && *t != "not set")
        .map(str::to_owned)
        .ok_or_else(|| format!("{} has no Developer ID signature", app.display()))
}

/// The installer's Authenticode signature is valid and has this app's signer.
fn windows_same_signer(msi: &Path, exe: &Path) -> Result<(), String> {
    const SCRIPT: &str = "$ErrorActionPreference = 'Stop'
$new = Get-AuthenticodeSignature -LiteralPath $env:FACTHORY_NEW
$ours = Get-AuthenticodeSignature -LiteralPath $env:FACTHORY_OURS
if ($new.Status -ne 'Valid') { [Console]::Error.WriteLine('the installer is not validly signed: ' + $new.Status); exit 3 }
if ($ours.Status -ne 'Valid') { [Console]::Error.WriteLine('this app is not validly signed: ' + $ours.Status); exit 3 }
if ($new.SignerCertificate.Subject -ne $ours.SignerCertificate.Subject) { [Console]::Error.WriteLine('the installer is signed by ' + $new.SignerCertificate.Subject); exit 3 }";
    let mut cmd = Command::new(windows_tool(r"WindowsPowerShell\v1.0\powershell.exe"));
    cmd.args(["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand"])
        .arg(encoded_command(SCRIPT))
        .env("FACTHORY_NEW", msi)
        .env("FACTHORY_OURS", exe);
    output(&mut cmd).map(|_| ())
}

/// Starts the install, which waits for this process to end, and reopens the app if `restart`.
fn finish(install: &Install, restart: bool) -> Result<(), String> {
    let restart = if restart { "1" } else { "0" };
    let pid = std::process::id().to_string();
    match install {
        Install::Bundle { staged, bundle } => {
            // The old bundle moves aside, the new one into its place, and back on a failure.
            const SCRIPT: &str = r#"while kill -0 "$FACTHORY_PID" 2>/dev/null; do sleep 0.2; done
rm -rf "$FACTHORY_OLD"
mv "$FACTHORY_BUNDLE" "$FACTHORY_OLD" || exit 1
if ! mv "$FACTHORY_STAGED" "$FACTHORY_BUNDLE"; then mv "$FACTHORY_OLD" "$FACTHORY_BUNDLE"; exit 1; fi
rm -rf "$FACTHORY_OLD"
if [ "$FACTHORY_RESTART" = 1 ]; then /usr/bin/open "$FACTHORY_BUNDLE"; fi"#;
            let old = bundle.with_file_name(format!(".{}.old", bundle.file_name().map(|n| n.to_string_lossy()).unwrap_or_default()));
            let mut cmd = Command::new("/bin/sh");
            cmd.args(["-c", SCRIPT])
                .env("FACTHORY_PID", &pid)
                .env("FACTHORY_BUNDLE", bundle)
                .env("FACTHORY_STAGED", staged)
                .env("FACTHORY_OLD", old)
                .env("FACTHORY_RESTART", restart);
            detach(&mut cmd)
        }
        Install::Msi { msi, exe, machine } => {
            // msiexec upgrades in place and keeps the app's files until this process has ended. A
            // copy installed for everyone asks for an administrator and needs ALLUSERS=1, without
            // which the installer refuses a silent update of it; one installed for the current
            // account (the default) updates without asking.
            const SCRIPT: &str = "Wait-Process -Id $env:FACTHORY_PID -ErrorAction SilentlyContinue
$msi = '\"' + $env:FACTHORY_MSI + '\"'
$list = @('/i', $msi, '/passive', '/norestart')
if ($env:FACTHORY_ALLUSERS -eq '1') { $list += 'ALLUSERS=1' }
$p = Start-Process -FilePath $env:FACTHORY_MSIEXEC -ArgumentList $list -Wait -PassThru
if ($env:FACTHORY_RESTART -eq '1' -and ($p.ExitCode -eq 0 -or $p.ExitCode -eq 3010)) { Start-Process -FilePath $env:FACTHORY_EXE }";
            let mut cmd = Command::new(windows_tool(r"WindowsPowerShell\v1.0\powershell.exe"));
            cmd.args(["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-EncodedCommand"])
                .arg(encoded_command(SCRIPT))
                .env("FACTHORY_PID", &pid)
                .env("FACTHORY_MSI", msi)
                .env("FACTHORY_MSIEXEC", windows_tool("msiexec.exe"))
                .env("FACTHORY_EXE", exe)
                .env("FACTHORY_ALLUSERS", if *machine { "1" } else { "0" })
                .env("FACTHORY_RESTART", restart);
            detach(&mut cmd)
        }
        Install::AppImage { staged, target } => {
            // The running AppImage stays mounted from the file it opened, so the new one can take
            // its name now.
            std::fs::rename(staged, target).map_err(|e| format!("{}: {e}", target.display()))?;
            if restart == "1" {
                detach(&mut Command::new(target))?;
            }
            Ok(())
        }
    }
}

// ---------------------------------------------------------------------------------------------
// Processes.

/// A system tool by absolute path where it has a fixed one, so no folder on `PATH` can stand in.
fn tool(name: &str) -> PathBuf {
    match std::env::consts::OS {
        "macos" => Path::new("/usr/bin").join(name),
        "windows" => windows_tool(&format!("{name}.exe")),
        _ => PathBuf::from(name),
    }
}

fn windows_tool(name: &str) -> PathBuf {
    let root = std::env::var_os("SystemRoot").map(PathBuf::from).unwrap_or_else(|| PathBuf::from(r"C:\Windows"));
    root.join("System32").join(name)
}

/// Runs `cmd` to its end without a console window; an exit other than success is an error.
fn output(cmd: &mut Command) -> Result<Output, String> {
    no_window(cmd);
    let program = cmd.get_program().to_string_lossy().into_owned();
    let out = cmd.stdin(Stdio::null()).output().map_err(|e| format!("{program}: {e}"))?;
    if out.status.success() { Ok(out) } else { Err(format!("{program}: {} {}", out.status, String::from_utf8_lossy(&out.stderr).trim())) }
}

/// Starts `cmd` on its own, to outlive this process.
fn detach(cmd: &mut Command) -> Result<(), String> {
    no_window(cmd);
    #[cfg(unix)]
    std::os::unix::process::CommandExt::process_group(cmd, 0);
    let program = cmd.get_program().to_string_lossy().into_owned();
    cmd.stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null()).spawn().map(|_| ()).map_err(|e| format!("{program}: {e}"))
}

#[cfg(windows)]
fn no_window(cmd: &mut Command) {
    // CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    std::os::windows::process::CommandExt::creation_flags(cmd, 0x0800_0000 | 0x0000_0200);
}

#[cfg(not(windows))]
fn no_window(_: &mut Command) {}

#[cfg(unix)]
fn make_executable(path: &Path) -> Result<(), String> {
    use std::os::unix::fs::PermissionsExt;
    std::fs::set_permissions(path, std::fs::Permissions::from_mode(0o755)).map_err(|e| format!("{}: {e}", path.display()))
}

#[cfg(not(unix))]
fn make_executable(_: &Path) -> Result<(), String> {
    Ok(())
}

/// A script for PowerShell's `-EncodedCommand`: Base64 of its UTF-16LE text, so no quoting applies.
fn encoded_command(script: &str) -> String {
    const ALPHABET: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let bytes: Vec<u8> = script.encode_utf16().flat_map(u16::to_le_bytes).collect();
    let mut out = String::with_capacity(bytes.len().div_ceil(3) * 4);
    for chunk in bytes.chunks(3) {
        let byte = |i: usize| u32::from(chunk.get(i).copied().unwrap_or(0));
        let n = (byte(0) << 16) | (byte(1) << 8) | byte(2);
        for i in 0..4 {
            out.push(if i <= chunk.len() { char::from(ALPHABET[((n >> (18 - 6 * i)) & 63) as usize]) } else { '=' });
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    const FEED_URL: &str = "https://github.com/FACTHORYAI/page/releases/latest/download/latest.json";
    const SUM: &str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

    fn feed(name: &str, url: &str) -> Vec<u8> {
        serde_json::json!({
            "name": "Facthory Page", "version": "0.11.0", "date": "2026-11-01",
            "assets": {"linux-x86_64": {"name": name, "url": url, "sha256": SUM.to_uppercase(), "size": 123}}
        })
        .to_string()
        .into_bytes()
    }

    fn temp(tag: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!("facthory-update-{tag}-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).unwrap();
        dir
    }

    #[test]
    fn only_a_higher_release_version_is_newer() {
        assert!(newer("0.11.0", "0.10.0"));
        assert!(newer("0.10.1", "0.10.0"));
        assert!(newer("1.0.0", "0.99.99"));
        assert!(!newer("0.10.0", "0.10.0"));
        assert!(!newer("0.9.9", "0.10.0"));
        for odd in ["0.11", "0.11.0.1", "0.11.0-beta.1", "v0.11.0", "", "0.11.x", "+1.0.0"] {
            assert!(!newer(odd, "0.10.0"), "{odd}");
        }
    }

    #[test]
    fn the_feed_gives_this_platforms_file_of_the_same_repository() {
        let url = "https://github.com/FACTHORYAI/page/releases/download/v0.11.0/facthorypage-0.11.0-linux-x86_64.AppImage";
        let f = Feed::parse(&feed("facthorypage-0.11.0-linux-x86_64.AppImage", url), FEED_URL, Some("linux-x86_64")).unwrap();
        assert_eq!(f.version, "0.11.0");
        assert_eq!(f.page, "https://github.com/FACTHORYAI/page/releases/tag/v0.11.0");
        let asset = f.asset.unwrap();
        assert_eq!((asset.url.as_str(), asset.sha256.as_str(), asset.size), (url, SUM, 123));
        // Another platform: the release page only.
        assert_eq!(Feed::parse(&feed("x", url), FEED_URL, Some("windows-x64")).unwrap().asset, None);
    }

    #[test]
    fn the_feed_never_points_elsewhere_or_outside_the_downloads_folder() {
        let parse = |name: &str, url: &str| Feed::parse(&feed(name, url), FEED_URL, Some("linux-x86_64")).unwrap().asset;
        let base = "https://github.com/FACTHORYAI/page/releases/download/v0.11.0/";
        assert_eq!(parse("a.AppImage", "https://example.com/releases/download/v0.11.0/a.AppImage"), None);
        assert_eq!(parse("a.AppImage", "https://github.com/someone/page/releases/download/v0.11.0/a.AppImage"), None);
        assert_eq!(parse("a.AppImage", &format!("{base}b.AppImage")), None);
        for name in ["../a.AppImage", ".a", "a/b", "a\\b", "a b"] {
            assert_eq!(parse(name, &format!("{base}{name}")), None, "{name}");
        }
        assert!(Feed::parse(b"{}", FEED_URL, None).is_err());
        assert!(Feed::parse(b"not json", FEED_URL, None).is_err());
        assert!(Feed::parse(&feed("a", "b"), "http://github.com/FACTHORYAI/page/releases/latest/download/latest.json", None).is_err());
    }

    #[test]
    fn saved_state_round_trips_and_spaces_the_checks() {
        let dir = temp("saved");
        assert_eq!(Saved::load(&dir), Saved { enabled: true, last_check: 0, skip: None });
        Saved::update(&dir, |s| s.last_check = 1_000_000);
        Saved::update(&dir, |s| s.skip = Some("0.11.0".into()));
        let saved = Saved::load(&dir);
        assert_eq!(saved, Saved { enabled: true, last_check: 1_000_000, skip: Some("0.11.0".into()) });
        assert_eq!(saved.wait(1_000_000), INTERVAL);
        assert_eq!(saved.wait(1_000_000 + INTERVAL - 5), 5);
        assert_eq!(saved.wait(1_000_000 + 2 * INTERVAL), 0);
        // A clock set back waits one interval, not until it catches up.
        assert_eq!(saved.wait(10), INTERVAL);
        std::fs::write(dir.join("update.json"), r#"{"enabled": false}"#).unwrap();
        assert!(!Saved::load(&dir).enabled);
        std::fs::write(dir.join("update.json"), "garbage").unwrap();
        assert_eq!(Saved::load(&dir), Saved { enabled: true, last_check: 0, skip: None });
        let _ = std::fs::remove_dir_all(dir);
    }

    #[cfg(unix)]
    #[test]
    fn a_download_is_kept_only_when_it_matches_the_feed() {
        let curl = Command::new(tool("curl")).arg("--version").stdout(Stdio::null()).status();
        if !curl.is_ok_and(|s| s.success()) {
            eprintln!("curl unavailable; skipping");
            return;
        }
        let dir = temp("download");
        let source = dir.join("source.bin");
        std::fs::write(&source, b"the new version").unwrap();
        let (size, sha256) = sha256_file(&source).unwrap();
        let url = format!("file://{}", source.display());
        let asset = Asset { name: "new.bin".into(), url, sha256: sha256.clone(), size };
        let file = dir.join("new.bin");
        download(&asset, &file, "=file").unwrap();
        assert_eq!(std::fs::read(&file).unwrap(), b"the new version");

        let _ = std::fs::remove_file(&file);
        let wrong = Asset { sha256: SUM.into(), ..asset };
        assert!(download(&wrong, &file, "=file").unwrap_err().contains("SHA-256"));
        assert!(!file.exists() && !dir.join("new.bin.part").exists());
        let short = Asset { size: size + 1, sha256, ..wrong };
        assert!(download(&short, &file, "=file").is_err());
        assert!(!file.exists());
        // Only the protocols given.
        assert!(download(&short, &file, "=https").is_err());
        let _ = std::fs::remove_dir_all(dir);
    }

    #[test]
    fn sha256_matches_the_standards_examples_however_the_input_is_split() {
        let hex = |d: [u8; 32]| d.iter().map(|b| format!("{b:02x}")).collect::<String>();
        let digest = |parts: &[&[u8]]| {
            let mut h = Sha256::new();
            parts.iter().for_each(|p| h.update(p));
            hex(h.finish())
        };
        assert_eq!(digest(&[]), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
        assert_eq!(digest(&[b"abc"]), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
        let two_blocks = b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";
        assert_eq!(digest(&[two_blocks]), "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1");
        for at in 0..two_blocks.len() {
            let (a, b) = two_blocks.split_at(at);
            assert_eq!(digest(&[a, b]), "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1", "{at}");
        }
        let million = vec![b'a'; 1_000_000];
        assert_eq!(digest(&[&million]), "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
        assert_eq!(digest(&million.chunks(997).collect::<Vec<_>>()), "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
    }

    #[test]
    fn sha256_of_a_file() {
        let dir = temp("sha");
        let path = dir.join("abc");
        std::fs::write(&path, b"abc").unwrap();
        assert_eq!(sha256_file(&path).unwrap(), (3, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad".to_owned()));
        let _ = std::fs::remove_dir_all(dir);
    }

    #[test]
    fn powershell_gets_its_script_encoded() {
        // UTF-16LE "A" = 41 00; "AB" = 41 00 42 00.
        assert_eq!(encoded_command("A"), "QQA=");
        assert_eq!(encoded_command("AB"), "QQBCAA==");
        assert_eq!(encoded_command(""), "");
    }

    #[test]
    fn the_msi_upgrades_only_the_copies_it_installed_in_their_own_scope() {
        let pf = [PathBuf::from("/pf"), PathBuf::from("/pf64")];
        let local = Some(Path::new("/users/a/local"));
        assert_eq!(msi_scope(Path::new("/pf64/Facthory/Facthory Page/facthorypage.exe"), &pf, local), Some(true));
        assert_eq!(msi_scope(Path::new("/users/a/local/Programs/Facthory/Facthory Page/facthorypage.exe"), &pf, local), Some(false));
        // A portable zip, unpacked anywhere else, or beside Programs rather than under it.
        assert_eq!(msi_scope(Path::new("/users/a/Downloads/facthorypage/facthorypage.exe"), &pf, local), None);
        assert_eq!(msi_scope(Path::new("/users/a/local/ProgramsOld/facthorypage.exe"), &pf, local), None);
        assert_eq!(msi_scope(Path::new("/users/a/local/Programs/x.exe"), &pf, None), None);
    }

    #[test]
    fn the_installers_record_is_read_from_reg_query() {
        let out = "\r\nHKEY_CURRENT_USER\\Software\\Facthory Page\r\n    InstallDir    REG_SZ    C:\\Users\\a\\AppData\\Local\\Programs\\Facthory\\Facthory Page\\\r\n\r\n";
        assert_eq!(reg_value(out, "InstallDir").as_deref(), Some(r"C:\Users\a\AppData\Local\Programs\Facthory\Facthory Page\"));
        assert_eq!(reg_value("    InstallDir    REG_EXPAND_SZ    %LOCALAPPDATA%\\X\r\n", "InstallDir").as_deref(), Some(r"%LOCALAPPDATA%\X"));
        assert_eq!(reg_value("ERROR: The system was unable to find the specified registry key or value.\r\n", "InstallDir"), None);
        assert_eq!(reg_value("    InstallDirOld    REG_SZ    C:\\x\r\n", "InstallDir"), None);
    }

    #[test]
    fn the_new_version_waits_hidden_beside_the_old() {
        assert_eq!(staged_beside(Path::new("/Applications/Facthory Page.app")), Path::new("/Applications/.Facthory Page.app.update"));
        assert_eq!(staged_beside(Path::new("/home/a/Apps/facthorypage.AppImage")), Path::new("/home/a/Apps/.facthorypage.AppImage.update"));
    }

    #[cfg(unix)]
    #[test]
    fn an_appimage_update_takes_the_old_ones_place() {
        let dir = temp("appimage");
        let (target, file) = (dir.join("app.AppImage"), dir.join("downloaded"));
        std::fs::write(&target, b"old").unwrap();
        std::fs::write(&file, b"new").unwrap();
        let install = Method::AppImage(target.clone()).prepare(&file, &dir).unwrap();
        let staged = dir.join(".app.AppImage.update");
        assert_eq!(install, Install::AppImage { staged: staged.clone(), target: target.clone() });
        use std::os::unix::fs::PermissionsExt;
        assert_eq!(std::fs::metadata(&staged).unwrap().permissions().mode() & 0o777, 0o755);
        finish(&install, false).unwrap();
        assert_eq!(std::fs::read(&target).unwrap(), b"new");
        assert!(!staged.exists());
        let _ = std::fs::remove_dir_all(dir);
    }
}
