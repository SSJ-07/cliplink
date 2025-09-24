# ClipLink Backend

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the backend directory:
```bash
OPENAI_API_KEY=your_actual_openai_api_key_here
```

3. Run the server:
```bash
python3 app.py
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## Security Note

Never commit your `.env` file to version control. The `.env` file is already added to `.gitignore`.
