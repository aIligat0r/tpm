from typing import Annotated

import typer

from telegram_pm.run import run_tpm


app = typer.Typer()


@app.command(no_args_is_help=True)
def run(
    db_path: Annotated[str, typer.Option()],
    channels_filepath: str = typer.Option(
        None,
        "--channels-filepath",
        "--chf",
        help="File of channel usernames (file where in each line Telegram username)",
    ),
    channel: list[str] = typer.Option(
        None,
        "--channel",
        "--ch",
        help="Channel (many channels: --ch username1 --ch username2)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "--v",
        help="Verbose mode",
    ),
):
    channels_list = []
    if channels_filepath:
        try:
            with open(
                channels_filepath, encoding="utf-8", errors="ignore"
            ) as channels_file:
                channels_list = channels_file.read().splitlines()
        except FileNotFoundError:
            typer.echo(
                message=typer.style(
                    f"[ERROR] File not found: {channels_filepath}",
                    fg=typer.colors.RED,
                    bold=True,
                ),
                err=True,
            )
            raise typer.Exit(1)
        except Exception as error:
            typer.echo(message=error, err=True)
            raise typer.Exit(1)
    if channel:
        channels_list = channel
    if not channels_list:
        typer.echo(
            message=typer.style(
                "[ERROR] Channels must be entered.", fg=typer.colors.RED, bold=True
            ),
            err=True,
        )
        raise typer.Exit(2)

    typer.echo("🚀 Run 🚀")
    try:
        run_tpm(channels=channels_list, verbose=verbose, db_path=db_path)
    except KeyboardInterrupt:
        typer.echo("🛑 Stopped 🛑")


if __name__ == "__main__":
    app()
