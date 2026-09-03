# AutoApply

AutoApply is a local-first Windows application for organizing remote job sources, importing job reports from Gmail, discovering opportunities with a local language model, and assisting with job applications through a dedicated Chrome profile.

The FastAPI backend, SQLite database, browser automation, and Ollama integration all run on your computer. Site credentials are encrypted with Windows Data Protection API (DPAPI) before they are stored.

> [!WARNING]
> Browser-assisted applications can submit real forms. Review your candidate profile and test the workflow carefully before using it with live vacancies. CAPTCHA, MFA, missing files, and unknown required answers are intentionally left for human review.

## Features

- Manage and prioritize job-search websites.
- Store site credentials locally with Windows DPAPI encryption.
- Import structured vacancies from Gmail messages whose subject contains `AutoApply Report`.
- Track pending, running, and completed applications in SQLite.
- Discover new jobs from the rules in `BUSCAR_VAGAS.md` using LlamaIndex and Ollama.
- Generate a per-job ZIP containing a resume, cover letter, and job information.
- Inspect a signed-in LinkedIn profile and generate local optimization suggestions.
- Record manual application sessions for future site-specific learning.
- Monitor CPU, memory, GPU, disk, and Ollama status.

## Requirements

AutoApply currently targets Windows because credential encryption and the desktop launcher use Windows APIs.

- Windows 10 or 11
- Python 3.11 or newer (Python 3.12 is recommended)
- Google Chrome
- [Ollama](https://ollama.com/) available on `PATH`, or configured with `AUTOAPPLY_OLLAMA_EXE`
- Redis available on `PATH`, or configured with `AUTOAPPLY_REDIS_EXE`
- Approximately 4 GB of free disk space for the default local model

Redis is started by the desktop launcher and shown in the health panel. The backend can be run manually without Redis, although the dashboard will report it as unavailable.

## Installation

Clone the repository and enter its directory:

```powershell
git clone https://github.com/pedrocampos0/autoapply.git
Set-Location autoapply
```

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create the local configuration files:

```powershell
Copy-Item .env.example .env
Copy-Item data\candidate.example.json data\candidate_profile.json
```

Edit `.env` and set at least `GMAIL_ACCOUNT`. Then replace every example value in `data/candidate_profile.json` with verified candidate information. Both files are ignored by Git.

Download the default Ollama model:

```powershell
ollama pull llama2:7b-chat-q2_K
```

You may select another installed model through `OLLAMA_MODEL` in `.env`.

## Running manually

Start Ollama in one PowerShell window:

```powershell
ollama serve
```

Start Redis in another window if you want it included in the health status:

```powershell
redis-server --bind 127.0.0.1 --port 6379
```

Start a dedicated Chrome instance with its debugging interface restricted to the local machine:

```powershell
$chrome = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"
& $chrome --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 --user-data-dir="$env:LOCALAPPDATA\AutoApply\ChromeProfile"
```

If Chrome is installed elsewhere, update `$chrome` to its actual executable path. Sign in to Gmail, LinkedIn, and any job sites only in this dedicated Chrome profile.

Finally, start the API from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>.

## Optional desktop launcher

The launcher starts Ollama, Redis, FastAPI, and the dedicated Chrome profile together. Child processes are attached to a Windows Job Object so they stop when AutoApply closes.

Compile it from a Developer PowerShell for Visual Studio, or use the .NET Framework C# compiler directly:

```powershell
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" `
  /nologo /target:winexe `
  /reference:System.Windows.Forms.dll `
  /reference:System.Drawing.dll `
  /reference:System.Management.dll `
  /out:AutoApply.exe launcher\AutoApplyDesktop.cs
```

Run `AutoApply.exe` from the repository root. The launcher searches `PATH` for `ollama.exe` and `redis-server.exe`. Use these environment variables when the executables or repository are elsewhere:

```powershell
$env:AUTOAPPLY_ROOT = "C:\path\to\autoapply"
$env:AUTOAPPLY_OLLAMA_EXE = "C:\path\to\ollama.exe"
$env:AUTOAPPLY_REDIS_EXE = "C:\path\to\redis-server.exe"
```

## Configuration

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `GMAIL_ACCOUNT` | For Gmail imports | None | Gmail account expected in the dedicated Chrome profile. |
| `OLLAMA_MODEL` | No | `llama2:7b-chat-q2_K` | Local model used for chat and automation. |
| `OLLAMA_URL` | No | `http://127.0.0.1:11434` | Ollama API base URL. |
| `OLLAMA_NUM_GPU` | No | `24` | Preferred number of model layers offloaded to the GPU. |
| `LINKEDIN_PROFILE_URL` | No | None | Exact LinkedIn profile URL when automatic navigation cannot find it. |
| `AUTOAPPLY_PROFILE_FILE` | No | `data/candidate_profile.json` | Alternate candidate-profile JSON file. |
| `AUTOAPPLY_ROOT` | Launcher only | Auto-detected | Repository path when the launcher is stored elsewhere. |
| `AUTOAPPLY_CHROME_PROFILE` | Launcher only | Local AppData | Dedicated Chrome user-data directory. |
| `AUTOAPPLY_OLLAMA_EXE` | Launcher only | Searched on `PATH` | Full Ollama executable path. |
| `AUTOAPPLY_REDIS_EXE` | Launcher only | Searched on `PATH` | Full Redis executable path. |

## Project structure

```text
backend/                 FastAPI API and automation services
frontend/                Static dashboard
launcher/                Windows desktop launcher source
data/candidate.example.json
                         Safe candidate-profile template
BUSCAR_VAGAS.md          Job-discovery rules and filters
requirements.txt         Python dependencies
```

Runtime state is stored under `data/`, `logs/`, and `tmp/`. These paths, `.env`, the real candidate profile, generated databases, recordings, and compiled executables are excluded from version control.

## Privacy and security

- API, database, Ollama, and Chrome debugging interfaces bind to loopback addresses.
- Site passwords are encrypted through DPAPI and can only be decrypted by the same Windows user account.
- Candidate identity data remains in a local ignored JSON file.
- AI prompts are sent to the configured Ollama server, not to OpenAI.
- Successful AI interactions and unexpected errors are logged locally; credentials and cookies are not intentionally included.
- Treat the dedicated Chrome profile, local database, candidate profile, and logs as sensitive data and do not share them.

## Development checks

From the repository root, verify Python syntax without creating bytecode files:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m compileall -q backend
```

The application exposes health information at <http://127.0.0.1:8000/api/status> once it is running.

## Troubleshooting

- **Candidate profile not found:** copy `data/candidate.example.json` to `data/candidate_profile.json` and fill it in.
- **Gmail account rejected:** confirm `GMAIL_ACCOUNT` matches the account signed in to the dedicated Chrome profile.
- **Chrome automation offline:** close other dedicated instances and start Chrome with remote debugging on port `9222`.
- **Ollama unavailable:** run `ollama serve`, verify `OLLAMA_URL`, and confirm the selected model is installed.
- **Launcher cannot find a service:** place it on `PATH` or set the corresponding `AUTOAPPLY_*_EXE` variable.
- **PowerShell blocks virtual-environment activation:** run `Set-ExecutionPolicy -Scope Process Bypass`, then activate the environment again.
