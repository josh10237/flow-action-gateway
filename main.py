#!/usr/bin/env python3
"""
Wispr Actions - Voice-controlled gateway for productivity apps
Entry point with onboarding flow and UI launcher
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def check_dependencies():
    """Check if required packages are installed."""
    try:
        import textual
        import openai
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("\nInstall dependencies with:")
        print("  pip install textual openai python-dotenv")
        return False


def load_config():
    """Load configuration from .env file."""
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
    return {"openai_api_key": os.getenv("OPENAI_API_KEY")}


def needs_onboarding(config):
    """Check if user needs to go through onboarding."""
    return not config.get("openai_api_key")


def run_onboarding():
    """Interactive onboarding to collect OpenAI API key."""
    print("\n" + "="*50)
    print("🎙️  Welcome to Wispr Actions!")
    print("="*50)
    print("\nLet's get you set up...\n")

    print("OpenAI API Key (required for voice transcription)")
    print("Get your key at: https://platform.openai.com/api-keys\n")

    openai_key = input("Paste your OpenAI API key: ").strip()

    if not openai_key:
        print("\n❌ OpenAI API key is required.")
        sys.exit(1)

    env_path = Path(__file__).parent / ".env"
    with open(env_path, "w") as f:
        f.write(f"OPENAI_API_KEY={openai_key}\n")

    print("\n✅ Configuration saved to .env")
    print("\nLaunching Wispr Actions...\n")


def launch_app(config):
    """Launch the main Textual UI application."""
    from ui.app import WisprActionsApp

    app = WisprActionsApp(config)
    try:
        app.run()
    finally:
        if app.audio_capture:
            app.audio_capture.cleanup()


def main():
    """Main entry point."""
    try:
        if not check_dependencies():
            sys.exit(1)

        config = load_config()

        if needs_onboarding(config):
            run_onboarding()
            config = load_config()

        launch_app(config)
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
