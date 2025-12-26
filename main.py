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

    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "gmail_token": os.getenv("GMAIL_TOKEN"),
    }


def needs_onboarding(config):
    """Check if user needs to go through onboarding."""
    return not config.get("openai_api_key")


def run_onboarding():
    """Interactive onboarding flow to collect credentials."""
    print("\n" + "="*50)
    print("🎙️  Welcome to Wispr Actions!")
    print("="*50)
    print("\nLet's get you set up...\n")

    # Collect OpenAI API key
    print("Step 1: OpenAI API Key (required)")
    print("This is used for voice transcription and intelligence.")
    print("Get your key at: https://platform.openai.com/api-keys\n")

    openai_key = input("Paste your OpenAI API key: ").strip()

    if not openai_key:
        print("\n❌ OpenAI API key is required to use Wispr Actions.")
        sys.exit(1)

    # Optional: Gmail setup
    print("\n" + "-"*50)
    print("\nStep 2: Connect Services (optional)")
    print("You can add integrations now or skip and add them later.\n")
    print("Available services:")
    print("  1. Gmail (send emails as you)")
    print("  2. Skip for now\n")

    choice = input("Enter your choice (1-2): ").strip()

    gmail_token = None
    if choice == "1":
        print("\n[Gmail OAuth flow would go here]")
        print("For now, you can manually add GMAIL_TOKEN to .env later.")

    # Save to .env
    env_path = Path(__file__).parent / ".env"
    with open(env_path, "w") as f:
        f.write(f"OPENAI_API_KEY={openai_key}\n")
        if gmail_token:
            f.write(f"GMAIL_TOKEN={gmail_token}\n")

    print("\n✅ Configuration saved to .env")
    print("\nLaunching Wispr Actions...\n")


def launch_app(config):
    """Launch the main Textual UI application."""
    from ui.app import WisprActionsApp

    app = WisprActionsApp(config)
    try:
        app.run()
    finally:
        # CRITICAL: Clean up audio BEFORE returning to asyncio cleanup
        if app.audio_capture:
            app.audio_capture.cleanup()


def main():
    """Main entry point."""
    try:
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)

        # Load config
        config = load_config()

        # Run onboarding if needed
        if needs_onboarding(config):
            run_onboarding()
            config = load_config()  # Reload after onboarding

        # Launch the app
        launch_app(config)
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"\n\nError: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
