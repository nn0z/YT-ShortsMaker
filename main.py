import re
import os
import subprocess
import sys
import shutil
from bs4 import BeautifulSoup
import requests


class VideoDownloaderSplitter:
    def __init__(self, segment_duration=120):
        self.videos = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        self.main_folder = "youtube-shorts"
        self.current_session = 1
        self.ffmpeg_path = None
        self.ffprobe_path = None
        self.segment_duration = segment_duration

    def setup_ffmpeg(self):
        print("\n╔" + "═" * 58 + "╗")
        print("║" + "  ⚙️   PREPARING FFMPEG  ".center(58) + "║")
        print("╠" + "═" * 58 + "╣")
        print("║" + "  Checking for ffmpeg...".ljust(58) + "║")
        print("╚" + "═" * 58 + "╝")

        try:
            from static_ffmpeg import run
        except ImportError:
            print("\n⚠️  static-ffmpeg not installed. Installing...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "static-ffmpeg", "--quiet"]
                )
                from static_ffmpeg import run
            except Exception as e:
                print(f"❌ Failed to install static-ffmpeg: {e}")
                print("   Please run: pip install static-ffmpeg")
                return False

        try:
            ffmpeg_path, ffprobe_path = run.get_or_fetch_platform_executables_else_raise()
            self.ffmpeg_path = ffmpeg_path
            self.ffprobe_path = ffprobe_path

            print("\n╔" + "═" * 58 + "╗")
            print("║" + "  ✅  FFMPEG READY  ".center(58) + "║")
            print("╠" + "═" * 58 + "╣")
            print("║" + f"  📁 ffmpeg:  {os.path.basename(ffmpeg_path)}".ljust(58) + "║")
            print("║" + f"  📁 ffprobe: {os.path.basename(ffprobe_path)}".ljust(58) + "║")
            print("╚" + "═" * 58 + "╝")
            return True

        except Exception as e:
            print(f"\n❌ Failed to prepare ffmpeg: {e}")
            print("   Videos will be downloaded but NOT split.")
            return False

    def get_channel_videos(self, channel_url, limit=50):
        print(f"\n🔍 Fetching videos from channel...")

        try:
            import yt_dlp

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'force_generic_extractor': False,
                'ignoreerrors': True,
            }

            if not channel_url.endswith('/videos') and '/videos' not in channel_url:
                if channel_url.endswith('/'):
                    channel_url = channel_url + 'videos'
                else:
                    channel_url = channel_url + '/videos'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)

                if info and 'entries' in info:
                    videos = []
                    count = 0
                    for entry in info['entries']:
                        if count >= limit:
                            break
                        if entry and 'id' in entry:
                            video_id = entry.get('id')
                            title = entry.get('title', 'No Title')
                            duration = entry.get('duration', None)
                            view_count = entry.get('view_count', None)
                            upload_date = entry.get('upload_date', None)

                            if video_id:
                                videos.append({
                                    'title': title,
                                    'url': f"https://www.youtube.com/watch?v={video_id}",
                                    'video_id': video_id,
                                    'duration': duration,
                                    'view_count': view_count,
                                    'upload_date': upload_date
                                })
                                count += 1

                    if videos:
                        self.videos = videos
                        self.display_videos()
                        return True
        except Exception as e:
            print(f"⚠️ yt-dlp method failed: {e}")

        try:
            response = requests.get(channel_url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/watch\?v='))

            videos = []
            seen = set()

            for link in links:
                if len(videos) >= limit:
                    break

                href = link.get('href', '')
                if href in seen:
                    continue

                match = re.search(r'/watch\?v=([^&]+)', href)
                if not match:
                    continue

                video_id = match.group(1)
                seen.add(href)

                title = link.get('title', '')
                if not title:
                    title_elem = link.find('yt-formatted-string')
                    if title_elem:
                        title = title_elem.text.strip()
                    else:
                        text = link.text.strip()
                        if text:
                            title = text

                if title and video_id:
                    videos.append({
                        'title': title,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'video_id': video_id,
                        'duration': None,
                        'view_count': None,
                        'upload_date': None
                    })

            if videos:
                self.videos = videos
                self.display_videos()
                return True
        except Exception as e:
            print(f"⚠️ scraping method failed: {e}")

        print("❌ No videos found")
        return False

    def get_video_info(self, video_url):
        print(f"\n🔍 Fetching video info...")

        try:
            import yt_dlp

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'nocheckcertificate': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web', 'ios'],
                        'skip': ['hls', 'dash'],
                        'player_skip': ['configs'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(video_url, download=False)
                except Exception:
                    print(f"⚠️ Full extraction failed, trying flat extraction...")
                    ydl_opts['extract_flat'] = True
                    ydl_opts.pop('extractor_args', None)
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        info = ydl2.extract_info(video_url, download=False)

                if info:
                    video = {
                        'title': info.get('title', 'No Title'),
                        'url': video_url,
                        'video_id': info.get('id', ''),
                        'duration': info.get('duration', None),
                        'view_count': info.get('view_count', None),
                        'upload_date': info.get('upload_date', None),
                        'uploader': info.get('uploader', None),
                    }
                    self.videos = [video]
                    self.display_videos()
                    return True
        except Exception as e:
            print(f"⚠️ Failed to fetch video info: {e}")

        return False

    def format_duration(self, seconds):
        if not seconds:
            return "N/A"
        minutes = seconds // 60
        secs = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def format_views(self, views):
        if not views:
            return "N/A"
        if views >= 1_000_000_000:
            return f"{views / 1_000_000_000:.1f}B"
        if views >= 1_000_000:
            return f"{views / 1_000_000:.1f}M"
        if views >= 1_000:
            return f"{views / 1_000:.1f}K"
        return str(views)

    def format_date(self, date_str):
        if not date_str:
            return "N/A"
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str

    def display_videos(self):
        print("\n" + "=" * 90)
        print(f"🎬 Available videos ({len(self.videos)}):")
        print("=" * 90)

        for i, video in enumerate(self.videos, 1):
            title = video['title'].replace('\u0026', '&').strip()
            print(f"\n{i}. 📹 {title}")
            print(f"   🔗 {video['url']}")
            print(f"   ⏱️ Duration: {self.format_duration(video.get('duration'))}")
            print(f"   👁️ Views: {self.format_views(video.get('view_count'))}")
            print(f"   📅 Uploaded: {self.format_date(video.get('upload_date'))}")
            print("-" * 90)

    def get_video_duration(self, video_path):
        try:
            cmd = [
                self.ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            result = subprocess.check_output(cmd, text=True)
            return float(result.strip())
        except:
            return None

    def split_video(self, input_path, output_folder, segment_duration=None):
        if segment_duration is None:
            segment_duration = self.segment_duration

        print(f"\n✂️ Splitting video into {segment_duration}-second segments...")

        if not self.ffmpeg_path:
            print("❌ ffmpeg not available. Cannot split video.")
            return False

        duration = self.get_video_duration(input_path)
        if not duration:
            print("❌ Cannot read video duration")
            return False

        total_segments = int(duration // segment_duration) + (1 if duration % segment_duration > 0 else 0)
        print(f"📊 Video duration: {self.format_duration(int(duration))}")
        print(f"📊 Number of segments: {total_segments}")

        success_count = 0
        for i in range(total_segments):
            start_time = i * segment_duration
            output_file = os.path.join(output_folder, f"segment_{i + 1:02d}.mp4")

            print(f"⏳ Creating segment {i + 1}/{total_segments}...")

            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-ss', str(start_time),
                '-t', str(segment_duration),
                '-c', 'copy',
                output_file,
                '-y'
            ]

            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"✅ Created segment {i + 1}: {os.path.basename(output_file)}")
                success_count += 1
            except subprocess.CalledProcessError:
                print(f"❌ Failed to create segment {i + 1}")
                continue

        if success_count == total_segments:
            print(f"\n✅ Video split successfully!")
            print(f"📁 Files are in: {output_folder}")
            return True
        else:
            print(f"\n⚠️ Only {success_count}/{total_segments} segments created")
            return success_count > 0

    def download_video(self, video, output_folder):
        print("\n⏬ Downloading video...")

        try:
            import yt_dlp

            title = video['title'].replace('\u0026', '&').strip()
            title = re.sub(r'[<>:"/\\|?*]', '_', title)

            output_template = os.path.join(output_folder, f"{title}.%(ext)s")

            ydl_opts = {
                'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'ignoreerrors': True,
                'extract_flat': False,
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'cookiefile': None,
                'nocheckcertificate': True,
                'prefer_ffmpeg': True,
                'ffmpeg_location': self.ffmpeg_path,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['hls', 'dash'],
                        'player_skip': ['configs'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video['url']])

            for file in os.listdir(output_folder):
                if file.endswith(('.mp4', '.mkv', '.webm')):
                    file_path = os.path.join(output_folder, file)
                    if not file.startswith('segment_'):
                        print(f"✅ Downloaded: {file}")
                        return file_path

            return None

        except ImportError:
            print("⚠️ yt-dlp not installed. Installing...")
            self.install_yt_dlp()
            return self.download_video(video, output_folder)
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None

    def install_yt_dlp(self):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "--upgrade", "--quiet"])
            print("✅ yt-dlp installed successfully")
            return True
        except:
            print("❌ Failed to install yt-dlp")
            return False

    def get_next_session_folder(self):
        if not os.path.exists(self.main_folder):
            os.makedirs(self.main_folder)

        existing_sessions = []
        for item in os.listdir(self.main_folder):
            if item.startswith('shorts(') and item.endswith(')'):
                try:
                    num = int(item.split('(')[1].split(')')[0])
                    existing_sessions.append(num)
                except:
                    pass

        self.current_session = max(existing_sessions) + 1 if existing_sessions else 1
        session_folder = os.path.join(self.main_folder, f"shorts({self.current_session})")

        if not os.path.exists(session_folder):
            os.makedirs(session_folder)

        return session_folder

    def download_and_split_video(self, video_index, session_folder=None):
        if not (0 <= video_index < len(self.videos)):
            print("❌ Invalid video number")
            return False

        video = self.videos[video_index]
        print(f"\n🎬 Selected video: {video['title']}")

        if session_folder is None:
            session_folder = self.get_next_session_folder()

        video_path = self.download_video(video, session_folder)

        if not video_path:
            print("❌ Failed to download video")
            return False

        if self.ffmpeg_path:
            success = self.split_video(video_path, session_folder)
            if success:
                print(f"\n✅ Operation completed successfully!")
                print(f"📁 Files are in: {session_folder}")

                segments = [f for f in os.listdir(session_folder) if f.startswith('segment_')]
                if segments:
                    print(f"📊 Number of segments: {len(segments)}")
                    total_size = 0
                    for seg in sorted(segments):
                        seg_path = os.path.join(session_folder, seg)
                        size = os.path.getsize(seg_path) / (1024 * 1024)
                        total_size += size
                        print(f"   - {seg} ({size:.2f} MB)")
                    print(f"📊 Total size: {total_size:.2f} MB")
                return True
            else:
                print("⚠️ Video downloaded but splitting failed")
                return False
        else:
            print("\n⚠️ ffmpeg not available. Video downloaded without splitting.")
            print(f"📁 Video is in: {session_folder}")
            return True

    def download_multiple_videos(self, video_indices):
        session_folder = self.get_next_session_folder()
        print(f"\n📁 Session folder: {session_folder}")

        success_count = 0
        for i, idx in enumerate(video_indices, 1):
            if 0 <= idx < len(self.videos):
                print(f"\n{'=' * 60}")
                print(f"Processing video {i}/{len(video_indices)}: {self.videos[idx]['title']}")
                print(f"{'=' * 60}")

                video = self.videos[idx]
                video_folder = os.path.join(session_folder, re.sub(r'[<>:"/\\|?*]', '_', video['title'])[:50])
                if not os.path.exists(video_folder):
                    os.makedirs(video_folder)

                if self.download_and_split_video(idx, video_folder):
                    success_count += 1

        print(f"\n{'=' * 60}")
        print(f"✅ Completed: {success_count}/{len(video_indices)} videos")
        print(f"📁 Files are in: {session_folder}")
        return success_count > 0

    def show_folders(self):
        if not os.path.exists(self.main_folder):
            print("📁 No downloaded folders")
            return

        folders = [f for f in os.listdir(self.main_folder) if os.path.isdir(os.path.join(self.main_folder, f))]

        if not folders:
            print("📁 No downloaded folders")
            return

        print("\n📁 Downloaded folders:")
        print("=" * 60)
        for folder in sorted(folders):
            folder_path = os.path.join(self.main_folder, folder)
            total_size = 0
            total_videos = 0
            total_segments = 0

            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    f_path = os.path.join(root, f)
                    if os.path.isfile(f_path):
                        total_size += os.path.getsize(f_path)
                    if f.startswith('segment_'):
                        total_segments += 1
                    elif f.endswith(('.mp4', '.mkv', '.webm')):
                        total_videos += 1

            size_mb = total_size / (1024 * 1024)

            print(f"\n📂 {folder}")
            print(f"   📹 Original videos: {total_videos}")
            print(f"   ✂️ Segments: {total_segments}")
            print(f"   💾 Size: {size_mb:.2f} MB")
            print(f"   📍 Path: {folder_path}")

    def delete_session(self):
        if not os.path.exists(self.main_folder):
            print("📁 No folders to delete")
            return

        folders = [f for f in os.listdir(self.main_folder) if os.path.isdir(os.path.join(self.main_folder, f))]

        if not folders:
            print("📁 No folders to delete")
            return

        print("\n🗑️ Folders available for deletion:")
        for i, folder in enumerate(sorted(folders), 1):
            folder_path = os.path.join(self.main_folder, folder)
            files = []
            for root, dirs, filenames in os.walk(folder_path):
                files.extend(filenames)
            print(f"{i}. {folder} ({len(files)} files)")

        try:
            choice = int(input("\n🎯 Choose folder number to delete (0 to exit): "))
            if choice == 0:
                return

            if 1 <= choice <= len(folders):
                folder_to_delete = sorted(folders)[choice - 1]
                folder_path = os.path.join(self.main_folder, folder_to_delete)

                confirm = input(f"⚠️ Are you sure you want to delete {folder_to_delete}? (y/n): ")
                if confirm.lower() == 'y':
                    shutil.rmtree(folder_path)
                    print(f"✅ Deleted {folder_to_delete}")
                else:
                    print("❌ Cancelled")
            else:
                print("❌ Invalid number")
        except ValueError:
            print("❌ Please enter a valid number")

    def parse_video_selection(self, selection, max_num):
        indices = set()
        parts = re.split(r'[,\s]+', selection.strip())

        for part in parts:
            if not part:
                continue
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start = int(start)
                    end = int(end)
                    for i in range(start, end + 1):
                        if 1 <= i <= max_num:
                            indices.add(i - 1)
                except ValueError:
                    print(f"⚠️ Invalid range: {part}")
            else:
                try:
                    num = int(part)
                    if 1 <= num <= max_num:
                        indices.add(num - 1)
                    else:
                        print(f"⚠️ Number out of range: {num}")
                except ValueError:
                    print(f"⚠️ Invalid number: {part}")

        return sorted(indices)

    def show_welcome(self):
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🎬  VIDEO DOWNLOADER  &  SPLITTER  🎬                 ║
║                                                              ║
║        Download YouTube videos and split them into           ║
║        custom-length segments automatically.                 ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   ✨ Features:                                               ║
║      📺  Download from a channel or a single video           ║
║      ✂️  Split into segments of any duration                 ║
║      🎯  Select one, many, or a range of videos              ║
║      📁  Organized folder structure                          ║
║      ⚙️  Zero setup — ffmpeg handled automatically           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    def show_main_menu(self):
        print("\n╔" + "═" * 58 + "╗")
        print("║" + "  📌  WHAT DO YOU WANT TO DOWNLOAD FROM?  ".center(58) + "║")
        print("╠" + "═" * 58 + "╣")
        print("║" + "  1.  📺  A YouTube Channel (multiple videos)".ljust(58) + "║")
        print("║" + "  2.  🎬  A Specific Video".ljust(58) + "║")
        print("║" + "  3.  🚪  Exit".ljust(58) + "║")
        print("╚" + "═" * 58 + "╝")

    def show_next_menu(self):
        print("\n╔" + "═" * 58 + "╗")
        print("║" + "  🎮  WHAT WOULD YOU LIKE TO DO NEXT?  ".center(58) + "║")
        print("╠" + "═" * 58 + "╣")
        print("║" + "  1.  📁  Show downloaded folders".ljust(58) + "║")
        print("║" + "  2.  🗑️   Delete a session folder".ljust(58) + "║")
        print("║" + "  3.  🔄  Start over".ljust(58) + "║")
        print("║" + "  4.  🚪  Exit".ljust(58) + "║")
        print("╚" + "═" * 58 + "╝")

    def run(self):
        self.show_welcome()

        self.setup_ffmpeg()

        print("\n╔" + "═" * 58 + "╗")
        print("║" + "  ⏱️   SEGMENT DURATION  ".center(58) + "║")
        print("╠" + "═" * 58 + "╣")
        print("║" + "  How long should each segment be? (in seconds)".ljust(58) + "║")
        print("║" + "  Default: 120 seconds (2 minutes)".ljust(58) + "║")
        print("╚" + "═" * 58 + "╝")

        while True:
            try:
                duration_input = input("\n⏱️ Segment duration in seconds (Enter for 120): ").strip()
                if duration_input == "":
                    self.segment_duration = 120
                    break
                self.segment_duration = int(duration_input)
                if self.segment_duration <= 0:
                    print("❌ Duration must be a positive number.")
                    continue
                break
            except ValueError:
                print("❌ Please enter a valid number.")

        print(f"✅ Segment duration set to {self.segment_duration} seconds.")

        while True:
            self.show_main_menu()

            source_choice = input("\n👤 Choose option (1-3): ").strip()

            if source_choice == '1':
                channel_url = input("\n🔗 Enter the channel URL: ").strip()
                if not channel_url:
                    print("❌ URL cannot be empty")
                    continue

                try:
                    limit_input = input("📊 How many videos to fetch? (default 50): ").strip()
                    limit = int(limit_input) if limit_input else 50
                except ValueError:
                    limit = 50

                if not self.get_channel_videos(channel_url, limit=limit):
                    print("\n❌ Failed to fetch videos.")
                    continue

                print("\n╔" + "═" * 58 + "╗")
                print("║" + "  🎯  SELECT VIDEOS TO PROCESS  ".center(58) + "║")
                print("╠" + "═" * 58 + "╣")
                print("║" + "  Examples:".ljust(58) + "║")
                print("║" + "    • Single:    2".ljust(58) + "║")
                print("║" + "    • Multiple:  2,3,4".ljust(58) + "║")
                print("║" + "    • Range:     1-5".ljust(58) + "║")
                print("║" + "    • Mixed:     1,3,5-8".ljust(58) + "║")
                print("║" + "    • All:       all".ljust(58) + "║")
                print("╚" + "═" * 58 + "╝")

                selection = input("\n👤 Enter your selection: ").strip()

                if selection.lower() == 'all':
                    indices = list(range(len(self.videos)))
                else:
                    indices = self.parse_video_selection(selection, len(self.videos))

                if not indices:
                    print("❌ No valid videos selected")
                    continue

                print(f"\n✅ Selected {len(indices)} video(s):")
                for idx in indices:
                    print(f"   • {self.videos[idx]['title']}")

                confirm = input("\n⚠️ Proceed with download and split? (y/n): ")
                if confirm.lower() != 'y':
                    print("❌ Cancelled")
                    continue

                self.download_multiple_videos(indices)

            elif source_choice == '2':
                video_url = input("\n🔗 Enter the video URL: ").strip()
                if not video_url:
                    print("❌ URL cannot be empty")
                    continue

                if not self.get_video_info(video_url):
                    print("\n❌ Failed to fetch video info.")
                    continue

                confirm = input("\n⚠️ Proceed with download and split? (y/n): ")
                if confirm.lower() != 'y':
                    print("❌ Cancelled")
                    continue

                self.download_and_split_video(0)

            elif source_choice == '3':
                print("\n👋 Goodbye!")
                break

            else:
                print("❌ Invalid option")
                continue

            self.show_next_menu()

            next_choice = input("\n👤 Choose option (1-4): ").strip()

            if next_choice == '1':
                self.show_folders()
            elif next_choice == '2':
                self.delete_session()
            elif next_choice == '3':
                continue
            elif next_choice == '4':
                print("\n👋 Goodbye!")
                break


def main():
    tool = VideoDownloaderSplitter()
    tool.run()


if __name__ == "__main__":
    main()