#!/usr/bin/env bash
# Constrói um AppImage do Blunix (executor de arquivo único).
#
# O AppImage usa o Python 3 + GTK/PyGObject do sistema (padrão em qualquer
# distro Linux moderna com desktop). Duplo clique → abre.
#
# Uso:  ./tools/build-appimage.sh
# Saída: Blunix-<versão>-x86_64.AppImage (na raiz do projeto)
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

VERSION="$(grep -m1 '^version' pyproject.toml | sed 's/.*"\(.*\)".*/\1/')"
ARCH="$(uname -m)"
APPDIR="build/AppDir"
OUT="Blunix-${VERSION}-${ARCH}.AppImage"

echo "==> Versão: ${VERSION} | Arquitetura: ${ARCH}"

# ---------------------------------------------------------------- precheck
command -v python3 >/dev/null || { echo "ERRO: python3 não encontrado"; exit 1; }
python3 -c "import gi; gi.require_version('Gtk','4.0'); import gi.repository.Gtk" 2>/dev/null \
  || { echo "ERRO: PyGObject/GTK4 não disponível no python3 do sistema"; exit 1; }

# ---------------------------------------------------------------- limpeza
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib/blunix" "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
         "$APPDIR/usr/share/applications" "$APPDIR/usr/bin"

# ---------------------------------------------------------------- AppRun
cat > "$APPDIR/AppRun" <<'APPRUN'
#!/usr/bin/env bash
# AppRun do Blunix: executa o app com o Python do sistema.
set -e
HERE="$(cd "$(dirname "$(readlink -f "${0}")")" && pwd)"
export APPDIR="${HERE}"
export APPIMAGE="${APPIMAGE:-}"
export GI_TYPELIB_PATH="${GI_TYPELIB_PATH:-}"
exec python3 -s -P "${HERE}/usr/lib/blunix/run.py" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# ---------------------------------------------------------------- run.py (bootstrap do pacote)
cat > "$APPDIR/usr/lib/blunix/run.py" <<'RUNPY'
"""Bootstrap: adiciona o dir do pacote ao sys.path e chama a GUI/CLI."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from blunix.cli import main  # noqa: E402

# Dentro do AppImage, sem argumentos = GUI (amigável para leigos)
if len(sys.argv) <= 1:
    sys.exit(main(["gui"]))
sys.exit(main(sys.argv[1:]))
RUNPY

# ---------------------------------------------------------------- pacote
cp -r blunix "$APPDIR/usr/lib/blunix/blunix"
find "$APPDIR/usr/lib/blunix" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$APPDIR/usr/lib/blunix" -name '*.pyc' -delete 2>/dev/null || true

cp "data/com.github.fernando.blunix.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/"
mkdir -p "$APPDIR/usr/lib/blunix/share"
cp "data/com.github.fernando.blunix.png" "$APPDIR/usr/lib/blunix/share/com.github.fernando.blunix.png"

sed "s|Exec=blunix gui|Exec=Blunix|; s|^Icon=.*|Icon=com.github.fernando.blunix|" \
    data/blunix.desktop > "$APPDIR/usr/share/applications/com.github.fernando.blunix.desktop"
cp "$APPDIR/usr/share/applications/com.github.fernando.blunix.desktop" "$APPDIR/com.github.fernando.blunix.desktop"
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/com.github.fernando.blunix.png" "$APPDIR/.DirIcon"
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/com.github.fernando.blunix.png" "$APPDIR/com.github.fernando.blunix.png"

# ---------------------------------------------------------------- appimagetool
# Baixa appimagetool (ferramenta oficial, ~2 MB) se ainda não existir
TOOL="build/appimagetool-${ARCH}.AppImage"
mkdir -p build
if [ ! -x "$TOOL" ]; then
  echo "==> Baixando appimagetool…"
  wget -q --show-progress -O "$TOOL" \
    "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"
  chmod +x "$TOOL"
fi

echo "==> Montando AppImage…"
# AppDir é Python puro (sem binários): ARCH precisa ser explícito.
# appimagetool é ele próprio um AppImage: roda extraído (--appimage-extract-and-run).
export ARCH="$ARCH"
if [ "$(id -u)" -eq 0 ]; then
  "$TOOL" --appimage-extract-and-run "$APPDIR" "$OUT"
else
  chmod +x "$TOOL"
  "$TOOL" --appimage-extract-and-run "$APPDIR" "$OUT" 2>/dev/null \
    || "$TOOL" "$APPDIR" "$OUT"
fi

chmod +x "$OUT"
echo ""
echo "✅ Pronto: $OUT"
echo "   Envie esse arquivo para quem quiser — é um executor único."
echo "   Dica: blunix install-menu cria o atalho no menu de aplicativos."
