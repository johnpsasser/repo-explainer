# Repo Explainer Video Generator

**Generate stunning 30-second explainer videos from any git repository using Gemini VEO 3.1**

## Overview

This skill analyzes a git repository (local or remote) and automatically creates a professional 30-second explainer video featuring:

- Clean, modern graphics with dynamic infographics
- AI-generated voiceover narration
- Lo-fi/trip hop background music
- Smooth scene transitions
- 1080p HD output

## How It Works

1. **Repository Analysis**: Uses parallel AI agents to comprehensively analyze README, documentation, and code structure
2. **Script Generation**: Creates a 5-scene narrative script (6 seconds per scene)
3. **Visual Generation**: Generates 5 video clips in parallel using Gemini VEO 3.1 Fast with scene extension
4. **Voiceover**: Creates natural AI narration using ElevenLabs
5. **Composition**: Combines video, voiceover, and music using ffmpeg

## Usage

```bash
/repo-explainer <path-or-url>
```

### Examples

```bash
# Local repository
/repo-explainer /Users/you/projects/my-app

# Remote GitHub repository
/repo-explainer https://github.com/username/repo

# With custom output path
/repo-explainer https://github.com/vercel/next.js --output ./nextjs-explainer.mp4
```

## Requirements

### Environment Variables

Required API keys (set in your `.env` or environment):

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Optional
OUTPUT_DIR=./videos  # Default: current directory
VIDEO_QUALITY=1080p  # Options: 720p, 1080p (default)
VEO_MODEL=fast       # Options: fast (default), standard
```

### System Dependencies

- Python 3.9+
- ffmpeg (for video composition)

### Python Dependencies

See `requirements.txt`:
- google-genai
- elevenlabs
- gitpython
- moviepy
- asyncio

## Output

Creates an MP4 file with:
- Resolution: 1080p (default) or 720p
- Duration: ~30 seconds
- Audio: Voiceover + background music
- Format: H.264 video, AAC audio

## Scene Structure

The generated video follows this 5-scene structure (6 seconds each):

1. **Hook** (0-6s): Eye-catching intro with the tool's name and tagline
2. **Problem** (6-12s): What problem does this tool solve?
3. **Solution** (12-18s): How does it work? Architecture overview
4. **Key Features** (18-24s): Highlight 2-3 standout features
5. **Get Started** (24-30s): Quick start guide and call-to-action

## Architecture

- **Ultra-parallel processing**: Repository analysis, video generation, and voiceover creation all run in parallel
- **Scene extension**: VEO clips seamlessly connect using the final frame of the previous clip
- **Cost-optimized**: Uses VEO 3.1 Fast ($0.15/sec = ~$4.50 per video) for fast, affordable generation
- **Quality-first**: ElevenLabs voiceover for natural, engaging narration

## Prompting Strategy

The skill uses Gemini 2.5 Flash to enrich prompts with:
- Cinematic camera movements
- Specific visual styles (modern tech + infographic aesthetics)
- Detailed scene descriptions
- Synchronized audio cues

## Cost Estimate

Per 30-second video:
- VEO 3.1 Fast: 30 seconds @ $0.15/sec = $4.50
- Gemini 2.5 Flash analysis: ~$0.05
- ElevenLabs voiceover: ~$0.01 (with free tier)
- **Total: ~$4.50-5.00 per video**

## Notes

- First run may take 3-5 minutes as clips are generated
- Supports both public and private repositories (if you have access)
- Automatically clones remote repos to temp directory
- Generates intermediate files in `.repo-explainer-cache/` (can be deleted after)

## Credits

Built with:
- [Gemini VEO 3.1](https://ai.google.dev/gemini-api/docs/video) - Video generation
- [ElevenLabs](https://elevenlabs.io) - AI voiceover
- [Claude Code](https://claude.com/claude-code) - Skill framework
