# Backup transcrito do projeto em Markdown (v3)
# PowerShell 7.5+
# Salva em: ./backup_
# Nome: BK{AAMMDDHHMMSS}_v3.md

$ErrorActionPreference = 'Stop'

$now = Get-Date -Format "yyMMddHHmmss"
$backupDir = Join-Path $PSScriptRoot 'backup_'
$outputFile = Join-Path $backupDir "BK${now}_v3.md"

$ignoreDirectories = @(
    '.git',
    '.mvn',
    '.idea',
    '.vscode',
    'node_modules',
    'target',
    'build',
    '.gradle',
    'backup_','__pycache__', '.venv'
)

$ignoreFileNames = @(
    'mvnw',
    'mvnw.cmd',
    'backup-projeto.ps1',
    'backup-projeto-v2.ps1',
    'backup-projeto-v3.ps1'
)

$ignoreContentPathPrefixes = @(
    'src/main/java/tech/vcinf/ecosysbridge/lov/'
)

$ignoreFileExtensions = @(
    '.log',
    '.class',
    '.jar',
    '.iml',
    '.md', 'pyc'
)

$binaryExtensions = @(
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp',
    '.exe', '.dll', '.so', '.dylib',
    '.zip', '.7z', '.rar', '.gz', '.tar',
    '.pdf',
    '.woff', '.woff2', '.ttf', '.eot',
    '.bin', '.dat'
)

$certificateExtensions = @('.pfx', '.crt', '.cer', '.pem', '.key', '.p12', '.p7b', '.jks')

function Normalize-RelativePath {
    param(
        [string]$RootPath,
        [string]$FilePath
    )

    $root = (Resolve-Path -Path $RootPath).Path
    if (-not $root.EndsWith([IO.Path]::DirectorySeparatorChar)) {
        $root += [IO.Path]::DirectorySeparatorChar
    }

    $full = (Resolve-Path -Path $FilePath).Path
    $relative = $full.Substring($root.Length)
    return $relative.Replace('\', '/')
}

function Should-IgnoreFile {
    param(
        [string]$RelativePath,
        [System.IO.FileInfo]$FileInfo
    )

    $segments = $RelativePath.Split('/', [System.StringSplitOptions]::RemoveEmptyEntries)
    foreach ($segment in $segments) {
        if ($ignoreDirectories -contains $segment) {
            return $true
        }
    }

    if ($ignoreFileNames -contains $FileInfo.Name) {
        return $true
    }

    $ext = [IO.Path]::GetExtension($FileInfo.Name).ToLowerInvariant()
    if ($ignoreFileExtensions -contains $ext) {
        return $true
    }

    return $false
}

function Should-IgnoreContent {
    param([string]$RelativePath)

    foreach ($prefix in $ignoreContentPathPrefixes) {
        if ($RelativePath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }

    return $false
}

function Is-CertificateFile {
    param([string]$FilePath)
    $ext = [IO.Path]::GetExtension($FilePath).ToLowerInvariant()
    return $certificateExtensions -contains $ext
}

function Get-CertificateInfo {
    param([string]$FilePath)

    $ext = [IO.Path]::GetExtension($FilePath).ToLowerInvariant()
    switch ($ext) {
        '.pfx' { return '[Arquivo de certificado PFX]' }
        '.cer' { return '[Arquivo de certificado CER]' }
        '.crt' { return '[Arquivo de certificado CRT]' }
        '.pem' { return '[Arquivo PEM]' }
        '.key' { return '[Arquivo de chave privada - Nao exibido por seguranca]' }
        '.p12' { return '[Arquivo de certificado PKCS#12]' }
        '.p7b' { return '[Arquivo de certificado PKCS#7 (.p7b)]' }
        '.jks' { return '[Keystore Java (JKS)]' }
        default { return '[Arquivo de certificado desconhecido]' }
    }
}

function Looks-Binary {
    param([string]$FilePath)

    $ext = [IO.Path]::GetExtension($FilePath).ToLowerInvariant()
    if ($binaryExtensions -contains $ext) {
        return $true
    }

    try {
        $bytes = [IO.File]::ReadAllBytes($FilePath)
        if ($bytes.Length -eq 0) {
            return $false
        }

        $sampleSize = [Math]::Min(4096, $bytes.Length)
        $controlCount = 0
        for ($i = 0; $i -lt $sampleSize; $i++) {
            $b = $bytes[$i]
            if ($b -eq 0) { return $true }
            if (($b -lt 9) -or (($b -gt 13) -and ($b -lt 32))) {
                $controlCount++
            }
        }

        return (($controlCount / $sampleSize) -gt 0.30)
    } catch {
        return $true
    }
}

function Get-CodeFence {
    param([string]$Text)

    if ($Text -match '```') {
        return '````'
    }
    return '```'
}

function Get-MarkdownLanguage {
    param([string]$FilePath)

    $ext = [IO.Path]::GetExtension($FilePath).ToLowerInvariant()
    switch ($ext) {
        '.java' { return 'java' }
        '.py' { return 'python' }
        '.xml' { return 'xml' }
        '.yml' { return 'yaml' }
        '.yaml' { return 'yaml' }
        '.json' { return 'json' }
        '.properties' { return 'properties' }
        '.sql' { return 'sql' }
        '.kt' { return 'kotlin' }
        '.groovy' { return 'groovy' }
        '.sh' { return 'bash' }
        '.ps1' { return 'powershell' }
        '.txt' { return 'text' }
        default { return '' }
    }
}

function Get-OmittedContentPlaceholder {
    param([string]$Language)

    switch ($Language) {
        'java' { return '// ...' }
        'json' { return '// ...' }
        'yaml' { return '# ...' }
        'properties' { return '# ...' }
        'sql' { return '-- ...' }
        'python' { return '#' }
        'bash' { return '# ...' }
        'powershell' { return '# ...' }
        default { return '...' }
    }
}

function Mask-Secrets {
    param([string]$Text)

    $maskedText = $Text
    $maskedCount = 0

    $linePatterns = @(
        '(?im)^(\s*(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|jwt\.secret|spring\.datasource\.password)\s*[:=]\s*)(.+)$',
        '(?im)^(\s*(?:export\s+)?(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)\s*=\s*)(.+)$'
    )

    foreach ($pattern in $linePatterns) {
        $matches = [regex]::Matches($maskedText, $pattern)
        if ($matches.Count -gt 0) {
            $maskedCount += $matches.Count
            $maskedText = [regex]::Replace($maskedText, $pattern, '$1***REDACTED***')
        }
    }

    $jsonPattern = '(?im)("(?:password|passwd|secret|token|apiKey|privateKey)"\s*:\s*")([^"]*)(")'
    $jsonMatches = [regex]::Matches($maskedText, $jsonPattern)
    if ($jsonMatches.Count -gt 0) {
        $maskedCount += $jsonMatches.Count
        $maskedText = [regex]::Replace($maskedText, $jsonPattern, '$1***REDACTED***$3')
    }

    $jdbcPattern = '(?im)(jdbc:[^\s]+://[^:\s/]+:)([^@\s]+)(@)'
    $jdbcMatches = [regex]::Matches($maskedText, $jdbcPattern)
    if ($jdbcMatches.Count -gt 0) {
        $maskedCount += $jdbcMatches.Count
        $maskedText = [regex]::Replace($maskedText, $jdbcPattern, '$1***REDACTED***$3')
    }

    return @{
        Text = $maskedText
        Count = $maskedCount
    }
}

if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

function Backup-ProjectAsMarkdownV3 {
    param([string]$Root)

    $allFiles = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue
    $processedCount = 0
    $skippedCount = 0
    $maskedFiles = 0
    $maskedTokens = 0
    $contentOmittedFiles = 0

    $utf8NoBom = [Text.UTF8Encoding]::new($false)
    $writer = [IO.StreamWriter]::new($outputFile, $false, $utf8NoBom)

    try {
        $writer.WriteLine('# Backup do Projeto')
        $writer.WriteLine()
        $writer.WriteLine("Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
        $writer.WriteLine("Raiz: $Root")
        $writer.WriteLine()

        foreach ($file in $allFiles) {
            try {
                $relativePath = Normalize-RelativePath -RootPath $Root -FilePath $file.FullName

                if (Should-IgnoreFile -RelativePath $relativePath -FileInfo $file) {
                    $skippedCount++
                    continue
                }

                $writer.WriteLine('---')
                $writer.WriteLine()
                $writer.WriteLine("## ``$relativePath``")
                $writer.WriteLine()

                $lang = Get-MarkdownLanguage -FilePath $file.FullName

                if (Should-IgnoreContent -RelativePath $relativePath) {
                    $placeholder = Get-OmittedContentPlaceholder -Language $lang
                    if ([string]::IsNullOrWhiteSpace($lang)) {
                        $writer.WriteLine('```')
                    } else {
                        $writer.WriteLine(('```' + $lang))
                    }
                    $writer.WriteLine($placeholder)
                    $writer.WriteLine('```')
                    $writer.WriteLine()
                    $contentOmittedFiles++
                    $processedCount++
                    continue
                }

                if (Is-CertificateFile -FilePath $file.FullName) {
                    $fence = '```'
                    $writer.WriteLine($fence)
                    $writer.WriteLine((Get-CertificateInfo -FilePath $file.FullName))
                    $writer.WriteLine($fence)
                    $writer.WriteLine()
                    $processedCount++
                    continue
                }

                if (Looks-Binary -FilePath $file.FullName) {
                    $writer.WriteLine('```')
                    $writer.WriteLine('[Arquivo binario - conteudo omitido]')
                    $writer.WriteLine('```')
                    $writer.WriteLine()
                    $processedCount++
                    continue
                }

                $fileBody = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
                if ([string]::IsNullOrWhiteSpace($fileBody)) {
                    $fileBody = '(arquivo vazio)'
                }

                $maskResult = Mask-Secrets -Text $fileBody
                $sanitizedBody = $maskResult.Text
                if ($maskResult.Count -gt 0) {
                    $maskedFiles++
                    $maskedTokens += $maskResult.Count
                }

                $fence = Get-CodeFence -Text $sanitizedBody
                if ([string]::IsNullOrWhiteSpace($lang)) {
                    $writer.WriteLine($fence)
                } else {
                    $writer.WriteLine("$fence$lang")
                }
                $writer.WriteLine($sanitizedBody)
                $writer.WriteLine($fence)
                $writer.WriteLine()

                $processedCount++
            } catch {
                Write-Warning "Erro ao processar '$($file.FullName)': $($_.Exception.Message)"
                $skippedCount++
            }
        }
    } finally {
        $writer.Dispose()
    }

    Write-Host "Backup v3 criado com sucesso: $outputFile" -ForegroundColor Green
    Write-Host "Arquivos processados: $processedCount" -ForegroundColor Cyan
    Write-Host "Arquivos ignorados: $skippedCount" -ForegroundColor Yellow
    Write-Host "Arquivos com conteudo omitido por regra: $contentOmittedFiles" -ForegroundColor DarkYellow
    Write-Host "Arquivos com mascara de segredo: $maskedFiles" -ForegroundColor Magenta
    Write-Host "Ocorrencias mascaradas: $maskedTokens" -ForegroundColor Magenta
}

try {
    Backup-ProjectAsMarkdownV3 -Root $PSScriptRoot
} catch {
    Write-Error "Erro durante o backup v3: $($_.Exception.Message)"
    exit 1
}
