# Known Issues

This document records verified operational constraints and known technical limitations in the current release of JyotishAI.

## 1. Third-Party LLM Billing Quotas

- Behavior: Direct OpenAI (`gpt-4o-mini`, `gpt-4o`) and Anthropic (`claude-3-5-sonnet`) models return `429 Insufficient Quota` or `400 Credit Balance Too Low` if the user's API key does not have active paid billing credits attached.
- Workaround: The system automatically falls back to `gemini-flash-latest` or OpenRouter endpoints when direct provider calls fail. Ensure API keys have billing credits enabled on respective provider dashboards.

## 2. Ephemeris Initialization Delay on First Startup

- Behavior: The backend downloads Swiss Ephemeris data files (~118 MB total) on the initial astronomical calculation call if binary files are not present in container storage.
- Workaround: Files are cached locally in the backend volume after first execution. Subsequent chart calculations execute synchronously without delay.

## 3. Large File Ingestion Timeouts

- Behavior: Uploading PDF files exceeding 10 MB or containing scanned image pages without selectable text can result in extended processing times or document status `failed`.
- Workaround: Restrict document uploads to text-based PDF, DOCX, TXT, or Markdown files under 10 MB.

## 4. Middleware Deprecation Warning in Logs

- Behavior: Next.js 16 container build logs display a warning regarding `middleware` file convention deprecation in favor of `proxy`.
- Impact: None. The application operates normally and routing functions as expected.
