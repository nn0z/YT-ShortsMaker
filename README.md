# 🎬 YT-ShortsMaker

A simple Python tool that downloads YouTube videos and splits them into short, ready-to-upload clips — perfect for creating content for **YouTube Shorts**, **Instagram Reels**, and **TikTok**.

Works with a single video or an entire channel, lets you pick one or many videos at once, and organizes everything into clean folders.

---

## ✨ Features

- 📺 Download from a **YouTube channel** or a **single video**
- ✂️ Split videos into **custom-length segments** (perfect for Shorts)
- 🎯 Select **one, many, or a range** of videos at once
- 📁 **Organized folder structure** for every session
- ⚙️ **Zero setup** — ffmpeg is downloaded automatically
- 🚀 Ready-to-upload clips for **Shorts, Reels, and TikTok**

---

## 📦 Requirements

- **Python 3.8+**
- **Internet connection** (only for the first run, to fetch ffmpeg)

---

## 🎮 How to Use

1. Run the tool:

   ```bash
   python main.py
   ```

2. Wait for ffmpeg to be prepared automatically.

3. Choose the **segment duration** in seconds (default: 120 seconds = 2 minutes).

4. Choose a source:
   - **📺 Channel** — paste a channel URL, then pick videos by number
   - **🎬 Single Video** — paste a video URL directly

5. Sit back — videos will be downloaded and split automatically.

---

## 📁 Output Structure

```
youtube-shorts/
└── shorts(1)/
    ├── Video Title 1/
    │   ├── Video Title 1.mp4
    │   ├── segment_01.mp4
    │   ├── segment_02.mp4
    │   └── ...
    └── Video Title 2/
        ├── Video Title 2.mp4
        ├── segment_01.mp4
        └── ...
```

## 📌 Use Cases

- 📱 Create YouTube Shorts from long videos
- 🎞️ Make Instagram Reels from podcast episodes
- 🎵 Cut TikTok clips from interviews
- 🗂️ Archive channel content into small, organized chunks

---

## ⚠️ Disclaimer

This tool is intended for **personal use only**. Please respect copyright laws and YouTube's Terms of Service. Do not download or redistribute content you do not own or have permission to use.

---

## ⭐ Support

If you find this tool useful, please consider giving it a **star** ⭐ on GitHub — it helps others discover the project !
