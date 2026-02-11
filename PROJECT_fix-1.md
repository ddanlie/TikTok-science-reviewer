# PROJECT FIXES, FEATURES


# Existing stage fix: Agent creates 1st part of the script - text file (tool)
Notice, that voice generator speed is in `./readonly_sources_of_truth/voice_generator_speech_speed.txt`. with formatting \<term\>:\<value\> per line.

Plan video duration and calculate how many words you should generate for the script. 

# Existing stage fix: Agent calls runware.ai API to generate images (tool)

Prompt tamplate: `[Abstract 5 words], [photography style], [camera model/lens], [angle], [image structure], [lighting description]`
Prompt example: "Cat eating from bird bowl, dog drinking from butterfly bowl, cinematic photograph, Sony A7R IV 50mm, eye-level, cozy kitchen composition with pets in foreground, warm sunlight streaming through window"
Note: first 5 words define the most of the image, choose wisely
Note: do not bias and do not limit your creativity by the example. Image could be anything - abstract figure, a nice photo or anything else inbetween 

# Tool modified: `generate_images_runware.py` 
Changed `runware_ai_api_model_id.txt` file format and refactored tool `generate_images_runware.py` tool for it - check

# Tool created: `calculate_script_word_amount.py`
Modify the tool for ` Agent creates 1st part of the script` stage demands 

# `article_discovery_and_content_creation.yaml` modification
Enhance the file with the stage fixes and tools created