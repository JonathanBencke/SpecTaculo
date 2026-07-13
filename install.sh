#!/usr/bin/env bash
# Instala a esteira de agentes SpecTaculo em uma CLI suportada.
#
# Uso:
#   ./install.sh -t claude                    # instala local para Claude Code
#   ./install.sh -t all -g                    # regenera artefatos e instala tudo
#   ./install.sh -t opencode -d ../meu-projeto
#   curl -fsSL https://raw.githubusercontent.com/JonathanBencke/SpecTaculo/main/install.sh | SPECTACULO_TOOL=opencode bash
#
# Equivalente bash do install.ps1.

set -euo pipefail

TOOL="${SPECTACULO_TOOL:-}"
TARGET="."
GENERATE=0
VERSION=""

# ---------------------------------------------------------------------------
# Parsing de argumentos
# ---------------------------------------------------------------------------
usage() {
  cat <<'EOF'
Uso: install.sh [-t|--tool claude|kimi|opencode|kiro|all] [-d|--target DIR]
                [-g|--generate] [-v|--version TAG] [-u|--uninstall] [-h|--help]

  -t, --tool TOOL      CLI alvo (claude, kimi, opencode, kiro, all).
                       Pode ser omitido se SPECTACULO_TOOL estiver definida.
  -d, --target DIR     Diretório de destino (padrão: diretório atual).
  -g, --generate       Regenera os artefatos a partir do código-fonte (modo local).
  -v, --version TAG    Versão/tag específica do GitHub (ex: v1.0.0). Padrão: latest.
  -u, --uninstall      Remove os artefatos do SpecTaculo do destino.
  -h, --help           Mostra esta ajuda.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--tool)      TOOL="$2"; shift 2 ;;
    -d|--target)    TARGET="$2"; shift 2 ;;
    -g|--generate)  GENERATE=1; shift ;;
    -v|--version)   VERSION="$2"; shift 2 ;;
    -u|--uninstall) UNINSTALL=1; shift ;;
    -h|--help)      usage; exit 0 ;;
    *) echo "Argumento desconhecido: $1" >&2; usage; exit 1 ;;
  esac
done

UNINSTALL="${UNINSTALL:-0}"

if [[ -z "$TOOL" ]]; then
  echo "Erro: informe -t <tool> ou defina SPECTACULO_TOOL." >&2
  exit 1
fi

case "$TOOL" in
  claude|kimi|opencode|kiro) TOOLS=("$TOOL") ;;
  all) TOOLS=(claude kimi opencode kiro) ;;
  *) echo "Erro: tool inválido '$TOOL'." >&2; exit 1 ;;
esac

# Mapeamento CLI -> subdir de origem (copia-se o conteúdo integral de cada subdir,
# pois cada um contém apenas os arquivos do tipo certo: SKILL.md, *.md, *.json).
declare -A DIR_MAP=(
  [claude]=".claude/skills"
  [kimi]=".kimi-code/skills"
  [opencode]=".opencode/agents"
  [kiro]=".kiro/agents"
)

# ---------------------------------------------------------------------------
# Desinstalação
# ---------------------------------------------------------------------------
if [[ "$UNINSTALL" == "1" ]]; then
  echo "Removendo SpecTaculo de: $TARGET"
  for t in "${TOOLS[@]}"; do
    dest="$TARGET/${DIR_MAP[$t]}"
    if [[ -d "$dest" ]]; then
      rm -rf "$dest"
      echo "[-] removido: $dest"
    fi
  done
  echo "Desinstalação concluída."
  exit 0
fi

# ---------------------------------------------------------------------------
# Detecção de modo: remoto (curl|bash) vs local (clone)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
REMOTE_MODE=0
TEMP_DIR=""

if [[ -z "$SCRIPT_DIR" || ! -d "$SCRIPT_DIR/generated" ]]; then
  REMOTE_MODE=1
  TEMP_DIR="$(mktemp -d)"
  trap 'rm -rf "$TEMP_DIR"' EXIT

  if [[ -n "$VERSION" ]]; then
    RELEASE_URL="https://api.github.com/repos/JonathanBencke/SpecTaculo/releases/tags/$VERSION"
  else
    RELEASE_URL="https://api.github.com/repos/JonathanBencke/SpecTaculo/releases/latest"
  fi
  echo "Modo remoto. Buscando release ($VERSION ou latest)..."
  if ! ASSET_JSON="$(curl -fsSL "$RELEASE_URL")"; then
    echo "Erro: falha ao buscar release em $RELEASE_URL" >&2
    exit 1
  fi

  ZIP_URL="$(printf '%s' "$ASSET_JSON" \
    | grep -o '"browser_download_url": *"[^"]*SpecTaculo-[^"]*\.zip"' \
    | head -n1 \
    | sed -E 's/.*"([^"]+)"$/\1/')"
  if [[ -z "$ZIP_URL" ]]; then
    echo "Erro: nenhum asset SpecTaculo-*.zip encontrado no release." >&2
    exit 1
  fi

  # Checksum (se existir .sha256 ao lado do zip)
  SHA_URL="${ZIP_URL}.sha256"
  ZIP_FILE="$TEMP_DIR/spectaculo.zip"
  echo "Baixando $ZIP_URL ..."
  curl -fsSL "$ZIP_URL" -o "$ZIP_FILE"

  if curl -fsSI "$SHA_URL" >/dev/null 2>&1; then
    echo "Verificando checksum..."
    EXPECTED="$(curl -fsSL "$SHA_URL" | awk '{print $1}')"
    ACTUAL="$(sha256sum "$ZIP_FILE" | awk '{print $1}')"
    if [[ "${EXPECTED,,}" != "${ACTUAL,,}" ]]; then
      echo "Erro: checksum divergente." >&2
      echo "  esperado: $EXPECTED" >&2
      echo "  atual:    $ACTUAL" >&2
      exit 1
    fi
    echo "Checksum OK."
  else
    echo "Aviso: nenhum checksum .sha256 publicado; pulando verificação."
  fi

  echo "Extraindo..."
  unzip -q "$ZIP_FILE" -d "$TEMP_DIR"
  SCRIPT_DIR="$TEMP_DIR"
fi

# ---------------------------------------------------------------------------
# (Re)geração local opcional
# ---------------------------------------------------------------------------
if [[ "$REMOTE_MODE" == "0" && "$GENERATE" == "1" ]]; then
  PY=""
  if [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
    PY="$SCRIPT_DIR/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
  elif command -v python >/dev/null 2>&1; then
    PY="python"
  else
    echo "Erro: Python não encontrado." >&2
    exit 1
  fi
  echo "Gerando artefatos com: $PY"
  "$PY" "$SCRIPT_DIR/src/generate.py" "$TOOL"
fi

SOURCE="$SCRIPT_DIR/generated"
if [[ ! -d "$SOURCE" ]]; then
  echo "Erro: diretório 'generated' não encontrado em '$SCRIPT_DIR'." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Instalação
# ---------------------------------------------------------------------------
mkdir -p "$TARGET"
echo "Destino: $TARGET"
for t in "${TOOLS[@]}"; do
  src="$SOURCE/${DIR_MAP[$t]}"
  dst="$TARGET/${DIR_MAP[$t]}"
  if [[ ! -d "$src" ]]; then
    echo "Aviso: nenhum artefato para '$t' em '$src'." >&2
    continue
  fi
  mkdir -p "$dst"
  # Copia preservando subdiretórios (skills vêm em subpastas).
  cp -r "$src"/. "$dst"/
  echo "[+] $t -> $dst"
done

echo "Instalação concluída."
