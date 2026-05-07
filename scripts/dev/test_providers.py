"""Quick smoke test: verify .env loads and each configured provider responds."""
import os
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "src"))
os.environ.setdefault("SPECSMITH_NO_AUTO_UPDATE", "1")

from specsmith.cli import _load_project_env  # noqa: E402

_load_project_env()

openai_key = os.environ.get("OPENAI_API_KEY", "")
google_key = os.environ.get("GOOGLE_API_KEY", "")

print(f"OPENAI_API_KEY : {'SET (' + str(len(openai_key)) + ' chars)' if openai_key else 'NOT SET'}")
print(f"GOOGLE_API_KEY : {'SET (' + str(len(google_key)) + ' chars)' if google_key else 'NOT SET'}")
print()

# --- Test OpenAI ---
if openai_key:
    print("Testing OpenAI (gpt-4.1-mini)...")
    try:
        from openai import OpenAI

        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": "Reply with exactly: OPENAI_OK"}],
            max_tokens=10,
        )
        reply = resp.choices[0].message.content.strip()
        print(f"  -> {reply}")
        print(f"  PASS" if "OPENAI_OK" in reply else f"  UNEXPECTED reply: {reply}")
    except Exception as e:
        print(f"  FAIL: {e}")
else:
    print("OpenAI: skipped (no key)")

print()

# --- Test Gemini ---
if google_key:
    print("Testing Gemini (gemini-2.5-flash)...")
    try:
        from google import genai

        client = genai.Client()
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Reply with exactly: GEMINI_OK",
        )
        reply = resp.text.strip()
        print(f"  -> {reply}")
        print(f"  PASS" if "GEMINI_OK" in reply else f"  UNEXPECTED reply: {reply}")
    except Exception as e:
        print(f"  FAIL: {e}")
else:
    print("Gemini: skipped (no key)")
