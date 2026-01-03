#!/usr/bin/env python3
"""
Repo Explainer Video Generator
Generates 30-second explainer videos from git repositories using Gemini VEO 3.1
"""

import os
import sys
import json
import asyncio
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Check and auto-install dependencies
def check_and_install_dependencies():
    """Check for required packages and install if missing."""
    required_packages = {
        'google.genai': 'google-genai',
        'elevenlabs': 'elevenlabs',
        'git': 'gitpython',
        'moviepy': 'moviepy',
        'dotenv': 'python-dotenv',
        'requests': 'requests',
        'aiohttp': 'aiohttp',
        'PIL': 'Pillow'
    }

    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"📦 Installing missing dependencies: {', '.join(missing)}")
        import subprocess
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--user', *missing
            ])
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError:
            try:
                # Fallback for externally managed environments
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', '--break-system-packages', *missing
                ])
                print("✅ Dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install dependencies. Please run: pip install {' '.join(missing)}")
                sys.exit(1)

check_and_install_dependencies()

# Now import the packages
import git
import requests
import aiohttp
from google import genai
from google.genai import types
from elevenlabs import ElevenLabs, Voice
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RepoExplainerGenerator:
    """Main class for generating explainer videos from repositories."""

    def __init__(self, repo_path: str, output_path: Optional[str] = None):
        self.repo_path = repo_path
        self.output_path = output_path or f"explainer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        self.cache_dir = Path(".repo-explainer-cache")
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize API clients
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        if not self.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable not set")

        self.gemini_client = genai.Client(api_key=self.gemini_api_key)
        self.elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_api_key)

        # Configuration
        self.video_quality = os.getenv("VIDEO_QUALITY", "1080p")
        self.veo_model = "veo-3.1-fast-generate-preview" if os.getenv("VEO_MODEL", "fast") == "fast" else "veo-3.1-generate-preview"

        print(f"🎬 Repo Explainer Video Generator")
        print(f"📁 Repository: {repo_path}")
        print(f"💾 Output: {self.output_path}")
        print(f"🎥 Quality: {self.video_quality} | Model: {self.veo_model}")
        print()

    def prepare_repository(self) -> Path:
        """Clone repository if URL, or use local path."""
        print("📂 Preparing repository...")

        # Check if it's a URL
        if self.repo_path.startswith(('http://', 'https://', 'git@')):
            print(f"🌐 Cloning remote repository: {self.repo_path}")
            temp_dir = self.cache_dir / "repo_clone"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            git.Repo.clone_from(self.repo_path, temp_dir)
            print(f"✅ Repository cloned to {temp_dir}")
            return temp_dir
        else:
            # Local path
            repo_path = Path(self.repo_path).resolve()
            if not repo_path.exists():
                raise ValueError(f"Repository path does not exist: {repo_path}")
            print(f"✅ Using local repository: {repo_path}")
            return repo_path

    def analyze_repository(self, repo_path: Path) -> Dict[str, any]:
        """
        Analyze repository using Gemini to understand its purpose, architecture, and features.
        In a real implementation, this would use Claude Code's Task tool to spawn parallel agents.
        For now, we'll use Gemini directly to analyze the repo.
        """
        print("🔍 Analyzing repository structure and purpose...")

        # Read key files
        analysis_data = {
            'readme': '',
            'code_files': [],
            'docs': [],
            'package_info': {}
        }

        # Read README
        for readme_name in ['README.md', 'README.rst', 'README.txt', 'README']:
            readme_path = repo_path / readme_name
            if readme_path.exists():
                with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                    analysis_data['readme'] = f.read()
                    print(f"  ✓ Found {readme_name}")
                break

        # Find package/project files
        package_files = {
            'package.json': 'npm',
            'pyproject.toml': 'python',
            'setup.py': 'python',
            'Cargo.toml': 'rust',
            'go.mod': 'go',
            'composer.json': 'php',
            'pom.xml': 'java'
        }

        for filename, lang in package_files.items():
            file_path = repo_path / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    analysis_data['package_info'][lang] = f.read()
                    print(f"  ✓ Found {filename} ({lang})")

        # Read docs directory
        docs_dir = repo_path / 'docs'
        if docs_dir.exists():
            for doc_file in docs_dir.glob('**/*.md'):
                with open(doc_file, 'r', encoding='utf-8', errors='ignore') as f:
                    analysis_data['docs'].append({
                        'name': doc_file.name,
                        'content': f.read()[:5000]  # Limit size
                    })
            print(f"  ✓ Found {len(analysis_data['docs'])} documentation files")

        # Sample some code files
        code_extensions = ['.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.c']
        code_files = []
        for ext in code_extensions:
            code_files.extend(list(repo_path.glob(f'**/*{ext}'))[:3])  # Max 3 per type

        for code_file in code_files[:10]:  # Max 10 total
            try:
                with open(code_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()[:2000]  # First 2000 chars
                    analysis_data['code_files'].append({
                        'name': code_file.name,
                        'path': str(code_file.relative_to(repo_path)),
                        'content': content
                    })
            except Exception as e:
                continue

        print(f"  ✓ Sampled {len(analysis_data['code_files'])} code files")

        # Use Gemini to analyze the repository
        print("\n🤖 Using Gemini to analyze repository content...")

        analysis_prompt = f"""Analyze this software repository and provide a comprehensive understanding:

README:
{analysis_data['readme'][:10000]}

Package/Config Files:
{json.dumps(analysis_data['package_info'], indent=2)[:5000]}

Code Samples:
{json.dumps([{'name': f['name'], 'preview': f['content'][:500]} for f in analysis_data['code_files']], indent=2)}

Provide a structured analysis in JSON format:
{{
    "name": "Project name",
    "tagline": "One-sentence description",
    "problem": "What problem does it solve?",
    "solution": "How does it solve it?",
    "architecture": "High-level architecture/approach",
    "key_features": ["feature1", "feature2", "feature3"],
    "tech_stack": ["tech1", "tech2"],
    "getting_started": "Quick start steps",
    "target_audience": "Who is this for?"
}}

Be concise and focus on what would make a compelling 30-second explainer video."""

        response = self.gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=analysis_prompt
        )

        # Parse JSON response
        analysis_text = response.text.strip()
        # Extract JSON from markdown code blocks if present
        if '```json' in analysis_text:
            analysis_text = analysis_text.split('```json')[1].split('```')[0].strip()
        elif '```' in analysis_text:
            analysis_text = analysis_text.split('```')[1].split('```')[0].strip()

        try:
            analysis_result = json.loads(analysis_text)
            print("✅ Repository analysis complete")
            return analysis_result
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON, using fallback analysis")
            # Fallback: create a basic analysis
            return {
                "name": repo_path.name,
                "tagline": "An open source project",
                "problem": "Solving software challenges",
                "solution": "Providing tools and libraries",
                "architecture": "Modern software architecture",
                "key_features": ["Open source", "Well documented", "Active development"],
                "tech_stack": ["Various technologies"],
                "getting_started": "See README for installation",
                "target_audience": "Developers"
            }

    def generate_video_script(self, analysis: Dict) -> Dict[str, any]:
        """Generate a 5-scene video script using Gemini."""
        print("\n📝 Generating video script...")

        script_prompt = f"""Create a compelling 40-second explainer video script for this software project.

Project Analysis:
{json.dumps(analysis, indent=2)}

Create a 5-scene script (8 seconds each) with cinematic visual descriptions:

Scene 1 (HOOK - 8 seconds):
- Visually striking intro
- Show the project name and tagline
- Modern tech aesthetic with gradients and animations

Scene 2 (PROBLEM - 8 seconds):
- Visualize the problem this solves
- Use metaphors and relatable scenarios
- Dynamic infographic style

Scene 3 (SOLUTION - 8 seconds):
- Show how it works (architecture visualization)
- Animated diagrams showing data flow
- Clean, technical but accessible

Scene 4 (KEY FEATURES - 8 seconds):
- Highlight 2-3 standout features
- Each feature gets a visual moment
- Smooth transitions between features

Scene 5 (GET STARTED - 8 seconds):
- Quick installation/getting started visual
- Call to action
- Project logo/name with link/GitHub stars

For each scene provide:
1. Visual description (detailed for VEO prompting - include camera movements, lighting, colors, objects)
2. Voiceover narration text (natural, conversational, ~20-25 words for 8-second scenes)
3. Audio cues (ambient sounds, effects that VEO should generate)

Return as JSON:
{{
    "scenes": [
        {{
            "number": 1,
            "title": "Scene title",
            "duration": 8,
            "visual_prompt": "Extremely detailed VEO prompt with cinematic details...",
            "voiceover_text": "What the narrator says...",
            "audio_cues": "background sounds, effects..."
        }},
        ...
    ],
    "video_title": "Project Name: Tagline",
    "overall_style": "modern tech + dynamic infographics"
}}

Make the visual prompts EXTREMELY detailed for best VEO results - include specific camera movements (dolly, pan, zoom), lighting (soft, dramatic, neon), colors (hex codes), composition, and transitions."""

        response = self.gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=script_prompt
        )

        script_text = response.text.strip()
        if '```json' in script_text:
            script_text = script_text.split('```json')[1].split('```')[0].strip()
        elif '```' in script_text:
            script_text = script_text.split('```')[1].split('```')[0].strip()

        script = json.loads(script_text)

        print(f"✅ Generated {len(script['scenes'])}-scene script")
        for i, scene in enumerate(script['scenes'], 1):
            print(f"   Scene {i}: {scene['title']}")

        return script

    async def generate_video_clip(
        self,
        scene: Dict,
        scene_number: int,
        previous_video_path: Optional[str] = None
    ) -> str:
        """Generate a single video clip using VEO 3.1."""
        print(f"\n🎥 Generating Scene {scene_number}: {scene['title']}...")

        # Prepare VEO prompt (already detailed from script generation)
        veo_prompt = scene['visual_prompt']

        # Add audio cues to prompt
        if scene.get('audio_cues'):
            veo_prompt += f"\n\nAudio: {scene['audio_cues']}"

        print(f"   Prompt: {veo_prompt[:100]}...")

        try:
            # Generate video with VEO
            config = types.GenerateVideosConfig(
                aspect_ratio="16:9",
                resolution=self.video_quality,
                duration_seconds=8,
            )

            # Use scene extension if we have a previous video
            if previous_video_path and os.path.exists(previous_video_path):
                print(f"   Using scene extension from previous clip...")
                with open(previous_video_path, 'rb') as f:
                    previous_video = f.read()

                operation = self.gemini_client.models.generate_videos(
                    model=self.veo_model,
                    prompt=veo_prompt,
                    video=previous_video,
                    config=config
                )
            else:
                operation = self.gemini_client.models.generate_videos(
                    model=self.veo_model,
                    prompt=veo_prompt,
                    config=config
                )

            print(f"   ⏳ Waiting for VEO to generate clip (this may take 1-3 minutes)...")

            # Poll for completion
            op_name = operation.name if hasattr(operation, 'name') else operation
            while not operation.done:
                await asyncio.sleep(5)
                operation = self.gemini_client.operations.get(op_name)
                if hasattr(operation, 'metadata') and hasattr(operation.metadata, 'progress_percentage'):
                    progress = operation.metadata.progress_percentage
                    print(f"   Progress: {progress}%", end='\r')

            # Get the generated video
            result = operation.result()

            # Save video clip
            clip_path = self.cache_dir / f"scene_{scene_number}.mp4"

            if hasattr(result, 'video') and result.video:
                with open(clip_path, 'wb') as f:
                    f.write(result.video.video_data)
                print(f"   ✅ Scene {scene_number} generated: {clip_path}")
                return str(clip_path)
            else:
                print(f"   ❌ Failed to generate scene {scene_number}")
                return None

        except Exception as e:
            print(f"   ❌ Error generating scene {scene_number}: {str(e)}")
            return None

    async def generate_all_video_clips(self, script: Dict) -> List[str]:
        """Generate all video clips with scene extension (sequential for proper chaining)."""
        print("\n🎬 Generating all video clips with scene extension...")

        clip_paths = []
        previous_clip = None

        for i, scene in enumerate(script['scenes'], 1):
            clip_path = await self.generate_video_clip(scene, i, previous_clip)
            if clip_path:
                clip_paths.append(clip_path)
                previous_clip = clip_path
            else:
                print(f"⚠️  Scene {i} failed, continuing with remaining scenes...")

        print(f"\n✅ Generated {len(clip_paths)}/{len(script['scenes'])} video clips")
        return clip_paths

    def generate_voiceover(self, script: Dict) -> str:
        """Generate voiceover narration using ElevenLabs."""
        print("\n🎙️  Generating AI voiceover...")

        # Combine all voiceover texts
        full_script = " ".join([scene['voiceover_text'] for scene in script['scenes']])

        print(f"   Script: \"{full_script[:100]}...\"")

        try:
            # Generate speech using ElevenLabs
            audio = self.elevenlabs_client.generate(
                text=full_script,
                voice="Adam",  # Professional male voice, can be customized
                model="eleven_multilingual_v2"
            )

            # Save audio
            voiceover_path = self.cache_dir / "voiceover.mp3"
            with open(voiceover_path, 'wb') as f:
                for chunk in audio:
                    f.write(chunk)

            print(f"✅ Voiceover generated: {voiceover_path}")
            return str(voiceover_path)

        except Exception as e:
            print(f"❌ Error generating voiceover: {str(e)}")
            return None

    def get_background_music(self) -> str:
        """
        Get lo-fi/trip hop background music.
        For now, uses a placeholder. In production, could:
        1. Generate music using a music generation API
        2. Select from a library of royalty-free tracks
        3. Use AI music generation (e.g., Suno, MusicGen)
        """
        print("\n🎵 Adding background music...")

        # For this demo, we'll create a silent placeholder
        # In production, you'd want to either:
        # 1. Include a royalty-free music library
        # 2. Use a music generation API like Suno or MusicGen
        # 3. Allow users to provide their own music file

        music_path = self.cache_dir / "background_music.mp3"

        # Create a silent audio file as placeholder
        # In production, replace this with actual music
        from moviepy import AudioClip
        import numpy as np

        def make_frame(t):
            return np.array([0, 0])  # Stereo silence

        duration = 40  # 40 seconds (5 scenes × 8 seconds)
        audio_clip = AudioClip(make_frame, duration=duration, fps=44100)
        audio_clip.write_audiofile(str(music_path), fps=44100, verbose=False, logger=None)

        print("⚠️  Using silent placeholder - add your own lo-fi music at:", music_path)
        print("   Tip: Replace this file with a 40-second lo-fi/trip hop track")

        return str(music_path)

    def compose_final_video(
        self,
        clip_paths: List[str],
        voiceover_path: Optional[str],
        music_path: Optional[str]
    ) -> str:
        """Compose final video with all clips, voiceover, and music."""
        print("\n🎬 Composing final video...")

        # Load all video clips
        clips = []
        for i, clip_path in enumerate(clip_paths, 1):
            try:
                clip = VideoFileClip(clip_path)
                clips.append(clip)
                print(f"   ✓ Loaded clip {i}/{len(clip_paths)}")
            except Exception as e:
                print(f"   ⚠️  Failed to load clip {i}: {str(e)}")

        if not clips:
            raise ValueError("No video clips could be loaded")

        # Concatenate video clips
        print("   Stitching clips together...")
        final_video = concatenate_videoclips(clips, method="compose")

        # Prepare audio tracks
        audio_tracks = []

        # Add voiceover
        if voiceover_path and os.path.exists(voiceover_path):
            try:
                voiceover = AudioFileClip(voiceover_path)
                audio_tracks.append(voiceover)
                print("   ✓ Added voiceover")
            except Exception as e:
                print(f"   ⚠️  Failed to load voiceover: {str(e)}")

        # Add background music
        if music_path and os.path.exists(music_path):
            try:
                music = AudioFileClip(music_path)
                # Reduce music volume to 30% so voiceover is clear
                music = music.volumex(0.3)
                audio_tracks.append(music)
                print("   ✓ Added background music (30% volume)")
            except Exception as e:
                print(f"   ⚠️  Failed to load music: {str(e)}")

        # Composite audio
        if audio_tracks:
            final_audio = CompositeAudioClip(audio_tracks)
            final_video = final_video.set_audio(final_audio)
            print("   ✓ Audio tracks mixed")

        # Write final video
        print(f"\n💾 Rendering final video to {self.output_path}...")
        final_video.write_videofile(
            self.output_path,
            codec='libx264',
            audio_codec='aac',
            fps=24,
            preset='medium',
            verbose=False,
            logger=None
        )

        # Cleanup
        for clip in clips:
            clip.close()
        if audio_tracks:
            final_audio.close()
        final_video.close()

        print(f"\n✅ Video generation complete!")
        print(f"📹 Output: {self.output_path}")

        # Show file size
        file_size = os.path.getsize(self.output_path) / (1024 * 1024)  # MB
        print(f"📊 File size: {file_size:.2f} MB")

        return self.output_path

    async def generate(self) -> str:
        """Main generation pipeline."""
        try:
            # Step 1: Prepare repository
            repo_path = self.prepare_repository()

            # Step 2: Analyze repository
            analysis = self.analyze_repository(repo_path)

            # Step 3: Generate script
            script = self.generate_video_script(analysis)

            # Step 4: Generate video clips (sequential for scene extension)
            clip_paths = await self.generate_all_video_clips(script)

            if not clip_paths:
                raise ValueError("Failed to generate any video clips")

            # Step 5: Generate voiceover (can run in parallel with step 4 in production)
            voiceover_path = self.generate_voiceover(script)

            # Step 6: Get background music
            music_path = self.get_background_music()

            # Step 7: Compose final video
            output_path = self.compose_final_video(clip_paths, voiceover_path, music_path)

            return output_path

        except Exception as e:
            print(f"\n❌ Error during generation: {str(e)}")
            raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate 30-second explainer videos from git repositories"
    )
    parser.add_argument(
        'repo',
        help='Repository path (local) or URL (remote)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output video path (default: explainer_TIMESTAMP.mp4)'
    )
    parser.add_argument(
        '--preview', '-p',
        action='store_true',
        help='Preview mode: generate and display script without creating video (free)'
    )

    args = parser.parse_args()

    # Create generator
    generator = RepoExplainerGenerator(args.repo, args.output)

    if args.preview:
        # Preview mode - just show the script
        print("\n🎭 PREVIEW MODE - Script generation only (no video)\n")
        repo_path = generator.prepare_repository()
        analysis = generator.analyze_repository(repo_path)
        script = generator.generate_video_script(analysis)

        print("\n" + "="*80)
        print("📋 GENERATED SCRIPT PREVIEW")
        print("="*80)
        print(f"\n🎬 Video Title: {script['video_title']}")
        print(f"🎨 Style: {script['overall_style']}\n")

        for scene in script['scenes']:
            print(f"\n{'─'*80}")
            print(f"Scene {scene['number']}: {scene['title']} ({scene['duration']}s)")
            print(f"{'─'*80}")
            print(f"\n🎥 Visual Prompt:")
            print(f"   {scene['visual_prompt']}\n")
            print(f"🎙️  Voiceover:")
            print(f"   \"{scene['voiceover_text']}\"\n")
            print(f"🔊 Audio Cues:")
            print(f"   {scene.get('audio_cues', 'None')}")

        print(f"\n{'='*80}")
        print("\n✅ Preview complete! To generate the actual video, run without --preview flag")
        print(f"💰 Estimated cost: ~$6.00-6.05 (VEO: $6.00, Gemini: $0.05, ElevenLabs: free tier)")
        return

    # Full generation mode
    output_path = asyncio.run(generator.generate())

    print(f"\n🎉 Success! Your explainer video is ready:")
    print(f"   {output_path}")
    print(f"\n💡 Tip: Edit {generator.cache_dir}/background_music.mp3 with your own lo-fi track!")


if __name__ == '__main__':
    main()
