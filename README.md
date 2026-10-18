# 📌 PinForge
 
**A free Pinterest marketing assistant for digital product sellers, powered by an open-weight model that runs on your own computer.**
 
Pinterest wants fresh pins all the time, and every pin needs its own title, description and keywords. PinPilot does that writing for you. You type in your product details, and it gives you ready-to-use content and a weekly posting plan. It uses **Gemma 3** through **Ollama**, so there is no usage limit and no cost per pin.
 
Built for the Hacktoberfest Open-Source AI Challenge, Week 2: Side Hustle.
 
## What it does
 
You enter a product name, details, target audience and tone. PinPilot generates:
 
- **Content angles**: different reasons a buyer might want your product
- **Pin titles**: 50 to 90 characters, written for each angle
- **Text overlays**: a headline and subtext for your pin designs, matched to each angle
- **Keyword ideas**: phrases people type into Pinterest search
- **Descriptions**: Pinterest-style descriptions with a soft call to action
- **A weekly posting plan**: pins spread across the week, downloadable as a CSV file
You can also upload a product photo. The model describes it, and that description is used to make the copy more specific.
 
Results appear section by section as they finish, so you don't have to wait for everything at once.
 
## What you need
 
- A Windows PC (Mac and Linux should work too, but these steps are written for Windows)
- Python 3.11 or newer, from [python.org](https://www.python.org/downloads/) (tick **Add python.exe to PATH** when installing)
- [Ollama](https://ollama.com), which runs the model on your computer
- Enough memory for the model you pick. As a rough guide from Ollama's docs, 8 GB of RAM is fine for small models, and 16 GB or more is better for the larger ones.
## Setup (Windows)
 
**1. Install Ollama** from [ollama.com](https://ollama.com) and run the installer. It keeps running in the background.
 
**2. Download a Gemma model.** Open PowerShell and run one of these:
 
```
ollama pull gemma3        # 4B model, about 3.3 GB, can read images
ollama pull gemma3:1b     # 1B model, about 815 MB, fastest, text only
ollama pull gemma3:12b    # 12B model, about 8.1 GB, better writing, needs more RAM
```
 
**3. Check that the model works:**
 
```
ollama run gemma3 "say hi"
```
 
If you get an answer, type `/bye` to exit.
 
**4. Get the project and open its folder:**
 
```
git clone <YOUR-REPO-URL>
cd pinpilot
```
 
**5. Create a virtual environment and install the packages:**
 
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
 
If PowerShell says scripts are disabled, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try activating again.
 
**6. Start the app:**
 
```
streamlit run app.py
```
 
A browser tab opens at `http://localhost:8501`.
 
## How to use it
 
1. Fill in the product name, details, audience and tone.
2. Optionally upload a product photo (use the 4B or 12B model for this, since the 1B model can't read images).
3. Pick **Quick** for faster results or **Full** for more variety.
4. Pick the model, and choose how many pins per week you want.
5. Click **Generate** and watch the tabs fill in.
6. Open the **Weekly plan** tab and download the CSV.
The speed of each run is shown under the results.
 
## Project files
 
| File | What it does |
|---|---|
| `app.py` | The Streamlit screen: the input form, the tabs and the CSV download |
| `pinpilot.py` | The brain: talks to Ollama, builds the prompts, generates each section and builds the weekly plan |
| `requirements.txt` | The Python packages the project needs |
 
## How it works
 
```
product details (+ optional photo)
  → the model describes the photo (optional)
  → one call: content angles
  → one call per angle: titles and overlays for that angle
  → one call: keywords
  → one call: descriptions
  → plain Python: weekly plan (no AI involved)
```
 
Titles and overlays are generated together for each angle, so a pin's title and text overlay always match. The weekly plan is plain Python with no AI call, because spreading pins across a week is a simple rule that code handles instantly and identically every time.
 
## Using a different Ollama address
 
By default the app talks to Ollama on your own computer at `http://localhost:11434`. You can change this in the app's sidebar, or by setting the `OLLAMA_URL` environment variable before starting the app. This lets the same app use a model hosted on another machine.
 
## Troubleshooting
 
**"500 Server Error" or "Could not generate..."**
Ollama is reachable but failed on the request. Try these in order:
1. Run `ollama run gemma3 "say hi"` in PowerShell. If that fails, the problem is Ollama, not PinPilot.
2. Make sure the model you picked in the app is one you have downloaded (`ollama list` shows them).
3. Quit Ollama from the system tray, start it again, and retry.
4. Close other heavy programs. If your computer is low on memory, Ollama can fail to load the model.
5. Look at `%LOCALAPPDATA%\Ollama\server.log` for the real error message.
**Connection error**
Ollama isn't running, or the address in the sidebar is wrong. Open `http://localhost:11434` in your browser. It should say "Ollama is running".
 
**It's very slow**
Local models run slower on laptops without a strong graphics card. Use **Quick** mode, switch to `gemma3:1b`, and close other programs.
 
**Image upload doesn't work**
The 1B model can't read images. Choose `gemma3` or `gemma3:12b`.
 
## Good to know
 
- The weekly posting times are starting guesses, not proven best times. Replace them with what your own Pinterest analytics show.
- Check Pinterest's current title and description length limits before posting.
- AI-written copy should be read and edited by you before you publish it.
- Local models can make mistakes. Always review the output for claims that don't match your product.
## Why open-source AI
 
- **No usage limit and no cost per pin.** The model runs on your computer, so you can generate as much as you want for free.
- **Control.** You can change the prompts and the steps, and swap models whenever a better one comes along.
- **Honest trade-off.** A paid hosted model would be faster and might write more polished copy. The same app can point at a model hosted elsewhere through the Ollama address setting. 
