# Workflows Directory

This directory contains structured workflows for autonomous agents to follow when executing tasks in the Science Papers TikTok Blogger project.

## Purpose

Workflows provide step-by-step guidance for agents (Claude Code, future autonomous agents) to:
- Understand what tasks to perform
- Know which tools to call and when
- Validate outputs at each step
- Handle errors gracefully
- Know when to hand off to human operators

## Available Workflows

### 1. Article Discovery and Content Creation
**File**: [article_discovery_and_content_creation.yaml](article_discovery_and_content_creation.yaml)

**When to use**: User asks to discover science papers or create TikTok video content

**Trigger phrases**:
- "Find me an interesting physics paper"
- "Create a TikTok video about recent AI research"
- "Discover a trending science paper"
- "Let's make a video about [topic]"

**What it does**:
- Web search for appropriate science papers
- Downloads paper PDF
- Creates TikTok script (30-60 seconds)
- Creates timeline (time_script.txt)
- Finds/downloads relevant images
- Generates missing images using AI
- Validates all resources
- Hands off to human for voice generation

**Outputs**:
- `paper.pdf` - Downloaded science paper
- `script.txt` - Voice script for TikTok video
- `time_script.txt` - Timeline mapping images to timestamps
- Multiple image files (found or AI-generated)

**Next phase**: Human uses Eleven Labs to generate voice, then runs video generation script

## How Agents Should Use Workflows

### 1. Workflow Selection
When user makes a request:
1. Identify user intent (discovery, video creation, etc.)
2. Match intent to appropriate workflow file
3. Load and parse the workflow YAML

### 2. Workflow Execution
Follow the workflow structure:

```
prerequisites → check environment, API keys, dependencies
↓
inputs → understand user request
↓
steps (1-N) → execute in sequence
↓
validation → verify success criteria
↓
handoff → inform user of completion
```

### 3. Step Execution Pattern
For each step in workflow:

```python
# 1. Read step metadata
step_name = step['name']
step_description = step['description']

# 2. Execute actions
for action in step['actions']:
    if action has 'tool_call':
        result = call_tool(action['tool_call'])
        validate(result)

# 3. Check success criteria
if not success_criteria_met:
    follow error_handling

# 4. Store outputs for next step
outputs[step] = result
```

### 4. Error Handling
Refer to workflow's `error_handling` section:
- **Critical errors**: Stop workflow, inform user
- **Non-critical errors**: Log, continue, inform at end

### 5. Validation
Before proceeding to next phase:
- Check all required outputs exist
- Validate file formats and content
- Report any issues to user

## Workflow File Format

Workflows use YAML format with this structure:

```yaml
workflow:
  name: "Workflow Name"
  version: "1.0.0"
  description: "What this workflow does"

prerequisites:
  - environment: "..."
  - dependencies: "..."

inputs:
  - name: "..."
    description: "..."

steps:
  - step: 1
    name: "step_name"
    description: "What this step does"
    actions: [...]
    validation: [...]
    output: [...]

error_handling:
  - error: "..."
    resolution: "..."

success_metrics:
  - "Metric 1"
  - "Metric 2"
```

## Creating New Workflows

When creating new workflows:

1. **Use existing workflows as templates**
2. **Be specific about tool calls**:
   ```yaml
   tool_call:
     function: "function_name"
     module: "tools.module_name"
     params:
       param1: "<value>"
   ```

3. **Include validation at every step**
4. **Specify error handling**
5. **Document expected outputs**
6. **Add agent notes for clarity**

## Integration with Tools

All workflows use tools from the `tools/` directory:

| Tool | Module | Purpose |
|------|--------|---------|
| download_paper | tools.download_paper | Download PDF from URL |
| save_script | tools.save_script | Save voice script |
| save_time_script | tools.save_time_script | Save timeline |
| save_image_prompt | tools.save_image_prompt | Save AI image prompt |
| download_image | tools.download_image | Download image from web |
| generate_images_runware | tools.generate_images_runware | Generate images with AI |
| generate_video_ffmpeg | tools.generate_video_ffmpeg | Create video with FFmpeg |
| post_video_tiktok | tools.post_video_tiktok | Post to TikTok |

## Workflow Execution Example

### User Request
"Find me an interesting quantum physics paper and create a TikTok video"

### Agent Process
1. **Identify workflow**: Article Discovery and Content Creation
2. **Check prerequisites**: ✅ Env activated, ✅ API key present
3. **Execute steps 1-9**: Search → Download → Script → Images
4. **Validate**: ✅ All resources present
5. **Handoff**: "Content ready! Please generate voice with Eleven Labs..."

### Result
```
project/resources/video_20260210_abc123_resources/
├── paper.pdf
├── script.txt
├── time_script.txt
├── paper_image_001_found.jpg
├── paper_image_002_generated.png
├── paper_image_003_generated.png
└── [User adds] generated_voice.mp3
```

## Future Workflows

Additional workflows to be created:

- **Script Revision Workflow**: Modify existing scripts based on user feedback
- **Image Regeneration Workflow**: Regenerate specific images with new prompts
- **Batch Processing Workflow**: Create multiple videos from a list of papers
- **Quality Review Workflow**: Analyze and improve existing video content
- **Analytics Workflow**: Track video performance and suggest improvements

## Questions?

For workflow-related questions:
1. Check this README
2. Review [article_discovery_and_content_creation.yaml](article_discovery_and_content_creation.yaml)
3. See main project workflow: `python main.py --workflow`
4. Check tools documentation in `tools/` directory

## Version

Workflows Directory v1.0.0 - Created 2026-02-10
