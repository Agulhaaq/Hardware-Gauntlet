"""Build branding assets for Hardware Gauntlet from source image."""
import os
import base64
import numpy as np
from PIL import Image, ImageDraw

def build_assets():
    src_path = r"C:/Users/agulh/.gemini/antigravity/brain/4af674bf-8467-4808-baa3-d130b14d0146/.user_uploaded/media_1791315361007.png"
    assets_dir = os.path.abspath("assets")
    os.makedirs(assets_dir, exist_ok=True)

    print(f"Loading source image from {src_path}...")
    img = Image.open(src_path).convert("L")
    arr = np.array(img, dtype=float)
    
    # Bounding box of emblem: Y in [85, 487], X in [334, 689]
    crop = arr[85:488, 334:690]  # height=403, width=356

    # Compute antialiased alpha matte
    alpha = np.clip((245.0 - crop) / (245.0 - 15.0) * 255.0, 0, 255).astype(np.uint8)

    # Tight white emblem RGBA
    white_arr = np.zeros((403, 356, 4), dtype=np.uint8)
    white_arr[:, :, 0:3] = 255
    white_arr[:, :, 3] = alpha
    white_tight = Image.fromarray(white_arr, "RGBA")

    # Tight black emblem RGBA
    black_arr = np.zeros((403, 356, 4), dtype=np.uint8)
    black_arr[:, :, 0:3] = 0
    black_arr[:, :, 3] = alpha
    black_tight = Image.fromarray(black_arr, "RGBA")

    # 1. Master 1024x1024 transparent canvases
    master_w, master_h = 1024, 1024
    target_h = 820
    target_w = int(round(target_h * (356.0 / 403.0)))
    pad_x = (master_w - target_w) // 2
    pad_y = (master_h - target_h) // 2

    # Scaled white master
    scaled_white = white_tight.resize((target_w, target_h), Image.Resampling.LANCZOS)
    logo_white_1024 = Image.new("RGBA", (master_w, master_h), (0, 0, 0, 0))
    logo_white_1024.paste(scaled_white, (pad_x, pad_y), scaled_white)
    logo_white_1024.save(os.path.join(assets_dir, "logo_white.png"), format="PNG")

    # Scaled black master
    scaled_black = black_tight.resize((target_w, target_h), Image.Resampling.LANCZOS)
    logo_black_1024 = Image.new("RGBA", (master_w, master_h), (0, 0, 0, 0))
    logo_black_1024.paste(scaled_black, (pad_x, pad_y), scaled_black)
    logo_black_1024.save(os.path.join(assets_dir, "logo_black.png"), format="PNG")

    # 2. Scaled logo PNG variants (16, 32, 48, 64, 128)
    for sz in [16, 32, 48, 64, 128]:
        s_target_h = int(sz * 0.84)
        s_target_w = int(round(s_target_h * (356.0 / 403.0)))
        s_pad_x = (sz - s_target_w) // 2
        s_pad_y = (sz - s_target_h) // 2

        w_small = white_tight.resize((s_target_w, s_target_h), Image.Resampling.LANCZOS)
        c_white = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        c_white.paste(w_small, (s_pad_x, s_pad_y), w_small)
        c_white.save(os.path.join(assets_dir, f"logo_white_{sz}.png"), format="PNG")

        b_small = black_tight.resize((s_target_w, s_target_h), Image.Resampling.LANCZOS)
        c_black = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        c_black.paste(b_small, (s_pad_x, s_pad_y), b_small)
        c_black.save(os.path.join(assets_dir, f"logo_black_{sz}.png"), format="PNG")

    # 3. App squircle icon (1024x1024)
    app_icon = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    ss = 2
    ss_w, ss_h = 1024 * ss, 1024 * ss
    ss_mask = Image.new("L", (ss_w, ss_h), 0)
    ss_draw = ImageDraw.Draw(ss_mask)
    radius = 210 * ss
    margin = 24 * ss
    ss_draw.rounded_rectangle([margin, margin, ss_w - margin, ss_h - margin], radius=radius, fill=255)
    mask = ss_mask.resize((1024, 1024), Image.Resampling.LANCZOS)

    # Dark obsidian card background (#09090b)
    bg_card = Image.new("RGBA", (1024, 1024), (9, 9, 11, 255))
    border_draw = ImageDraw.Draw(bg_card)
    border_draw.rounded_rectangle([24, 24, 1000, 1000], radius=210, outline=(39, 39, 42, 255), width=6)

    # Overlay white emblem
    emblem_h = 580
    emblem_w = int(round(emblem_h * (356.0 / 403.0)))
    emb_scaled = white_tight.resize((emblem_w, emblem_h), Image.Resampling.LANCZOS)
    e_px = (1024 - emblem_w) // 2
    e_py = (1024 - emblem_h) // 2
    bg_card.paste(emb_scaled, (e_px, e_py), emb_scaled)

    app_icon.paste(bg_card, (0, 0), mask)
    app_icon.save(os.path.join(assets_dir, "app.png"), format="PNG")

    # 4. Multi-resolution Windows ICO
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    app_icon.save(os.path.join(assets_dir, "app.ico"), format="ICO", sizes=ico_sizes)

    # 5. Base64 encoded logos in assets_data.py
    with open(os.path.join(assets_dir, "logo_white_64.png"), "rb") as f:
        b64_white = base64.b64encode(f.read()).decode("ascii")

    with open(os.path.join(assets_dir, "logo_black_64.png"), "rb") as f:
        b64_black = base64.b64encode(f.read()).decode("ascii")

    assets_data_path = os.path.abspath("hwscan/assets_data.py")
    with open(assets_data_path, "w", encoding="utf-8") as f:
        f.write("# Generated logo assets\n")
        f.write(f'LOGO_WHITE_B64 = "{b64_white}"\n')
        f.write(f'LOGO_BLACK_B64 = "{b64_black}"\n')

    print("All branding assets generated and assets_data.py updated successfully!")

if __name__ == "__main__":
    build_assets()
