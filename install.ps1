<#
.SYNOPSIS
    Instala a esteira de agentes SpecTaculo em uma CLI suportada.

.DESCRIPTION
    Copia os artefatos gerados em generated/ para a estrutura nativa da
    ferramenta escolhida (Claude Code, kimi-code, opencode, kiro-cli).

    Quando executado localmente, pode regenerar os artefatos a partir do
    código-fonte. Quando executado remotamente via irm ... | iex, o script
    baixa o release mais recente (zip pré-gerado) do GitHub.

.PARAMETER Tool
    CLI alvo: claude, kimi, opencode, kiro ou all.
    Pode ser omitido se a variável de ambiente SPECTACULO_TOOL estiver definida.

.PARAMETER Target
    Diretório de destino. Padrão: diretório atual.

.PARAMETER Generate
    Se definido, executa src/generate.py antes de instalar.
    Aplica-se apenas à execução local.

.PARAMETER Version
    Versão/tag específica do GitHub (ex: v1.0.0). Padrão: latest (release mais recente).
    Só se aplica à execução remota.

.PARAMETER Uninstall
    Remove os artefatos do SpecTaculo do diretório de destino.

.PARAMETER Update
    Equivalente a -Generate + reinstalação (modo local). No modo remoto,
    apenas reinstala a versão mais recente por cima.

.EXAMPLE
    .\install.ps1 -Tool claude
    .\install.ps1 -Tool all -Generate
    .\install.ps1 -Tool kimi -Target ..\meu-projeto
    .\install.ps1 -Tool opencode -Version v1.2.0
    .\install.ps1 -Tool all -Uninstall
    $env:SPECTACULO_TOOL = "claude"; irm https://raw.githubusercontent.com/JonathanBencke/SpecTaculo/main/install.ps1 | iex
#>
[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet("claude", "kimi", "opencode", "kiro", "all")]
    [string]$Tool = $env:SPECTACULO_TOOL,

    [Parameter()]
    [string]$Target = ".",

    [Parameter()]
    [switch]$Generate,

    [Parameter()]
    [string]$Version,

    [Parameter()]
    [switch]$Uninstall,

    [Parameter()]
    [switch]$Update
)

# Garante codificação UTF-8 para saída no console
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Test-Command($cmd) {
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Get-ToolMapping() {
    return @{
        claude   = @{ Dir = ".claude/skills";     Pattern = "*" }
        kimi     = @{ Dir = ".kimi-code/skills";  Pattern = "*" }
        opencode = @{ Dir = ".opencode/agents";   Pattern = "*.md" }
        kiro     = @{ Dir = ".kiro/agents";       Pattern = "*.json" }
    }
}

function Install-Tool($tool, $source, $dest) {
    $mapping = Get-ToolMapping
    $m = $mapping[$tool]
    $srcPath = Join-Path $source $m.Dir
    $dstPath = Join-Path $dest $m.Dir

    if (-not (Test-Path $srcPath)) {
        Write-Warning "Nenhum artefato encontrado para '$tool' em '$srcPath'."
        return
    }

    New-Item -ItemType Directory -Path $dstPath -Force | Out-Null

    Get-ChildItem -Path $srcPath -Recurse -Filter $m.Pattern | ForEach-Object {
        $relative = $_.FullName.Substring($srcPath.Length + 1)
        $targetFile = Join-Path $dstPath $relative
        New-Item -ItemType Directory -Path (Split-Path $targetFile) -Force | Out-Null
        Copy-Item -Path $_.FullName -Destination $targetFile -Force
        Write-Host "[+] $tool -> $targetFile" -ForegroundColor Green
    }
}

function Uninstall-Tool($tool, $dest) {
    $mapping = Get-ToolMapping
    $m = $mapping[$tool]
    $dstPath = Join-Path $dest $m.Dir
    if (Test-Path $dstPath) {
        Remove-Item -Path $dstPath -Recurse -Force
        Write-Host "[-] removido: $dstPath" -ForegroundColor Yellow
    } else {
        Write-Host "(nada para remover em $dstPath)" -ForegroundColor DarkGray
    }
}

function Confirm-Checksum($zipFile, $expectedSha256) {
    if (-not $expectedSha256) { return $false }
    $actual = (Get-FileHash -Path $zipFile -Algorithm SHA256).Hash
    return $actual -ieq $expectedSha256
}

# Validações
if (-not $Tool) {
    Write-Error "Informe -Tool ou defina a variável de ambiente SPECTACULO_TOOL."
    exit 1
}

# Garante que o diretório de destino exista
if (-not (Test-Path $Target)) {
    New-Item -ItemType Directory -Path $Target -Force | Out-Null
}
$Target = Resolve-Path $Target
$tools = if ($Tool -eq "all") { @("claude", "kimi", "opencode", "kiro") } else { @($Tool) }

# ---------------------------------------------------------------------------
# Desinstalação
# ---------------------------------------------------------------------------
if ($Uninstall) {
    Write-Host "Removendo SpecTaculo de: $Target"
    foreach ($t in $tools) { Uninstall-Tool -tool $t -dest $Target }
    Write-Host "Desinstalação concluída." -ForegroundColor Cyan
    exit 0
}

Write-Host "Instalando SpecTaculo para: $Tool"
Write-Host "Destino: $Target"

# Detecta execução remota (irm ... | iex)
$RemoteMode = [string]::IsNullOrEmpty($PSScriptRoot)
$TempDir = $null
$ScriptDir = $PSScriptRoot

if ($RemoteMode) {
    $TempDir = Join-Path $env:TEMP ("SpecTaculo-" + [System.Guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

    $ReleaseLabel = if ($Version) { "tag $Version" } else { "latest" }
    $ReleaseUrl = if ($Version) {
        "https://api.github.com/repos/JonathanBencke/SpecTaculo/releases/tags/$Version"
    } else {
        "https://api.github.com/repos/JonathanBencke/SpecTaculo/releases/latest"
    }
    Write-Host "Modo remoto detectado. Buscando release ($ReleaseLabel)..."
    try {
        $release = Invoke-RestMethod -Uri $ReleaseUrl -UseBasicParsing
    } catch {
        Write-Error "Falha ao buscar o release ($ReleaseLabel): $_"
        exit 1
    }

    $asset = $release.assets | Where-Object { $_.name -like "SpecTaculo-*.zip" } | Select-Object -First 1
    if (-not $asset) {
        Write-Error "Nenhum asset .zip encontrado no release $($release.tag_name)."
        exit 1
    }

    $zipUrl = $asset.browser_download_url
    $zipFile = Join-Path $TempDir $asset.name
    Write-Host "Baixando $($asset.name) ($($asset.size) bytes)..."
    try {
        Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile -UseBasicParsing
    } catch {
        Write-Error "Falha ao baixar o release: $_"
        exit 1
    }

    # Verificação de checksum (asset .sha256 publicado ao lado do zip)
    $shaAsset = $release.assets | Where-Object { $_.name -eq "$($asset.name).sha256" } | Select-Object -First 1
    if ($shaAsset) {
        Write-Host "Verificando checksum SHA256..."
        try {
            $shaContent = (Invoke-WebRequest -Uri $shaAsset.browser_download_url -UseBasicParsing).Content
            $expected = ($shaContent -split '\s+')[0].Trim()
            if (Confirm-Checksum -zipFile $zipFile -expectedSha256 $expected) {
                Write-Host "Checksum OK." -ForegroundColor Green
            } else {
                Write-Error "Checksum divergente. Abortando por segurança."
                exit 1
            }
        } catch {
            Write-Warning "Não foi possível verificar o checksum ($_), prosseguindo."
        }
    } else {
        Write-Host "Aviso: nenhum checksum .sha256 publicado; pulando verificação." -ForegroundColor DarkYellow
    }

    Write-Host "Extraindo release..."
    Expand-Archive -Path $zipFile -DestinationPath $TempDir -Force
    $ScriptDir = $TempDir
}

try {
    # Resolve o interpretador Python (prioriza venv do projeto)
    $PythonPath = if (Test-Path (Join-Path $ScriptDir ".venv/Scripts/python.exe")) {
        Join-Path $ScriptDir ".venv/Scripts/python.exe"
    } elseif (Test-Command python) {
        "python"
    } else {
        $null
    }

    # Regenera artefatos se solicitado (apenas modo local)
    if (-not $RemoteMode -and ($Generate -or $Update)) {
        if (-not $PythonPath) {
            Write-Error "Python não encontrado. Instale o Python ou crie um venv com as dependências."
            exit 1
        }
        Write-Host "Gerando artefatos com: $PythonPath"
        & $PythonPath (Join-Path $ScriptDir "src/generate.py") $Tool --clean
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Falha ao gerar artefatos."
            exit 1
        }
    }

    $source = Join-Path $ScriptDir "generated"
    if (-not (Test-Path $source)) {
        # Auto-gera se estiver em modo local e o Python estiver disponível.
        if (-not $RemoteMode -and $PythonPath) {
            Write-Host "Diretório 'generated' ausente. Gerando automaticamente..." -ForegroundColor Yellow
            & $PythonPath (Join-Path $ScriptDir "src/generate.py") $Tool
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Falha ao gerar artefatos automaticamente."
                exit 1
            }
        } else {
            Write-Error "Diretório 'generated' não encontrado em '$ScriptDir'."
            exit 1
        }
    }

    # Instalação
    foreach ($t in $tools) {
        Install-Tool -tool $t -source $source -dest $Target
    }

    Write-Host "Instalação concluída." -ForegroundColor Cyan
}
finally {
    if ($RemoteMode -and $TempDir -and (Test-Path $TempDir)) {
        Write-Host "Limpando arquivos temporários..."
        Remove-Item -Path $TempDir -Recurse -Force
    }
}
