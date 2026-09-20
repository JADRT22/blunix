"""Entry point de `python -m blunix`.

Sem argumentos abre a GUI; com argumentos, roda a CLI.
"""
import sys


def main() -> int:
    if len(sys.argv) <= 1:
        try:
            from .gui import run
        except ImportError as exc:
            print(
                "GTK 4 / PyGObject não disponível — instale python-gobject e gtk4,\n"
                f"ou use a CLI: python -m blunix --help\n({exc})",
                file=sys.stderr,
            )
            return 2
        return run()
    from .cli import main as cli_main
    return cli_main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
