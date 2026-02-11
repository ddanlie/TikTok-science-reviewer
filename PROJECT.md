# Science Papers Reviews TikTok blogger generator - MVP

# Description
This is an agent finding science papers, generating review for them and editing and posting a tiktok video

## Meta
- OS you are working on - Windows 10
- Project Orchestrating agent: claude code agent vscode extension
- Current project - MVP

## Tech stack
- ffmpeg (dependency) - pre-downloaded in `dependencies/` folder
- python 3 (virtual environment in `.venv/` folder is mandatory)
- runware.ai API
- tiktok API

## Tech stack meta
- Eleven Labs voice generator (`not used in code, only by human to generate .mp3 files`)

# Folder structure

## Structure Description 
This project has strict pre-defined folder structure serving 2 purposes at a time:

1. Workflows Agent Tools (WAT) structure for fully automated workflow - NOT A THING FOR THE MVP
2. Workflows Agent Tools (WAT) but the `agent/` folder is empty and the agent is claude code vscode extension itself - PRIMARPLY FOR THE MVP

Folder structure supposes the code generated will be interchangebly used as by both future `agent/` models and claude code vscode extension

## Structure explanation

`./.tmp` - all temporary files used by orchestrator to experiment, that will not be present in a final project and have to be deleted and not cause any dependency after successful project creation

`./.venv` - python 3 virtual environment folder, supposed to be created and with `python -m venv .venv/`, also the environment inside this folder must be activated before installing any python modules and packages

`./workflows` - W in WAT structure. Orchestrator uses it for creating usefull workflows to remember through context wipes. Also human-predefined workflows could be found here if some. Must be capable of being interchangebly used by orchestrator and potential autonomous agents

`./agent` - A in WAT structure. Folder for autonomous AI agents, not used in MVP project

`./tools` - T in WAT structure. Tools (.py files) agent can use when their LLM is called (you know ai agent work better than me <:). Must be capable of being interchangebly used by orchestrator and potential autonomous agents. In contrast to `./dependencies` folder - tools are using `./dependencies` folder, e.g. to call some cli utilities using some configs defined by arguments given for the tool by agent etc. 

`./dependencies` - folder for project base dependencies like cli utilities

`./readonly_sources_of_truth` - read only folder with sources of truth given by a human. you can notice the `.env` file there - it is a basic readonly file, external .evn file can be created in `project/src/` folder for orchestrator extra purposes

`./project` - all project functionality related files and folders. All predefined folders inside it are described in some workflow or project task file like this one and must be present

`./project/src` - special folder for orchestrator code. In constrast to folders and files on the same level (at `./project`) this folder is completely for the orchestrator and not participating in any human related workflows/project tasks

`./main.py` - main project starter, should be minimal, just to run the project

`./PROJECT.md` - main project task (this file)


# Full project workflow (main usecase)

The project created has to implement this main forkflow-usecase:

## Agent looks for articles with web-search
The flow is started with an agent discovering for science papers for one of the topics listed in `./locked_sources_of_truth/science_papers_topics.txt` file - topic per line format.

The criteria for the paper to be chosen by its title is
- Free access for downloading
- Current mainstream relevance (hype)
- TikTok format relevance (paper itself is not really long and overloaded)
- Paper represents an interesting story (or story that could be popularly-translated) for the tiktok audience to listen to

Main player here is an agent - since it is an MVP project claude will be asked in chat to start the web search discovery process, main.py will not be run here.

## Downloads 1 article (tool)
By selecting one paper, it has to be downloaded into `./project/resources/video_{date-now}_{uuid4}_resources/` folder

## Agent reads newly downloaded article file, finds images and creates a video script
The agnet has to read an article and make a script for the video.
Script could follow basic structure `Setup -> Conflict -> Growth -> Climax -> Resolution` or the modified one made by an agent and if he really likes it he should make a reference script structure file arbitrary for future references

### Agent creates 1st part of the script - text file (tool)
in `./project/resources/video_{date-now}_{uuid4}_resources/script.txt` agent saves his script as a pure text

Script text criteria:
- TikTok format: hook for first 2 seconds, dynamic, interesting
- Script is being created for voice generator, thats why there must not be any marks extra symbols or artifacts. Extra intonation should be added if needed and thoroughly written in order for speech generator to synthesize a clear speech.
- Script is exacly the text like it has to be said right now - no comments, no explanations around
- Script should follow some structure (reference above or any agent custom structure)

### Agent creates 2nd part of the script - text file with timestamps (tool)
Since the tiktok video will be edited using ffmpeg, time script must be created for future parsing
as `./project/resources/video_{date-now}_{uuid4}_resources/time_script.txt`.
internal format organization is on orchestractor but main criteria are:

- 1st line - duration of the video in seconds based on `./project/resources/video_{date-now}_{uuid4}_resources/script.txt` length
- 2nd and further lines - time section with an filepath of an image to be shown during that time `paper_image_{id}` from `./project/resources/video_{date-now}_{uuid4}_resources/` with one time section matching image per line

Please notice - images do not exist yet so come up with names and the flow below explains where to get them.

Time script must follow up the text script and nicely reflect the story told

### Agent arbitrary web-searches for images for the content 
Most of the content images might be generated by runware.ai api, but if agent wants to show creativity it can disciover for scenario-appropriate images itself

Criteria:
- Agent must try to find main article page to show for first seconds of the video if possible
- Image format: tiktok format 9:16, 3:4 ... 
- Image resolution >= 720:1280 (except article main page in adequate ranges)

### Agent downloads arbitrary found images (tool)

If some images were decided to be added - they are downloaded into `./project/resources/video_{date-now}_{uuid4}_resources/` folder 
and named `paper_image_{uuid4}_found` with .jpg or .png format and id strictly corresponding to the `./project/resources/video_{date-now}_{uuid4}_resources/time_script.txt`

### Agent generates prompts for the rest of the images
Rest of the images from `./project/resources/video_{date-now}_{uuid4}_resources/time_script.txt` that were not downloaded yet must be genrated with runware.ai model that's why a bunch of prompt files should be created to deal with this. 
Prompt files are put in `./project/resources/video_{date-now}_{uuid4}_resources/` too

Criteria:
- Prompt format: .txt file with name of target image. Example `paper_image_{id}_prompt.txt`
- Same style per images batch
- Script topic and time section related
- You are going to work with really weak and cheap image generator - it is sensitive for prompt and negative prompt. So carefully choose the style, scene description and actions. Don't rely on that some text should be generated - prompt for minimalistic images instead.
- Imagine you are professional promp engineer for image generators and trying to generate an enterprise level prompt for really weak generation model. You know many tricks to make it look like something meaningfull - not a bunch of unconnected halucinations

### Agent calls runware.ai API to generate images (tool)

Based on prompts created, call runware.ai API to generate images.
Starting point docs link to work with API is in `./readonly_sources_of_truth/runware_ai_api_docs_reference_startpoint`

From previous descriptions I think you have to know where to save those images - same `./project/resources/video_{date-now}_{uuid4}_resources/` folder, accordingly named file `paper_image_{uuid4}_generated` 
The id of the model you are going to work with is described in `./readonly_sources_of_truth/runware_ai_api_model_id.txt`

As was described above, its a really weak but fast and relatively beautiful generator model. Your generated prompts have to be really ready for it.

Criteria:
- Provide a one-img1-one-gen protection code to generate one and only one image per prompt. Set response wait tolerance to 30 seconds max. on any response fail: skip and generate next image


## After all teh content was generated - human plays his role. On this moment of a flow agents stops working

In order for human to continue to work in semi-automatic way several script files were prepared to fill with your code:

1. `./project/generate_video.py` - a file you have to modify to create a video. Here is how: Base of a script is still an agent tool in `./tools` but adapted for a human to just run in command line. That means other agents should be able to use it in the future but for now this adapter file exploits it. The `./project/generate_video.py` has to use `./project/resources/video_{date-now}_{uuid4}_resources/generated_voice.mp3` file. Finally the video is created with ffmpeg (important: ffmpeg - dependency used by tool (for agents) not some utility, but again - current adapter script uses that tool, so dependency->tool->adapter for human). The video has to be created based on `./project/resources/video_{date-now}_{uuid4}_resources/time_script.txt` so its combining generated and found images placing them on certain time sections and putting audio with it. ffmpeg is really helpful about this. FInal file is placed in `./project/videos/` folder. Script arguments: `uuid4` of the project folder

2. `./project/post_video.py` - simple tiktok API script to post a video. No arguments. Same structure: general agent tool created first, then this script as an adapter for a human to just run it


## This is it! Human works in the end of this MVP flow by calling tool adapter scripts, tools created will be used by other agents in the future project to fully automate the process (not now)! :)

# Notes and advices

- Even though one agent might be struggling with all the actions and tools created in one flow - multi agent potential should be set. That means interchangability again - tools created must be universal for both - current vscode extention agent and any agent created in future project modifications

- When you see that extra API variables should be created, don't ask me, just leave key variables in your .env file and tell me where it is

- Each `(tool)` marked flow point should be actually so agents created in the future use it

- For file naming matches, path findings and similar operations don't rely on yourself but create utilities in `./project/src/utils` so tools can use it

- Each video generation request is unique so i left some patterns for you to create files and folders like {uuid4} to be replaced by uuid4 string.

- A bunch of files and folders is created during this flow. Agent can miss something so rely on built-in tools and utils tests to check if all target files are created. Target files and folders list should be formalized too. On fail do not implement any difficult backup logic - just exit the program with error message describing what happened (i believe erros should be really rare at least you try to organize code like so)

- Generally, you are my partner and should not try to hide anything from me in order to "optimise" some answers or orchestration actions, we are partners building a project and help each other



