<p align="center">
  <img src="banner.png" alt="Repo Explainer" width="600">
</p>

# Repo Explainer

Automatically generate 30-second explainer videos from any git repository using AI.

This tool analyzes your codebase, writes a script, generates cinematic video clips with Gemini VEO 3.1, adds AI voiceover, and produces a polished HD video ready to share.

## Quick Install

```bash
curl -sL https://raw.githubusercontent.com/johnpsasser/repo-explainer/main/install.sh | bash
```

Then set up your API keys:

1. Get a [Gemini API key](https://aistudio.google.com/apikey) (paid, ~$5/video)
2. Get an [ElevenLabs API key](https://elevenlabs.io) (free tier available)
3. Add to your shell config:
   ```bash
   export GEMINI_API_KEY="your-gemini-key"
   export ELEVENLABS_API_KEY="your-elevenlabs-key"
   ```
4. Install ffmpeg: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Linux)
5. Restart Claude Code

## Usage

Generate a video from any repository:

```bash
/repo-explainer https://github.com/username/repo
```

Or use a local path:

```bash
/repo-explainer ~/dev/my-project
```

Preview the script without generating video (free):

```bash
/repo-explainer https://github.com/username/repo --preview
```

Specify output location:

```bash
/repo-explainer https://github.com/username/repo --output ~/Videos/demo.mp4
```

## What It Does

The tool follows a five-step process:

1. **Analyzes the repository** by reading the README, documentation, package files, and sampling code
2. **Generates a script** with five 6-second scenes covering introduction, problem, solution, features, and getting started
3. **Creates video clips** using Gemini VEO 3.1, applying scene extension for smooth transitions
4. **Generates voiceover** narration using ElevenLabs
5. **Composes the final video** by stitching clips, layering audio, and adding background music

The result is a 30-second, 1080p MP4 file.

## Cost

Per video using VEO Fast (recommended):
- VEO 3.1 Fast: $4.50 (30 seconds at $0.15/sec)
- Gemini 2.0 Flash: ~$0.05 (analysis and script)
- ElevenLabs: $0 (free tier covers most use)

**Total: About $5 per video**

Preview mode is free. It generates the full script so you can review before paying for video generation.

## How the Videos Look

The generated videos combine modern tech aesthetics with dynamic infographics. Each scene includes:

- Detailed visual descriptions for VEO (camera movements, lighting, composition)
- Natural voiceover narration explaining the project
- Ambient audio and sound effects
- Smooth transitions between scenes

The five-scene structure:
1. Hook (0-6s): Eye-catching intro with project name
2. Problem (6-12s): What problem does it solve?
3. Solution (12-18s): How it works, architecture
4. Features (18-24s): Key capabilities
5. Get Started (24-30s): Quick start and call to action

## Background Music

The tool creates a silent placeholder at `.repo-explainer-cache/background_music.mp3`. Replace this with your own 30-second track.

Free music sources:
- [YouTube Audio Library](https://studio.youtube.com/channel/UC/music)
- [Incompetech](https://incompetech.com/) (free with attribution)
- [Chosic](https://www.chosic.com/free-music/lofi/)

## Configuration

Optional environment variables:

```bash
VIDEO_QUALITY=1080p    # or 720p
VEO_MODEL=fast         # or standard (slower, $12/video)
OUTPUT_DIR=./videos
```

## Manual Installation

If you prefer not to run the install script:

1. Create the skill directory:
   ```bash
   mkdir -p ~/.claude/skills/repo-explainer
   ```

2. Download the files:
   ```bash
   cd ~/.claude/skills/repo-explainer
   curl -sL https://raw.githubusercontent.com/johnpsasser/repo-explainer/main/SKILL.md -o SKILL.md
   curl -sL https://raw.githubusercontent.com/johnpsasser/repo-explainer/main/generate.py -o generate.py
   curl -sL https://raw.githubusercontent.com/johnpsasser/repo-explainer/main/requirements.txt -o requirements.txt
   chmod +x generate.py
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   brew install ffmpeg  # or apt install ffmpeg
   ```

4. Set your API keys and restart Claude Code

## Customization

**Change the voiceover voice**: Edit `generate.py` around line 548. Replace `voice="Adam"` with another ElevenLabs voice like Rachel, Bella, Antoni, or Thomas.

**Adjust video quality**: Set `VIDEO_QUALITY=720p` in your environment for faster generation at lower resolution.

**Use higher quality VEO**: Set `VEO_MODEL=standard` for better results. This costs $0.40/sec instead of $0.15/sec ($12 vs $5 per video).

## Troubleshooting

**"GEMINI_API_KEY not set"**

Make sure the key is exported in your shell. Check with `echo $GEMINI_API_KEY`. Add it to `.zshrc` or `.bashrc` and restart your terminal.

**"Module not found" errors**

Install dependencies manually: `pip install -r requirements.txt`

If you have multiple Python versions, make sure you're using Python 3.9+.

**"ffmpeg not found"**

Install ffmpeg using your package manager: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Linux).

**Generation is slow**

This is normal. VEO takes 1-3 minutes per 6-second clip, so total generation time is 5-15 minutes for a complete video.

**No sound in video**

Make sure you have voiceover generated. Check the console output for ElevenLabs errors. Free tier has monthly limits.

## Best Practices

**Pick good repositories**: Projects with clear README files, distinct features, and well-documented architecture produce the best videos. Very old or poorly documented repos may generate generic content.

**Use preview mode first**: Test the script generation before spending money on video. Preview mode is free and shows you exactly what the video will say.

**Start with small repos**: Simpler projects are easier to explain in 30 seconds. Complex enterprise codebases may not fit well in this format.

**Add custom music**: The default background track is silent. Adding lo-fi or trip hop music makes the video much more engaging.

## How It Works Internally

**Repository analysis**: The tool reads README.md, package files (package.json, pyproject.toml, etc.), documentation in `/docs`, and samples up to 10 code files. It sends this to Gemini 2.0 Flash for analysis.

**Script generation**: Gemini creates a structured JSON script with five scenes. Each scene includes a detailed visual prompt (camera movements, lighting, colors), voiceover text, and audio cues.

**Video generation**: The tool calls VEO 3.1 sequentially for each scene, using scene extension so each clip continues from the last frame of the previous clip. This creates smooth transitions.

**Audio composition**: ElevenLabs generates the voiceover. MoviePy mixes it with background music (voiceover at 100%, music at 30%) and combines with the video.

**Output**: The final video is rendered with ffmpeg (H.264 video, AAC audio, 24fps) and saved as an MP4.

## Examples

Generate for a popular framework:
```bash
/repo-explainer https://github.com/vercel/next.js
```

Local project with custom output:
```bash
/repo-explainer ~/projects/my-app --output ~/Desktop/demo.mp4
```

Preview a repo before generating:
```bash
/repo-explainer https://github.com/django/django --preview
```

## Links

- [Gemini VEO 3.1 Documentation](https://ai.google.dev/gemini-api/docs/video)
- [ElevenLabs API Docs](https://elevenlabs.io/docs)
- [VEO Prompting Guide](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1)

## License

MIT
