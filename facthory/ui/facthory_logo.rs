//! Facthory's mark in the About box: part of the Facthory patch set (`facthory/ui/`), copied into
//! `crates/ui-egui/src/` when the brand is applied. Upstream's About box shows no logo.
//!
//! The two files are renders of `facthory/icons/brand/mark.svg` (for light grounds) and
//! `mark-mono.svg` (white and greys, for dark ones), scaled and nothing else
//! (`facthory/icons/render.py`). The one that matches the window's theme is drawn.

use egui::{ColorImage, Context, Id, TextureHandle, TextureOptions, Ui, Vec2};

const LIGHT: &[u8] = include_bytes!("../../../assets/app-icon/facthorypage-logo-light.png");
const DARK: &[u8] = include_bytes!("../../../assets/app-icon/facthorypage-logo-dark.png");

/// The mark's height in points.
const HEIGHT: f32 = 72.0;

/// The texture of the mark for the theme, decoded once; `None` when the file can't be read.
fn texture(ctx: &Context, dark: bool) -> Option<TextureHandle> {
    let id = Id::new(if dark { "facthory.logo.dark" } else { "facthory.logo.light" });
    if let Some(t) = ctx.data(|d| d.get_temp::<TextureHandle>(id)) {
        return Some(t);
    }
    let rgba = image::load_from_memory(if dark { DARK } else { LIGHT }).ok()?.to_rgba8();
    let size = [usize::try_from(rgba.width()).ok()?, usize::try_from(rgba.height()).ok()?];
    let handle = ctx.load_texture(id.short_debug_format(), ColorImage::from_rgba_unmultiplied(size, rgba.as_raw()), TextureOptions::LINEAR);
    ctx.data_mut(|d| d.insert_temp(id, handle.clone()));
    Some(handle)
}

/// Draws the mark for the current theme, in its own proportions.
pub(crate) fn show(ui: &mut Ui) {
    let dark = ui.visuals().dark_mode;
    let Some(texture) = texture(ui.ctx(), dark) else { return };
    let size = texture.size_vec2();
    if size.y <= 0.0 {
        return;
    }
    let drawn = Vec2::new(HEIGHT * size.x / size.y, HEIGHT);
    ui.image(egui::load::SizedTexture::new(texture.id(), drawn));
    ui.add_space(4.0);
}
