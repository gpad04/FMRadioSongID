# FM Song Identifier (RTL-SDR + Flask)

## Setup

1. Install Python 3.x
2. Install ffmpeg and add it to your PATH: https://www.gyan.dev/ffmpeg/builds/
3. Install rtl_fm and make sure your RTL-SDR is working.

## Python Environment

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Configure AcrCloud

Edit `acr_identify.py` and insert your credentials:
- `access_key`
- `access_secret`
- `host`

## Run

```bash
python app.py
```

Then open http://localhost:5000
