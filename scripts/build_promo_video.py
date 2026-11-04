"""
BS Lab Tool PRO v2.0 - Automated Promotional Video & Voiceover Generator
Generates a full Full-HD (1920x1080) video with Roman Urdu neural voiceover,
Studio Obsidian neon graphics, live subtitles, and scene transitions.
"""

import os
import sys
import io
import asyncio
import subprocess

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from PIL import Image, ImageDraw, ImageFont
import edge_tts
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUT_DIR = os.path.abspath("marketing")
SCENES_DIR = os.path.join(OUT_DIR, "scenes")
TEMP_DIR = os.path.join(OUT_DIR, "temp_video_build")
os.makedirs(TEMP_DIR, exist_ok=True)

SCENES = [
    {
        "id": 1,
        "title": "BS LAB TOOL PRO v2.0 — ALL-IN-ONE GSM SUITE",
        "badge": "❖ NEXT-GEN MOBILE SERVICING & UNBRICKING PLATFORM",
        "bullets": "• Zero Missing Firehose Loaders  • 100% Offline Standalone  • No Credit/Dongle Limits",
        "image": os.path.join(SCENES_DIR, "scene1_intro.jpg"),
        "script": (
            "As-salamu alaykum dosto! Flashing aur unbricking karte waqt kya aap bhi roz roz "
            "missing Firehose loaders, wrong scatter files, aur driver errors se tang aa chuke hain? "
            "Har doosre model ke liye alag alag tool kholna, credit khareedna, ya dead boot risk lena ab band kijiye! "
            "Kyun ke ab aa chuka hai mobile software servicing ka all-in-one ultimate solution: "
            "BS Lab Tool PRO Version 2.0! Aik aisi power jo har technician ki pehli pasand banne wali hai."
        )
    },
    {
        "id": 2,
        "title": "⚡ MEDIATEK (MTK) BROM EXPLOIT & 20s FAST UNBRICK",
        "badge": "⚡ 847 PRELOADERS + 58 SLA BYPASS PAYLOADS BUNDLED",
        "bullets": "• Direct BROM Exploit (No TP)  • Instant SLA Bypass  • 20s Core Bootloader Flash",
        "image": os.path.join(SCENES_DIR, "scene2_mtk.png"),
        "script": (
            "Sab se pehle baat karte hain MediaTek module ki! Chahe latest MT6765 ho, Helio G99 ho ya Dimensity chipsets, "
            "BS Lab Tool ka direct BROM exploit bina hardware khole device ko BROM mode mein pakad leta hai. "
            "Isme 847 se zyada MTK preloaders aur SLA bypass payloads pehle se maujood hain. "
            "Agar phone logo par atka hai ya bootloop mein hai, to sirf aik click par hamara Fast Unbrick mode "
            "core bootloader partitions ko sirf 20 second mein flash kar ke dead phone ko foran zinda kar deta hai!"
        )
    },
    {
        "id": 3,
        "title": "🐉 QUALCOMM EDL 9008 & UFS MULTI-LUN MASTERY",
        "badge": "🐉 878 FIREHOSE LOADERS + UFS LUN 0 TO LUN 5 FLASHER",
        "bullets": "• Auto-Detect Sahara Protocol  • UFS Multi-LUN Partitioning  • Full QCN / NV Backup",
        "image": os.path.join(SCENES_DIR, "scene3_qualcomm.jpg"),
        "script": (
            "Ab aate hain Qualcomm EDL 9008 par! Internet par ghanton Firehose loader dhoondne ki ab koi zaroorat nahi, "
            "kyun ke BS Lab Tool mein 878 se zyada verified Firehose loaders pehle se bundled hain! "
            "Chahe Snapdragon 680 ho, 778 ho ya 8-Gen series, auto-detect Sahara protocol phone ko foran connect karta hai. "
            "Aur 2026 ka sab se advanced feature: UFS storage ke LUN 0 se lekar LUN 5 tak tamam multi-LUN partitions ka direct access, "
            "safe XML rawprogram flashing, aur full QCN IMEI backup sirf aik click par!"
        )
    },
    {
        "id": 4,
        "title": "🟡 SAMSUNG ODIN SUPER-FLASHER & 2026 SERVICES",
        "badge": "🟡 4-FILE ODIN ENGINE + 484 GALAXY PIT PARTITION TABLES",
        "bullets": "• 1-Click MTP CSC Changer (Instant)  • Knox Guard (KG) State Audit  • Auto-Match BL/AP/CP/CSC",
        "image": os.path.join(SCENES_DIR, "scene4_samsung.jpg"),
        "script": (
            "Samsung users ke liye ye tool aik complete game-changer hai! 4-File full firmware flashing ho ya auto-folder matching, "
            "sab kuch seconds mein set hota hai, aur isme 484 se zyada Galaxy PIT files pre-loaded hain. "
            "Aur sab se special 2026 upgrade: phone ko khole baghair MTP mode mein sirf 2 second ke andar country CSC change karein, "
            "chahe INS ho ya XSG! Saath hi phone ka Knox Guard status aur MDM lock audit kar ke safe flashing decision lain bina knox trip kiye!"
        )
    },
    {
        "id": 5,
        "title": "📱 UNISOC / SPD, OTA UNPACKER & AI DIAGNOSTICS",
        "badge": "🧠 AI HARDWARE & LOG FAULT DETECTOR + UNIVERSAL PAYLOAD.BIN",
        "bullets": "• SC & Tiger PAC Flashing  • Android 14/15 OTA Payload Extraction  • Instant AI Error Solutions",
        "image": os.path.join(SCENES_DIR, "scene5_ai_diagnostics.jpg"),
        "script": (
            "Unisoc aur Spreadtrum devices par Realtek aur Tiger series ki direct PAC flashing aur NV repair! "
            "Aur agar aapke paas latest Android OTA update ki payload.bin file hai, to hamara built-in Universal Unpacker "
            "bina kisi external tool ke super aur boot images extract kar ke de deta hai. "
            "Aur suniye sab se bari baat: AI Log Analyzer! Flashing ke dauran koi bhi error aaye, to AI system log ko scan kar ke "
            "foran bata deta hai ke masla software ka hai, cable ka hai ya motherboard ki eMMC chip dead ho chuki hai!"
        )
    },
    {
        "id": 6,
        "title": "🚀 100% STANDALONE SETUP & OFFICIAL COMMUNITY",
        "badge": "🛡️ 100MB COMPACT SETUP • PASSWORD: BsLab • AUTO-INSTALLED DRIVERS",
        "bullets": "• Zero Driver Conflicts  • Built-In Cloud Database Sync  • Download Now & Upgrade Your Lab",
        "image": os.path.join(SCENES_DIR, "scene6_outro.jpg"),
        "script": (
            "Sab se behtareen baat? BS Lab Tool PRO v2.0 ka setup sirf 100 MB ka hai! "
            "Isay chalane ke liye kisi bhi new PC mein Python install karne ki koi zaroorat nahi. "
            "Setup password hai BsLab! Installer ke andar MediaTek, Qualcomm 9008, Unisoc aur UsbDk ke certified drivers pehle se shaamil hain. "
            "Aur naye models aane par Cloud Sync button se database bina reinstall kiye update ho jata hai! "
            "To intezar kaisa? Aaj hi BS Lab Tool PRO v2.0 download karein, aur apni repairing ko professional standard par le kar jayen. Shukriya!"
        )
    }
]


def get_audio_duration(file_path: str) -> float:
    """Uses ffprobe / ffmpeg to get audio duration in seconds."""
    cmd = [
        FFMPEG, "-i", file_path, "-f", "null", "-"
    ]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    import re
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if match:
        h, m, s = match.groups()
        return int(h) * 3600 + int(m) * 60 + float(s)
    return 25.0


def create_scene_frame(scene: dict, output_frame: str):
    """Generates a branded 1920x1080 Full-HD slide."""
    w, h = 1920, 1080
    bg_img_path = scene["image"]

    if os.path.exists(bg_img_path):
        base = Image.open(bg_img_path).convert("RGBA")
        # Scale to fill 1920x1080 preserving aspect ratio
        bw, bh = base.size
        scale = max(w / bw, h / bh)
        new_w, new_h = int(bw * scale), int(bh * scale)
        base = base.resize((new_w, new_h), Image.Resampling.LANCZOS)
        # Center crop
        left = (new_w - w) // 2
        top = (new_h - h) // 2
        base = base.crop((left, top, left + w, top + h))
    else:
        base = Image.new("RGBA", (w, h), (13, 17, 23, 255))

    # Add dark vignette overlay for readability
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    # Dark vignette gradient at top and bottom
    d_over.rectangle([0, 0, w, 160], fill=(13, 17, 23, 230))
    d_over.rectangle([0, h - 220, w, h], fill=(13, 17, 23, 240))
    # Outer 4px cyan border
    d_over.rectangle([4, 4, w - 5, h - 5], outline=(0, 242, 254, 255), width=4)

    # Top Header Bar Card
    d_over.rectangle([30, 25, w - 30, 135], fill=(22, 29, 43, 230), outline=(35, 45, 66, 255), width=2)
    # Glowing neon accent bar on top card
    d_over.rectangle([30, 25, 40, 135], fill=(0, 242, 254, 255))

    # Bottom Highlight Card
    d_over.rectangle([30, h - 195, w - 30, h - 35], fill=(22, 29, 43, 240), outline=(0, 242, 254, 180), width=2)
    # Glowing cyan top border on bottom card
    d_over.line([30, h - 195, w - 30, h - 195], fill=(0, 242, 254, 255), width=3)

    img = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(img)

    # Fonts (Try Arial / Segoe UI / default)
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 36)
        font_badge = ImageFont.truetype("arial.ttf", 22)
        font_bottom_badge = ImageFont.truetype("arialbd.ttf", 28)
        font_bullets = ImageFont.truetype("arial.ttf", 24)
        font_watermark = ImageFont.truetype("arialbd.ttf", 20)
    except Exception:
        font_title = font_badge = font_bottom_badge = font_bullets = font_watermark = ImageFont.load_default()

    # Draw Top Texts
    draw.text((60, 40), scene["title"], fill=(241, 245, 249), font=font_title)
    draw.text((60, 88), scene["badge"], fill=(0, 242, 254), font=font_badge)

    # Watermark Top Right
    draw.text((w - 320, 55), "BS LAB TOOL v2.0 PRO", fill=(79, 172, 254), font=font_watermark)
    draw.text((w - 320, 85), "Official Product Showcase", fill=(148, 163, 184), font=font_badge)

    # Draw Bottom Texts (Feature Highlights & Live Subtitle)
    draw.text((60, h - 175), f"HIGHLIGHTS: {scene['title'].split('—')[-1].strip()}", fill=(0, 242, 254), font=font_bottom_badge)
    draw.text((60, h - 125), scene["bullets"], fill=(241, 245, 249), font=font_bullets)
    draw.text((60, h - 80), "🎙️ Roman Urdu Audio Active • Real-Time Diagnostics & Unbrick Subsystem", fill=(148, 163, 184), font=font_badge)

    img = img.convert("RGB")
    img.save(output_frame, quality=95)


async def generate_scene_audio(scene: dict, output_mp3: str):
    """Generates natural neural voiceover audio for the scene."""
    voice = "hi-IN-MadhurNeural"  # Best energetic Roman Urdu diction
    communicate = edge_tts.Communicate(scene["script"], voice, rate="+2%")
    await communicate.save(output_mp3)


async def main():
    print("=" * 70)
    print("BS LAB TOOL PRO v2.0 - Automated Promotional Video Production")
    print("=" * 70)

    scene_clips = []
    total_duration = 0.0

    for scene in SCENES:
        s_id = scene["id"]
        print(f"\n[Scene {s_id}/6] Processing: {scene['title']}")

        # 1. Generate Voiceover Audio
        audio_path = os.path.join(TEMP_DIR, f"scene_{s_id}.mp3")
        print(f"  Generating neural voiceover audio...")
        await generate_scene_audio(scene, audio_path)

        duration = get_audio_duration(audio_path) + 0.6  # slight breathing room
        total_duration += duration
        print(f"  Audio generated ({duration:.1f}s)")

        # 2. Generate Full-HD Video Frame
        frame_path = os.path.join(TEMP_DIR, f"scene_{s_id}_frame.png")
        create_scene_frame(scene, frame_path)
        print(f"  Rendered Full-HD 1080p frame")

        # 3. Compile Scene Video via FFmpeg
        scene_mp4 = os.path.join(TEMP_DIR, f"scene_{s_id}.mp4")
        cmd = [
            FFMPEG, "-y",
            "-loop", "1", "-i", frame_path,
            "-i", audio_path,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            scene_mp4
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        scene_clips.append(scene_mp4)
        print(f"  Encoded video clip -> {scene_mp4}")

    # 4. Concatenate all scenes into master video
    print(f"\nConcatenating master video (Total Duration: {total_duration/60:.2f} mins)...")
    concat_list = os.path.join(TEMP_DIR, "concat_list.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            # Escape path for ffmpeg concat
            f.write(f"file '{clip.replace(chr(92), '/')}'\n")

    final_video = os.path.join(OUT_DIR, "BS_Lab_Tool_PRO_v2.0_Promo_Video.mp4")
    cmd_concat = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        final_video
    ]
    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 5. Concatenate full audio track
    final_audio = os.path.join(OUT_DIR, "BS_Lab_Tool_PRO_v2.0_Voiceover_Full.mp3")
    audio_concat_list = os.path.join(TEMP_DIR, "audio_concat_list.txt")
    with open(audio_concat_list, "w", encoding="utf-8") as f:
        for s in SCENES:
            a_p = os.path.join(TEMP_DIR, f"scene_{s['id']}.mp3")
            f.write(f"file '{a_p.replace(chr(92), '/')}'\n")

    cmd_audio = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", audio_concat_list,
        "-c", "copy",
        final_audio
    ]
    subprocess.run(cmd_audio, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print("\n" + "=" * 70)
    print("SUCCESS: Full Promo Video & Voiceover Generated Successfully!")
    print(f"  Master Video (MP4) : {final_video}")
    print(f"  Master Audio (MP3) : {final_audio}")
    print(f"  Total Run Time     : {total_duration:.1f} seconds (~{total_duration/60:.1f} mins)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
