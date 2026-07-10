<#
.SYNOPSIS
    Instala a esteira de agentes SDD em uma CLI suportada.

.DESCRIPTION
    Copia os artefatos gerados em generated/ para a estrutura nativa da
    ferramenta escolhida (Claude Code, kimi-code, opencode, kiro-cli).
    Também pode regenerar os artefatos antes de instalar.

.PARAMETER Tool
    CLI alvo: claude, kimi, opencode, kiro ou all.
    Pode ser omitido se a variável de ambiente SPECTACULO_TOOL estiver definida.

.PARAMETER Target
    Diretório de destino. Padrão: diretório atual.

.PARAMETER Generate
    Se definido, executa src/generate.py antes de instalar.

.EXAMPLE
    .\install.ps1 -Tool claude
    .\install.ps1 -Tool all -Generate
    .\install.ps1 -Tool kimi -Target ..\meu-projeto
    $env:SPECTACULO_TOOL = "claude"; irm https://.../install.ps1 | iex
#>
[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet("claude", "kimi", "opencode", "kiro", "all")]
    [string]$Tool = $env:SPECTACULO_TOOL,

    [Parameter()]
    [string]$Target = ".",

    [Parameter()]
    [switch]$Generate
)

# Garante codificação UTF-8 para saída no console
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Resolve o diretório onde o script reside (suporta execução via irm | iex)
$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }

function Test-Command($cmd) {
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Install-Tool($tool, $source, $dest) {
    $mapping = @{
        claude   = @{ Dir = ".claude/skills";     Pattern = "*" }
        kimi     = @{ Dir = ".kimi-code/skills";  Pattern = "*" }
        opencode = @{ Dir = ".opencode/agents";   Pattern = "*.md" }
        kiro     = @{ Dir = ".kiro/agents";       Pattern = "*.json" }
    }

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
Write-Host "Instalando SpecTaculo para: $Tool"
Write-Host "Destino: $Target"

# Resolve o interpretador Python (prioriza venv do projeto)
$PythonPath = if (Test-Path (Join-Path $ScriptDir ".venv/Scripts/python.exe")) {
    Join-Path $ScriptDir ".venv/Scripts/python.exe"
} elseif (Test-Command python) {
    "python"
} else {
    $null
}

# Regenera artefatos se solicitado
if ($Generate) {
    if (-not $PythonPath) {
        Write-Error "Python não encontrado. Instale o Python ou crie um venv com as dependências."
        exit 1
    }
    Write-Host "Gerando artefatos com: $PythonPath"
    & $PythonPath (Join-Path $ScriptDir "src/generate.py") $Tool
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha ao gerar artefatos."
        exit 1
    }
}

$source = Join-Path $ScriptDir "generated"
if (-not (Test-Path $source)) {
    Write-Error "Diretório 'generated' não encontrado em '$ScriptDir'. Use -Generate ou execute src/generate.py."
    exit 1
}

# Instalação
$tools = if ($Tool -eq "all") { @("claude", "kimi", "opencode", "kiro") } else { @($Tool) }
foreach ($t in $tools) {
    Install-Tool -tool $t -source $source -dest $Target
}

Write-Host "Instalação concluída." -ForegroundColor Cyan
