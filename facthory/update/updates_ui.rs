//! Updates in Facthory Page: part of the Facthory patch set (`facthory/update/`), copied over
//! upstream's `updates_ui.rs` when the brand is applied. Upstream's update flow (craft-update)
//! checks and installs the upstream apps' releases, so it is not built in. The app updates itself
//! through `facthory_update` instead, which reads our releases' feed once a day and installs a new
//! version as the app quits. Help ▸ Check for Updates opens the latest release's page.

use crate::WordApp;

const RELEASES: &str = "https://github.com/FACTHORYAI/page/releases/latest";

#[derive(Default)]
pub(crate) struct Runtime {
    /// Help ▸ Check for Updates was chosen; the next frame opens the releases page.
    open_releases: bool,
}

impl WordApp {
    /// Upstream's switch for its check at start; `facthory_update` decides when to check.
    pub fn set_startup_update_check(&mut self, _on: bool) {}

    /// Upstream's switch for a process that still carries another program's AppImage variables;
    /// `facthory_update::disable` (called beside it in main.rs) is the one that turns updates off.
    pub fn disable_self_update(&mut self) {}

    /// Upstream starts the helper of a ready update here; `facthory_update::on_exit` installs ours.
    pub fn start_pending_update(&mut self) {}
}

pub(crate) fn check(app: &mut WordApp) {
    app.updates_rt.open_releases = true;
}

pub(crate) fn tick(_app: &mut WordApp, _ctx: &egui::Context) {}

pub(crate) fn show(app: &mut WordApp, ctx: &egui::Context) {
    if std::mem::take(&mut app.updates_rt.open_releases) {
        ctx.open_url(egui::OpenUrl::new_tab(RELEASES));
    }
}
