import typer
import subprocess
import requests
import tempfile
from dotenv import load_dotenv
import os

app = typer.Typer()


def get_commit_message(diff: str) -> str:
    load_dotenv()
    key = os.getenv("OPENROUTER_API_KEY")

    prompt = f"""You are an expert developer. Given the following git diff, generate a single conventional commit message (e.g. feat, fix, refactor, chore...).
Reply with only the commit message, nothing else.

Git diff:
{diff}"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": prompt}],
        },
    )

    data = response.json()
    return data["choices"][0]["message"]["content"]


# making the edit experience slightly better with notepad (doesn't sound like a really smart idea but let's try it)
def edit_in_notepad(message: str) -> str:

    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write(message)
        tmpfile = f.name

    subprocess.run(["notepad.exe", tmpfile])

    with open(tmpfile) as f:
        edited = f.read().strip()

    os.unlink(tmpfile)
    return edited


@app.command()
def generate(interactive: bool = False):

    result = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True)

    diff = result.stdout

    if not diff:
        typer.echo("No staged changes found. Use git add first.")
        raise typer.Exit()

    typer.echo("Generating commit message...")
    message = get_commit_message(diff)

    # interactive mode
    if interactive:
        while True:
            typer.echo("Interactive mode!")
            typer.echo(f"Suggested commit message :\n\n{message}")
            typer.echo("[a] Accept & commit")
            typer.echo("[r] Regenerate")
            typer.echo("[e] Edit")
            typer.echo("[q] Quit")
            choice = typer.prompt("Your choice").strip().lower()
            if choice == "a":
                # commit with the message ==== accept
                subprocess.run(["git", "commit", "-m", message])
                break
            elif choice == "r":
                # regenerate
                typer.echo("regenerating commit message...")
                message = get_commit_message(diff)
                pass
            elif choice == "e":
                # let user edit
                message = edit_in_notepad(message)
                pass
            elif choice == "q":
                # quit
                raise typer.Exit()
            else:
                typer.echo("Invalid choice, try again.")
    else:
        typer.echo(f"Suggested commit message :\n\n{message}")

    if typer.confirm("wanna commit with this message???"):
        subprocess.run(["git", "commit", "-m", message])


if __name__ == "__main__":
    app()
