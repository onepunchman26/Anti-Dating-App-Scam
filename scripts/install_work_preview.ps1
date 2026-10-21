# Fixed-release bootstrap. No Python/Git/Node, account binding or model calls.
# Read the publisher's release before running; do not change system execution policy.
[CmdletBinding()]
param([switch]$RegisterPlugin, [switch]$Launch)

$ErrorActionPreference = 'Stop'
$script:SMVersion = '0.8.5'
$script:SMRepository = 'onepunchman26/Anti-Dating-App-Scam'
$script:SMAsset = 'AI-SlowMatch-Work-0.8.5-windows-x64-controlled-preview.zip'
$script:SMAssetUrl = 'https://github.com/onepunchman26/Anti-Dating-App-Scam/releases/download/v0.8.5/AI-SlowMatch-Work-0.8.5-windows-x64-controlled-preview.zip'
# Final verified payload source: 2b42511c4743af33a143a8b1cb6217f89636de04.
$script:SMArchiveSha256 = 'd94aee709290c1b8a672da09eb481c87e4d91464291c90c9cdaf8afc8a17ec78'
$script:SMManifestSha256 = 'd9aed5f4e1ecfc03158c2a66830e4d2e1fe86a02feea030637c2d86c43773619'
$script:SMArchiveLimit = 300000000L
$script:SMFileLimit = 300000000L
$script:SMTotalLimit = 1000000000L
$script:SMEntryLimit = 4001

function Stop-SMBootstrap([string]$Code) { throw ('SMB:' + $Code) }

function Get-SMNativePath([string]$Path) {
    # Extended Win32 paths avoid legacy path limits; PS5.1 execution is policy-blocked
    # on the validation host, so PS5.1 compatibility is not claimed as tested.
    $plain = $Path.Replace('/', '\')
    if ($plain.StartsWith('\\?\')) { $plain = $plain.Substring(4) }
    if ($plain -notmatch '^[A-Za-z]:\\' -or $plain.Length -gt 32000) {
        Stop-SMBootstrap 'local_absolute_path_required'
    }
    if ($plain.Length -gt 3) {
        $plain = $plain.TrimEnd('\')
        foreach ($part in $plain.Substring(3).Split('\')) {
            if ($part -in @('', '.', '..') -or $part.EndsWith('.') -or $part.EndsWith(' ')) {
                Stop-SMBootstrap 'ambiguous_local_path'
            }
        }
    }
    return '\\?\' + $plain
}

function Test-SMPath([string]$Path) {
    $native = Get-SMNativePath $Path
    return [IO.File]::Exists($native) -or [IO.Directory]::Exists($native)
}

function Get-SMSha256([string]$Path) {
    $stream = [IO.File]::OpenRead((Get-SMNativePath $Path))
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $sha.Dispose() }
}

function Assert-SMAncestors([string]$Path) {
    $cursor = (Get-SMNativePath $Path).Substring(4)
    if ($cursor -match '(?i)(^|[\\/])OneDrive(?:[^\\/]*)?([\\/]|$)') {
        Stop-SMBootstrap 'nonsynced_local_storage_required'
    }
    while ($cursor) {
        $attributes = $null
        try { $attributes = [IO.File]::GetAttributes((Get-SMNativePath $cursor)) }
        catch [IO.FileNotFoundException] { }
        catch [IO.DirectoryNotFoundException] { }
        if ($null -ne $attributes) {
            if (($attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                Stop-SMBootstrap 'redirected_path_rejected'
            }
            if (($attributes -band [IO.FileAttributes]::Directory) -ne 0 -and
                (Test-SMPath ($cursor.TrimEnd('\') + '\.git'))) {
                Stop-SMBootstrap 'source_storage_rejected'
            }
        }
        if ($cursor.Length -le 3) { break }
        $last = $cursor.LastIndexOf('\')
        $cursor = if ($last -le 2) { $cursor.Substring(0, 3) } else { $cursor.Substring(0, $last) }
    }
}

function Assert-SMRelativeName([string]$Name) {
    if ([string]::IsNullOrEmpty($Name) -or $Name.Length -gt 240 -or
        $Name -match '[\\:\x00-\x1f<>"|?*]' -or $Name.StartsWith('/') -or
        $Name -cne $Name.Normalize([Text.NormalizationForm]::FormC)) {
        Stop-SMBootstrap 'unsafe_archive_path'
    }
    foreach ($part in $Name.Split('/')) {
        if ($part -in @('', '.', '..') -or $part.EndsWith('.') -or $part.EndsWith(' ') -or
            $part -match '^(?i:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)') {
            Stop-SMBootstrap 'unsafe_archive_path'
        }
    }
}

function Assert-SMArchive([string]$Archive, [string]$ExpectedHash) {
    Assert-SMAncestors $Archive
    $file = [IO.FileInfo]::new((Get-SMNativePath $Archive))
    if (-not $file.Exists -or $file.Length -le 0 -or $file.Length -gt $script:SMArchiveLimit -or
        $ExpectedHash -cnotmatch '^[0-9a-f]{64}$' -or (Get-SMSha256 $Archive) -cne $ExpectedHash) {
        Stop-SMBootstrap 'archive_integrity_failed'
    }
}

function Test-SMVerifiedCache([string]$Path, [string]$ExpectedHash) {
    if (-not (Test-SMPath $Path)) { return $false }
    Assert-SMAncestors $Path
    if (-not [IO.File]::Exists((Get-SMNativePath $Path))) { Stop-SMBootstrap 'cached_path_not_file' }
    try { Assert-SMArchive $Path $ExpectedHash; return $true }
    catch {
        if ($_.Exception.Message -ceq 'SMB:archive_integrity_failed') { return $false }
        throw
    }
}

function Read-SMBoundedEntry($Entry, [long]$Limit) {
    if ($Entry.Length -lt 0 -or $Entry.Length -gt $Limit) { Stop-SMBootstrap 'archive_limit' }
    $inputStream = $Entry.Open()
    $memory = [IO.MemoryStream]::new()
    try {
        $buffer = [byte[]]::new(65536)
        $count = 0L
        while (($read = $inputStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
            $count += $read
            if ($count -gt $Limit -or $count -gt $Entry.Length) { Stop-SMBootstrap 'archive_limit' }
            $memory.Write($buffer, 0, $read)
        }
        if ($count -ne $Entry.Length) { Stop-SMBootstrap 'archive_size_mismatch' }
        return ,$memory.ToArray()
    } finally { $inputStream.Dispose(); $memory.Dispose() }
}

function Expand-SMVerifiedArchive([string]$Archive, [string]$Destination,
        [string]$ExpectedArchiveHash, [string]$ExpectedManifestHash) {
    Assert-SMArchive $Archive $ExpectedArchiveHash
    Assert-SMAncestors $Destination
    if (Test-SMPath $Destination) { Stop-SMBootstrap 'fresh_staging_required' }
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead((Get-SMNativePath $Archive))
    try {
        if ($zip.Entries.Count -lt 2 -or $zip.Entries.Count -gt $script:SMEntryLimit) {
            Stop-SMBootstrap 'archive_limit'
        }
        $entries = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
        $folded = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        $total = 0L
        foreach ($entry in $zip.Entries) {
            $name = $entry.FullName
            Assert-SMRelativeName $name
            if (-not $folded.Add($name)) { Stop-SMBootstrap 'archive_path_collision' }
            $mode = ($entry.ExternalAttributes -shr 16) -band 0xF000
            if ($mode -notin @(0, 0x8000) -or ($entry.ExternalAttributes -band 0x410) -ne 0) {
                Stop-SMBootstrap 'archive_special_file_rejected'
            }
            if ($entry.Length -lt 0 -or $entry.Length -gt $script:SMFileLimit -or
                ($entry.Length -gt 1000000 -and $entry.Length -gt (500 * [Math]::Max(1L, $entry.CompressedLength)))) {
                Stop-SMBootstrap 'archive_limit'
            }
            $total += $entry.Length
            if ($total -gt $script:SMTotalLimit) { Stop-SMBootstrap 'archive_limit' }
            $entries.Add($name, $entry)
        }
        # File/directory prefix collisions are rejected before creating any file.
        foreach ($name in $entries.Keys) {
            $parts = $name.Split('/')
            for ($i = 1; $i -lt $parts.Length; $i++) {
                if ($folded.Contains(($parts[0..($i - 1)] -join '/'))) {
                    Stop-SMBootstrap 'archive_path_collision'
                }
            }
        }
        if (-not $entries.ContainsKey('work-release.json')) { Stop-SMBootstrap 'manifest_missing' }
        $manifestBytes = Read-SMBoundedEntry $entries['work-release.json'] 2000000
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $manifestHash = ([BitConverter]::ToString($sha.ComputeHash($manifestBytes))).Replace('-', '').ToLowerInvariant() }
        finally { $sha.Dispose() }
        if ($ExpectedManifestHash -cnotmatch '^[0-9a-f]{64}$' -or $manifestHash -cne $ExpectedManifestHash) {
            Stop-SMBootstrap 'manifest_integrity_failed'
        }
        $manifest = [Text.UTF8Encoding]::new($false, $true).GetString($manifestBytes) | ConvertFrom-Json
        if ($manifest.schema_version -ne 1 -or $manifest.version -cne $script:SMVersion -or
            $manifest.repository -cne $script:SMRepository -or $manifest.product -cne 'AI-SlowMatch' -or
            $manifest.channel -cne 'controlled-preview' -or $manifest.platform -cne 'windows-x64' -or
            $manifest.entrypoint -cne 'SlowMatch-Work.exe' -or $manifest.data_schema -ne 1 -or
            $manifest.source_commit -cnotmatch '^[0-9a-f]{40}$' -or
            $manifest.source_digest -cnotmatch '^[0-9a-f]{64}$' -or
            $manifest.source_dirty -isnot [bool] -or $manifest.source_dirty -or
            $manifest.service_origin -cne 'https://slowmatch-private-pilot.fizzydeer7.chatgpt.site' -or
            $manifest.files -isnot [Management.Automation.PSCustomObject]) {
            Stop-SMBootstrap 'release_identity_mismatch'
        }
        $files = @($manifest.files.PSObject.Properties)
        if ($files.Count + 1 -ne $entries.Count -or
            -not $entries.ContainsKey('SlowMatch-Work.exe')) { Stop-SMBootstrap 'manifest_entries_mismatch' }
        $allowlist = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
        foreach ($file in $files) {
            Assert-SMRelativeName $file.Name
            if ($file.Name -ieq 'work-release.json' -or -not $entries.ContainsKey($file.Name) -or
                $file.Value.sha256 -cnotmatch '^[0-9a-f]{64}$' -or
                $file.Value.size -ne $entries[$file.Name].Length -or
                ($file.Value.size -isnot [int] -and $file.Value.size -isnot [long])) {
                Stop-SMBootstrap 'manifest_entries_mismatch'
            }
            $allowlist.Add($file.Name, $file.Value)
        }
        $root = (Get-SMNativePath $Destination).Substring(4)
        [IO.Directory]::CreateDirectory((Get-SMNativePath $root)) | Out-Null
        Assert-SMAncestors $root
        foreach ($name in $entries.Keys) {
            $target = $root + '\' + $name.Replace('/', '\')
            if (-not $target.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
                Stop-SMBootstrap 'unsafe_archive_path'
            }
            [IO.Directory]::CreateDirectory((Get-SMNativePath ($target.Substring(0, $target.LastIndexOf('\'))))) | Out-Null
            Assert-SMAncestors $target
            $entry = $entries[$name]
            $inputStream = $entry.Open()
            $outputStream = [IO.File]::Open((Get-SMNativePath $target), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
            try {
                $buffer = [byte[]]::new(65536)
                $count = 0L
                while (($read = $inputStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
                    $count += $read
                    if ($count -gt $entry.Length -or $count -gt $script:SMFileLimit) { Stop-SMBootstrap 'archive_limit' }
                    $outputStream.Write($buffer, 0, $read)
                }
                if ($count -ne $entry.Length) { Stop-SMBootstrap 'archive_size_mismatch' }
                $outputStream.Flush()
            } finally { $inputStream.Dispose(); $outputStream.Dispose() }
            $expected = if ($name -ceq 'work-release.json') { $ExpectedManifestHash } else { $allowlist[$name].sha256 }
            if ((Get-SMSha256 $target) -cne $expected) { Stop-SMBootstrap 'component_integrity_failed' }
        }
        return $root
    } finally { $zip.Dispose() }
}

function Assert-SMDownloadUri([Uri]$Uri) {
    if ($Uri.Scheme -cne 'https' -or $Uri.Port -ne 443 -or $Uri.UserInfo -or
        $Uri.Host -notin @('github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com')) {
        Stop-SMBootstrap 'download_redirect_rejected'
    }
}

function Receive-SMPinnedArchive([string]$Destination) {
    Add-Type -AssemblyName System.Net.Http
    $handler = [Net.Http.HttpClientHandler]::new()
    $handler.AllowAutoRedirect = $false
    $handler.UseDefaultCredentials = $false
    $client = [Net.Http.HttpClient]::new($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(180)
    $client.DefaultRequestHeaders.UserAgent.ParseAdd('AI-SlowMatch-Installer/0.8.5')
    $cancel = [Threading.CancellationTokenSource]::new(180000)
    $response = $null
    try {
        $uri = [Uri]$script:SMAssetUrl
        for ($hop = 0; $hop -le 5; $hop++) {
            Assert-SMDownloadUri $uri
            $response = $client.GetAsync($uri, [Net.Http.HttpCompletionOption]::ResponseHeadersRead, $cancel.Token).GetAwaiter().GetResult()
            if ([int]$response.StatusCode -in @(301, 302, 303, 307, 308)) {
                if ($hop -eq 5 -or $null -eq $response.Headers.Location) { Stop-SMBootstrap 'download_redirect_rejected' }
                $uri = [Uri]::new($uri, $response.Headers.Location)
                $response.Dispose(); $response = $null
                continue
            }
            if ([int]$response.StatusCode -ne 200) { Stop-SMBootstrap 'release_download_unavailable' }
            $declared = $response.Content.Headers.ContentLength
            if ($null -ne $declared -and ($declared -le 0 -or $declared -gt $script:SMArchiveLimit)) { Stop-SMBootstrap 'download_limit' }
            $inputStream = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
            $outputStream = [IO.File]::Open((Get-SMNativePath $Destination), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
            try {
                $buffer = [byte[]]::new(65536)
                $count = 0L
                while (($read = $inputStream.ReadAsync($buffer, 0, $buffer.Length, $cancel.Token).GetAwaiter().GetResult()) -gt 0) {
                    $count += $read
                    if ($count -gt $script:SMArchiveLimit) { Stop-SMBootstrap 'download_limit' }
                    $outputStream.Write($buffer, 0, $read)
                }
                if ($count -le 0 -or ($null -ne $declared -and $count -ne $declared)) { Stop-SMBootstrap 'download_size_mismatch' }
            } finally { $inputStream.Dispose(); $outputStream.Dispose() }
            return
        }
    } finally {
        if ($null -ne $response) { $response.Dispose() }
        $cancel.Dispose(); $client.Dispose(); $handler.Dispose()
    }
}

function Invoke-SMRuntime([string]$Executable, [string]$Arguments) {
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = Get-SMNativePath $Executable
    $start.Arguments = $Arguments
    $start.WorkingDirectory = Get-SMNativePath ($Executable.Substring(0, $Executable.LastIndexOf('\')))
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardInput = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $start
    try {
        if (-not $process.Start()) { Stop-SMBootstrap 'runtime_launch_failed' }
        $process.StandardInput.Close()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(180000)) { $process.Kill(); Stop-SMBootstrap 'runtime_timeout' }
        $raw = $stdout.GetAwaiter().GetResult()
        $stderr.GetAwaiter().GetResult() | Out-Null
        if ($raw.Length -gt 16000) { Stop-SMBootstrap 'runtime_output_invalid' }
        $result = $raw | ConvertFrom-Json
        if ($process.ExitCode -ne 0 -or $result.ok -ne $true) {
            if ($result.error.code -cmatch '^[a-z0-9_]{1,64}$') { Stop-SMBootstrap ('native_' + $result.error.code) }
            Stop-SMBootstrap 'runtime_check_failed'
        }
        return $result
    } finally { $process.Dispose() }
}

function Invoke-SMPreviewInstall([bool]$InstallPlugin = $false) {
    $timer = [Diagnostics.Stopwatch]::StartNew()
    try {
        if ($script:SMArchiveSha256 -cnotmatch '^[0-9a-f]{64}$' -or $script:SMManifestSha256 -cnotmatch '^[0-9a-f]{64}$') {
            Stop-SMBootstrap 'release_not_ready'
        }
        if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT -or
            -not [Environment]::Is64BitOperatingSystem -or
            $env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') {
            Stop-SMBootstrap 'windows_x64_required'
        }
        if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA) -or -not [IO.Path]::IsPathRooted($env:LOCALAPPDATA)) {
            Stop-SMBootstrap 'local_application_storage_unavailable'
        }
        $base = (Get-SMNativePath ($env:LOCALAPPDATA.TrimEnd('\') + '\AI-SlowMatch\downloads')).Substring(4)
        Assert-SMAncestors $base
        [IO.Directory]::CreateDirectory((Get-SMNativePath $base)) | Out-Null
        Assert-SMAncestors $base
        $stage = $base + '\b-' + [Guid]::NewGuid().ToString('N')
        if (Test-SMPath $stage) { Stop-SMBootstrap 'fresh_staging_required' }
        [IO.Directory]::CreateDirectory((Get-SMNativePath $stage)) | Out-Null
        Assert-SMAncestors $stage
        $cache = Join-Path $base ('package-' + $script:SMArchiveSha256 + '.zip')
        $download = 'verified_cache'
        if (Test-SMVerifiedCache $cache $script:SMArchiveSha256) {
            $archive = $cache
        } else {
            $archive = Join-Path $stage $script:SMAsset
            Receive-SMPinnedArchive $archive
            Assert-SMArchive $archive $script:SMArchiveSha256
            # Cache is optional. Preserve an invalid existing public cache and use the new
            # verified stage instead; a partial cache must never make reinstall impossible.
            if (-not (Test-SMPath $cache)) {
                try { [IO.File]::Copy((Get-SMNativePath $archive), (Get-SMNativePath $cache), $false) }
                catch [IO.IOException] { } # Another installer may have created it; use our stage.
            }
            $download = 'downloaded_and_verified'
        }
        $package = Expand-SMVerifiedArchive $archive ($stage + '\p') $script:SMArchiveSha256 $script:SMManifestSha256
        $executable = Join-Path $package 'SlowMatch-Work.exe'
        # Windows filenames cannot contain quotes; only this checked local path is quoted.
        $installed = Invoke-SMRuntime $executable ('install --package "' + $package + '" --expected-manifest-sha256 ' + $script:SMManifestSha256)
        $doctor = Invoke-SMRuntime $executable 'doctor'
        if ($installed.version -cne $script:SMVersion -or $doctor.version -cne $script:SMVersion) {
            Stop-SMBootstrap 'runtime_version_mismatch'
        }
        $registration = 'not_requested'
        if ($InstallPlugin) { Invoke-SMRuntime $executable 'register-plugin' | Out-Null; $registration = 'installer_completed' }
        $assistant = 'not_requested'
        if ($Launch) {
            $activePath = Join-Path $env:LOCALAPPDATA 'AI-SlowMatch\portable\active.json'
            Assert-SMAncestors $activePath
            $active = [IO.File]::ReadAllText((Get-SMNativePath $activePath)) | ConvertFrom-Json
            if ($active.release -cnotmatch '^0\.8\.4-[a-f0-9]{12}(?:-repair-[a-f0-9]{8})?$') { Stop-SMBootstrap 'invalid_active_release' }
            $installedExe = Join-Path $env:LOCALAPPDATA ('AI-SlowMatch\portable\releases\' + $active.release + '\SlowMatch-Work.exe')
            Assert-SMAncestors $installedExe
            $started = Invoke-SMRuntime $installedExe 'launch'
            $assistant = $started.assistant
        }
        return @{ok=$true; version=$script:SMVersion; channel='controlled-preview'; download=$download;
            program_check='passed'; plugin_registration=$registration; account_binding='not_requested'; local_assistant=$assistant;
            native_chatgpt='not_checked'; remote_identity='not_checked'; two_accounts='not_checked';
            public_staging='retained_for_repair'; elapsed_ms=$timer.ElapsedMilliseconds; model_calls=0}
    } catch {
        $code = 'bootstrap_failed'
        if ($_.Exception.Message -cmatch '^SMB:([a-z0-9_]{1,80})$') { $code = $Matches[1] }
        return @{ok=$false; version=$script:SMVersion; channel='controlled-preview'; error=$code;
            elapsed_ms=$timer.ElapsedMilliseconds; model_calls=0; next='consult_release_help_for_this_error'}
    } finally { $timer.Stop() }
}

# Dot-sourcing exposes deterministic validation helpers only, for offline maintainer tests.
if ($MyInvocation.InvocationName -ne '.') {
    $result = Invoke-SMPreviewInstall -InstallPlugin ([bool]$RegisterPlugin)
    $result | ConvertTo-Json -Depth 4 -Compress
    if (-not $result.ok) { exit 1 }
}
