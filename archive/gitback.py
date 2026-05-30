<#
.SYNOPSIS
    Git Backdate Tool - Make commits appear at different dates
.DESCRIPTION
    A PowerShell tool for backdating git commits with stealth features,
    time manipulation, and profile management.
.VERSION
    2.1
#>

param(
    [Parameter(Position=0)]
    [string]$Command = "",
    
    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Args = @()
)

# Configuration paths
$Script:ConfigDir = Join-Path $env:USERPROFILE ".git-backdate"
$Script:ConfigFile = Join-Path $Script:ConfigDir "config"
$Script:ProfilesDir = Join-Path $Script:ConfigDir "profiles"
$Script:TemplatesDir = Join-Path $Script:ConfigDir "templates"

# Colors for PowerShell
function Write-ColorOutput($Color, $Text) {
    Write-Host $Text -ForegroundColor $Color
}

function Print-Header($Text) {
    Write-ColorOutput "Cyan" "`n═══════════════════════════════════════════════════════════"
    Write-ColorOutput "Cyan" "  $Text"
    Write-ColorOutput "Cyan" "═══════════════════════════════════════════════════════════"
}

function Print-Success($Text) { Write-ColorOutput "Green" "✓ $Text" }
function Print-Error($Text) { Write-ColorOutput "Red" "✗ $Text" }
function Print-Warning($Text) { Write-ColorOutput "Yellow" "⚠ $Text" }
function Print-Info($Text) { Write-ColorOutput "Blue" "ℹ $Text" }

# Initialize configuration
function Init-Config {
    if (-not (Test-Path $Script:ConfigDir)) {
        New-Item -ItemType Directory -Path $Script:ConfigDir -Force | Out-Null
        New-Item -ItemType Directory -Path $Script:ProfilesDir -Force | Out-Null
        New-Item -ItemType Directory -Path $Script:TemplatesDir -Force | Out-Null
        
        # Default config
        $defaultConfig = @"
# Git Backdate Configuration
# Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

INITIAL_DATE=
CURRENT_OFFSET=0
DEFAULT_TIME=09:00
PROFILE=default
"@
        Set-Content -Path $Script:ConfigFile -Value $defaultConfig
        Print-Success "Configuration initialized at $Script:ConfigDir"
    }
}

# Read config value
function Get-ConfigValue($Key) {
    if (Test-Path $Script:ConfigFile) {
        $content = Get-Content $Script:ConfigFile
        foreach ($line in $content) {
            if ($line -match "^$Key=(.*)$") {
                return $Matches[1].Trim()
            }
        }
    }
    return $null
}

# Set config value
function Set-ConfigValue($Key, $Value) {
    Init-Config
    $content = Get-Content $Script:ConfigFile -ErrorAction SilentlyContinue
    $found = $false
    $newContent = @()
    
    foreach ($line in $content) {
        if ($line -match "^$Key=") {
            $newContent += "$Key=$Value"
            $found = $true
        } else {
            $newContent += $line
        }
    }
    
    if (-not $found) {
        $newContent += "$Key=$Value"
    }
    
    Set-Content -Path $Script:ConfigFile -Value $newContent
}

# Calculate date from offset
function Get-DateFromOffset {
    param(
        [int]$DayOffset = 0,
        [string]$TimeSpec = "",
        [int]$JitterMinutes = 0
    )
    
    $initialDateStr = Get-ConfigValue "INITIAL_DATE"
    
    if (-not $initialDateStr) {
        Print-Error "No initial date set. Run: gbd init <YYYY-MM-DD>"
        return $null
    }
    
    try {
        $initialDate = [DateTime]::Parse($initialDateStr)
    } catch {
        Print-Error "Invalid initial date: $initialDateStr"
        return $null
    }
    
    # Calculate target date
    $targetDate = $initialDate.AddDays($DayOffset)
    
    # Handle time specification
    if ($TimeSpec -and $TimeSpec -match "^(\d{1,2}):(\d{2})(?::(\d{2}))?$") {
        $hours = [int]$Matches[1]
        $minutes = [int]$Matches[2]
        $seconds = if ($Matches[3]) { [int]$Matches[3] } else { 0 }
        $targetDate = $targetDate.AddHours($hours).AddMinutes($minutes).AddSeconds($seconds)
    } else {
        # Use default time
        $defaultTime = Get-ConfigValue "DEFAULT_TIME"
        if ($defaultTime -and $defaultTime -match "^(\d{1,2}):(\d{2})$") {
            $hours = [int]$Matches[1]
            $minutes = [int]$Matches[2]
            $targetDate = $targetDate.AddHours($hours).AddMinutes($minutes)
        } else {
            $targetDate = $targetDate.AddHours(9)  # Default 9 AM
        }
    }
    
    # Add jitter if specified
    if ($JitterMinutes -gt 0) {
        $jitter = Get-Random -Minimum (-$JitterMinutes) -Maximum $JitterMinutes
        $targetDate = $targetDate.AddMinutes($jitter)
    }
    
    return $targetDate
}

# Format date for git
function Format-GitDate($Date) {
    return $Date.ToString("ddd MMM dd HH:mm:ss yyyy zzz")
}

# Initialize with date
function Invoke-Init {
    param([string]$DateStr)
    
    if (-not $DateStr) {
        Print-Error "Usage: gbd init <YYYY-MM-DD>"
        Print-Info "Example: gbd init 2023-03-15"
        return
    }
    
    try {
        $date = [DateTime]::Parse($DateStr)
        $formattedDate = $date.ToString("yyyy-MM-dd")
        
        Init-Config
        Set-ConfigValue "INITIAL_DATE" $formattedDate
        Set-ConfigValue "CURRENT_OFFSET" "0"
        
        Print-Success "Initial date set to: $formattedDate"
        Print-Info "Use 'gbd commit <days> <message>' to commit with offset"
    } catch {
        Print-Error "Invalid date format: $DateStr"
        Print-Info "Use format: YYYY-MM-DD (e.g., 2023-03-15)"
    }
}

# Do the actual commit
function Invoke-Commit {
    param(
        [int]$DayOffset = 0,
        [string]$Message = "",
        [string]$TimeSpec = "",
        [int]$JitterMinutes = 0,
        [switch]$Preview,
        [string]$Template = ""
    )
    
    # Check for staged changes
    $staged = git diff --cached --quiet 2>$null
    if ($LASTEXITCODE -eq 0) {
        Print-Warning "No staged changes. Use 'git add' first."
        return
    }
    
    # Calculate target date
    $targetDate = Get-DateFromOffset -DayOffset $DayOffset -TimeSpec $TimeSpec -JitterMinutes $JitterMinutes
    if (-not $targetDate) { return }
    
    $gitDate = Format-GitDate $targetDate
    
    # Use template if specified
    if ($Template -and [string]::IsNullOrEmpty($Message)) {
        $templateFile = Join-Path $Script:TemplatesDir "$Template.txt"
        if (Test-Path $templateFile) {
            $Message = Get-Content $templateFile -Raw
        } else {
            Print-Warning "Template not found: $Template"
        }
    }
    
    # Default message
    if ([string]::IsNullOrEmpty($Message)) {
        $Message = "Update"
    }
    
    if ($Preview) {
        Print-Info "Preview mode - no changes made"
        Write-Host ""
        Write-Host "  Date:   $($targetDate.ToString('yyyy-MM-dd HH:mm:ss'))"
        Write-Host "  Offset: $DayOffset days from initial date"
        Write-Host "  Message: $Message"
        Write-Host ""
        Write-Host "  Git command:"
        Write-Host "  GIT_AUTHOR_DATE=`"$gitDate`" GIT_COMMITTER_DATE=`"$gitDate`" git commit -m `"$Message`""
        return
    }
    
    # Perform the commit
    $env:GIT_AUTHOR_DATE = $gitDate
    $env:GIT_COMMITTER_DATE = $gitDate
    
    git commit -m $Message
    
    if ($LASTEXITCODE -eq 0) {
        Print-Success "Committed with date: $($targetDate.ToString('yyyy-MM-dd HH:mm:ss'))"
        
        # Update offset for next commit
        $currentOffset = [int](Get-ConfigValue "CURRENT_OFFSET")
        Set-ConfigValue "CURRENT_OFFSET" ($currentOffset + 1)
    }
    
    Remove-Item Env:GIT_AUTHOR_DATE -ErrorAction SilentlyContinue
    Remove-Item Env:GIT_COMMITTER_DATE -ErrorAction SilentlyContinue
}

# Show status
function Show-Status {
    $initialDate = Get-ConfigValue "INITIAL_DATE"
    $currentOffset = Get-ConfigValue "CURRENT_OFFSET"
    $defaultTime = Get-ConfigValue "DEFAULT_TIME"
    $profile = Get-ConfigValue "PROFILE"
    
    Print-Header "Backdate Status"
    
    if ($initialDate) {
        Write-Host "  Initial Date:  $initialDate"
        Write-Host "  Next Offset:   $currentOffset days"
        
        # Calculate next commit date
        $nextDate = Get-DateFromOffset -DayOffset ([int]$currentOffset)
        if ($nextDate) {
            Write-Host "  Next Commit:   $($nextDate.ToString('yyyy-MM-dd HH:mm:ss'))"
        }
    } else {
        Write-Host "  Initial Date:  Not set"
    }
    
    Write-Host "  Default Time:  $defaultTime"
    Write-Host "  Active Profile: $profile"
    Write-Host ""
}

# Reset configuration
function Invoke-Reset {
    param([string]$What)
    
    switch ($What) {
        "offset" {
            Set-ConfigValue "CURRENT_OFFSET" "0"
            Print-Success "Offset reset to 0"
        }
        "date" {
            Set-ConfigValue "INITIAL_DATE" ""
            Set-ConfigValue "CURRENT_OFFSET" "0"
            Print-Success "Initial date cleared"
        }
        "all" {
            if (Test-Path $Script:ConfigDir) {
                Remove-Item -Path $Script:ConfigDir -Recurse -Force
            }
            Print-Success "All configuration deleted"
        }
        default {
            Print-Info "Usage: gbd reset <option>"
            Write-Host "  offset  - Reset day offset to 0"
            Write-Host "  date    - Clear initial date"
            Write-Host "  all     - Delete all configuration"
        }
    }
}

# Show commit log with dates
function Show-Log {
    param([int]$Count = 10)
    
    Print-Header "Backdate Log (Last $Count commits)"
    
    git log --pretty=format:"%h | %ad | %s" --date=format:"%Y-%m-%d %H:%M" -n $Count
    
    Write-Host ""
}

# Show calendar view
function Show-Calendar {
    param([int]$Month = 0, [int]$Year = 0)
    
    $initialDateStr = Get-ConfigValue "INITIAL_DATE"
    if (-not $initialDateStr) {
        Print-Error "No initial date set"
        return
    }
    
    $initialDate = [DateTime]::Parse($initialDateStr)
    
    if ($Year -eq 0) { $Year = $initialDate.Year }
    if ($Month -eq 0) { $Month = $initialDate.Month }
    
    $firstDay = [DateTime]::new($Year, $Month, 1)
    $daysInMonth = [DateTime]::DaysInMonth($Year, $Month)
    
    # Get commits for this month
    $commits = @()
    $startDate = $firstDay.ToString("yyyy-MM-dd")
    $endDate = $firstDay.AddDays($daysInMonth - 1).ToString("yyyy-MM-dd")
    
    $logOutput = git log --since="$startDate" --until="$endDate 23:59:59" --pretty=format:"%ad" --date=format:"%Y-%m-%d" 2>$null
    
    foreach ($line in $logOutput) {
        if ($line -and $line -match "^\d{4}-\d{2}-\d{2}$") {
            $commits += $line
        }
    }
    
    Print-Header "Calendar - $Year-$Month"
    
    # Day headers
    Write-Host "  Su  Mo  Tu  We  Th  Fr  Sa"
    Write-Host "  ---------------------------"
    
    # Leading spaces
    $startDayOfWeek = [int]$firstDay.DayOfWeek
    $line = "  "
    for ($i = 0; $i -lt $startDayOfWeek; $i++) {
        $line += "    "
    }
    
    # Days
    for ($day = 1; $day -le $daysInMonth; $day++) {
        $dateStr = "{0:D4}-{1:D2}-{2:D2}" -f $Year, $Month, $day
        $hasCommit = $commits -contains $dateStr
        
        if ($hasCommit) {
            $line += "[$day]".PadLeft(3).PadRight(4)
        } else {
            $line += " $day ".PadLeft(3).PadRight(4)
        }
        
        if ((($startDayOfWeek + $day) % 7) -eq 0) {
            Write-Host $line
            $line = "  "
        }
    }
    
    if ($line.Trim() -ne "") {
        Write-Host $line
    }
    
    Write-Host ""
    Write-Host "  [N] = Commit exists"
    Write-Host ""
}

# Stealth check
function Invoke-StealthCheck {
    param([switch]$Quick)
    
    Print-Header "Stealth Analysis"
    
    $issues = @()
    $score = 100
    
    # Get recent commits
    $commits = git log --pretty=format:"%H|%ad|%s" --date=iso -n 100 2>$null
    
    $commitList = @()
    foreach ($line in $commits) {
        $parts = $line -split "\|"
        if ($parts.Count -ge 3) {
            $commitList += @{
                Hash = $parts[0]
                Date = $parts[1]
                Message = $parts[2]
            }
        }
    }
    
    if ($commitList.Count -eq 0) {
        Print-Warning "No commits found"
        return
    }
    
    # Check 1: Identical timestamps
    $timestamps = @{}
    foreach ($c in $commitList) {
        $time = $c.Date.Substring(0, 16)  # Group by minute
        if ($timestamps.ContainsKey($time)) {
            $timestamps[$time]++
        } else {
            $timestamps[$time] = 1
        }
    }
    
    $identicalCount = ($timestamps.Values | Where-Object { $_ -gt 1 }).Count
    if ($identicalCount -gt 0) {
        $issues += "Found $identicalCount timestamps with multiple commits"
        $score -= 15
    }
    
    # Check 2: Late night commits
    $lateNight = 0
    foreach ($c in $commitList) {
        $hour = [int]($c.Date.Substring(11, 2))
        if ($hour -ge 0 -and $hour -lt 6) {
            $lateNight++
        }
    }
    if ($lateNight -gt ($commitList.Count * 0.3)) {
        $issues += "High late-night commit ratio: $lateNight commits between midnight-6am"
        $score -= 10
    }
    
    # Check 3: Weekend commits
    $weekendCommits = 0
    foreach ($c in $commitList) {
        try {
            $date = [DateTime]::Parse($c.Date)
            if ($date.DayOfWeek -in @("Saturday", "Sunday")) {
                $weekendCommits++
            }
        } catch {}
    }
    if ($weekendCommits -gt ($commitList.Count * 0.4)) {
        $issues += "High weekend commit ratio: $weekendCommits commits on weekends"
        $score -= 10
    }
    
    # Check 4: Round times
    $roundTimes = 0
    foreach ($c in $commitList) {
        if ($c.Date -match ":00:00$") {
            $roundTimes++
        }
    }
    if ($roundTimes -gt ($commitList.Count * 0.5)) {
        $issues += "Many round timestamps: $roundTimes commits at exact hours"
        $score -= 15
    }
    
    # Check 5: Time gaps
    $dates = @($commitList | ForEach-Object { 
        try { [DateTime]::Parse($_.Date) } catch {} 
    } | Sort-Object)
    
    $gaps = @()
    for ($i = 1; $i -lt $dates.Count; $i++) {
        $gap = ($dates[$i-1] - $dates[$i]).Days
        if ($gap -gt 7) {
            $gaps += $gap
        }
    }
    
    if ($gaps.Count -gt 0) {
        $issues += "Found $($gaps.Count) gaps larger than 7 days"
        $score -= 5
    }
    
    # Print results
    Write-Host ""
    Write-Host "  Stealth Score: $score/100"
    
    if ($score -ge 80) {
        Write-ColorOutput "Green" "  Rating: GOOD - Low detection risk"
    } elseif ($score -ge 60) {
        Write-ColorOutput "Yellow" "  Rating: FAIR - Some suspicious patterns"
    } else {
        Write-ColorOutput "Red" "  Rating: POOR - High detection risk"
    }
    
    Write-Host ""
    
    if ($issues.Count -gt 0) {
        Write-Host "  Issues found:"
        foreach ($issue in $issues) {
            Write-Host "    - $issue"
        }
    } else {
        Print-Success "No suspicious patterns detected"
    }
    
    Write-Host ""
}

# Doctor - fix issues
function Invoke-Doctor {
    Print-Header "Doctor - Analysis & Suggestions"
    
    # Check git installation
    try {
        $gitVersion = git --version
        Print-Success "Git installed: $gitVersion"
    } catch {
        Print-Error "Git not found in PATH"
    }
    
    # Check configuration
    $initialDate = Get-ConfigValue "INITIAL_DATE"
    if ($initialDate) {
        Print-Success "Initial date configured: $initialDate"
    } else {
        Print-Warning "No initial date set - run: gbd init <YYYY-MM-DD>"
    }
    
    # Check for staged changes
    $staged = git diff --cached --name-only 2>$null
    if ($staged) {
        Print-Info "Staged files ready for commit: $($staged.Count)"
    }
    
    Write-Host ""
    Write-Host "  Suggestions:"
    
    # Run stealth check
    $lateNight = 0
    $commits = git log --pretty=format:"%ad" --date=iso -n 50 2>$null
    foreach ($line in $commits) {
        if ($line -match " (\d{2}):") {
            $hour = [int]$Matches[1]
            if ($hour -ge 0 -and $hour -lt 6) {
                $lateNight++
            }
        }
    }
    
    if ($lateNight -gt 10) {
        Write-Host "    - Consider using time jitter to vary commit times"
        Write-Host "      Example: gbd commit 1 'message' --jitter 30"
    }
    
    Write-Host "    - Use --preview flag before committing to verify dates"
    Write-Host "    - Run 'gbd stealth' periodically to check patterns"
    Write-Host ""
}

# Push helper
function Invoke-PushHelper {
    param([string]$Remote = "origin", [string]$Branch = "")
    
    if ([string]::IsNullOrEmpty($Branch)) {
        $Branch = git rev-parse --abbrev-ref HEAD 2>$null
        if ([string]::IsNullOrEmpty($Branch)) {
            $Branch = "main"
        }
    }
    
    Print-Header "Push Helper"
    
    # Show commits to be pushed
    Write-Host "  Remote: $Remote"
    Write-Host "  Branch: $Branch"
    Write-Host ""
    
    $unpushed = git log "$Remote/$Branch..HEAD" --oneline 2>$null
    
    if ($unpushed) {
        Write-Host "  Commits to push:"
        foreach ($line in $unpushed) {
            Write-Host "    $line"
        }
        Write-Host ""
        
        Write-Host "  Press Y to push, any other key to cancel..."
        $key = $Host.UI.RawUI.ReadKey("IncludeKeyDown,NoEcho")
        
        if ($key.Character -eq 'y' -or $key.Character -eq 'Y') {
            git push $Remote $Branch
            if ($LASTEXITCODE -eq 0) {
                Print-Success "Pushed successfully"
            }
        } else {
            Print-Info "Push cancelled"
        }
    } else {
        Print-Info "No commits to push"
    }
    
    Write-Host ""
}

# Profile management
function Manage-Profiles {
    param(
        [string]$Action,
        [string]$Name,
        [string]$InitialDate
    )
    
    Init-Config
    
    switch ($Action) {
        "list" {
            Print-Header "Profiles"
            
            $profiles = Get-ChildItem -Path $Script:ProfilesDir -Filter "*.profile" -ErrorAction SilentlyContinue
            if ($profiles) {
                $activeProfile = Get-ConfigValue "PROFILE"
                foreach ($p in $profiles) {
                    $profileName = $p.BaseName
                    $marker = if ($profileName -eq $activeProfile) { " (active)" } else { "" }
                    Write-Host "  $profileName$marker"
                }
            } else {
                Write-Host "  No profiles configured"
            }
            Write-Host ""
        }
        "save" {
            if ([string]::IsNullOrEmpty($Name)) {
                Print-Error "Usage: gbd profile save <name>"
                return
            }
            
            $profileFile = Join-Path $Script:ProfilesDir "$Name.profile"
            Copy-Item $Script:ConfigFile $profileFile -Force
            Print-Success "Profile saved: $Name"
        }
        "load" {
            if ([string]::IsNullOrEmpty($Name)) {
                Print-Error "Usage: gbd profile load <name>"
                return
            }
            
            $profileFile = Join-Path $Script:ProfilesDir "$Name.profile"
            if (Test-Path $profileFile) {
                Copy-Item $profileFile $Script:ConfigFile -Force
                Set-ConfigValue "PROFILE" $Name
                Print-Success "Profile loaded: $Name"
            } else {
                Print-Error "Profile not found: $Name"
            }
        }
        "delete" {
            if ([string]::NullOrEmpty($Name)) {
                Print-Error "Usage: gbd profile delete <name>"
                return
            }
            
            $profileFile = Join-Path $Script:ProfilesDir "$Name.profile"
            if (Test-Path $profileFile) {
                Remove-Item $profileFile -Force
                Print-Success "Profile deleted: $Name"
            } else {
                Print-Error "Profile not found: $Name"
            }
        }
        "create" {
            if ([string]::IsNullOrEmpty($Name) -or [string]::IsNullOrEmpty($InitialDate)) {
                Print-Error "Usage: gbd profile create <name> <initial-date>"
                return
            }
            
            $profileFile = Join-Path $Script:ProfilesDir "$Name.profile"
            $config = @"
# Profile: $Name
INITIAL_DATE=$InitialDate
CURRENT_OFFSET=0
DEFAULT_TIME=09:00
PROFILE=$Name
"@
            Set-Content -Path $profileFile -Value $config
            Print-Success "Profile created: $Name"
        }
        default {
            Write-Host ""
            Write-Host "  Usage: gbd profile <action> [args]"
            Write-Host ""
            Write-Host "  Actions:"
            Write-Host "    list              List all profiles"
            Write-Host "    create <n> <date> Create new profile"
            Write-Host "    save <name>       Save current config as profile"
            Write-Host "    load <name>       Load a profile"
            Write-Host "    delete <name>     Delete a profile"
            Write-Host ""
        }
    }
}

# Gap detection
function Show-Gaps {
    param([int]$Threshold = 3)
    
    Print-Header "Gap Detection (threshold: $Threshold days)"
    
    $commits = git log --pretty=format:"%ad" --date=iso 2>$null
    
    $dates = @()
    foreach ($line in $commits) {
        try {
            $dates += [DateTime]::Parse($line)
        } catch {}
    }
    
    $dates = $dates | Sort-Object -Descending
    
    Write-Host ""
    
    $gapsFound = 0
    for ($i = 0; $i -lt $dates.Count - 1; $i++) {
        $gap = ($dates[$i] - $dates[$i+1]).Days
        if ($gap -ge $Threshold) {
            $gapsFound++
            Write-Host "  Gap: $gap days"
            Write-Host "    From: $($dates[$i+1].ToString('yyyy-MM-dd'))"
            Write-Host "    To:   $($dates[$i].ToString('yyyy-MM-dd'))"
            Write-Host ""
        }
    }
    
    if ($gapsFound -eq 0) {
        Print-Success "No gaps larger than $Threshold days found"
    } else {
        Print-Info "Found $gapsFound gaps"
    }
    
    Write-Host ""
}

# Template management
function Manage-Templates {
    param(
        [string]$Action,
        [string]$Name,
        [string]$Content
    )
    
    Init-Config
    
    switch ($Action) {
        "list" {
            Print-Header "Commit Templates"
            
            $templates = Get-ChildItem -Path $Script:TemplatesDir -Filter "*.txt" -ErrorAction SilentlyContinue
            if ($templates) {
                foreach ($t in $templates) {
                    Write-Host "  $($t.BaseName)"
                }
            } else {
                Write-Host "  No templates configured"
            }
            Write-Host ""
        }
        "add" {
            if ([string]::IsNullOrEmpty($Name)) {
                Print-Error "Usage: gbd template add <name>"
                return
            }
            
            Write-Host "Enter template content (Ctrl+C to finish):"
            $content = @()
            do {
                $line = Read-Host
                $content += $line
            } while ($line -ne "")
            
            $templateFile = Join-Path $Script:TemplatesDir "$Name.txt"
            Set-Content -Path $templateFile -Value ($content -join "`n")
            Print-Success "Template created: $Name"
        }
        "use" {
            if ([string]::IsNullOrEmpty($Name)) {
                Print-Error "Usage: gbd commit --template <name>"
                return
            }
            
            $templateFile = Join-Path $Script:TemplatesDir "$Name.txt"
            if (Test-Path $templateFile) {
                $content = Get-Content $templateFile -Raw
                Write-Host "Template content:"
                Write-Host $content
            } else {
                Print-Error "Template not found: $Name"
            }
        }
        "delete" {
            if ([string]::IsNullOrEmpty($Name)) {
                Print-Error "Usage: gbd template delete <name>"
                return
            }
            
            $templateFile = Join-Path $Script:TemplatesDir "$Name.txt"
            if (Test-Path $templateFile) {
                Remove-Item $templateFile -Force
                Print-Success "Template deleted: $Name"
            } else {
                Print-Error "Template not found: $Name"
            }
        }
        default {
            Write-Host ""
            Write-Host "  Usage: gbd template <action> [args]"
            Write-Host ""
            Write-Host "  Actions:"
            Write-Host "    list           List all templates"
            Write-Host "    add <name>     Create new template"
            Write-Host "    use <name>     Show template content"
            Write-Host "    delete <name>  Delete a template"
            Write-Host ""
        }
    }
}

# Show help
function Show-Help {
    Print-Header "Git Backdate (gbd) - Help"
    
    Write-Host @"
  USAGE:
    gbd <command> [arguments] [options]

  COMMANDS:
    init <YYYY-MM-DD>     Set initial reference date
    commit [days] [msg]   Create commit with date offset
    status                Show current configuration
    log [count]           Show recent commits with dates
    reset <option>        Reset configuration

  FEATURES:
    calendar [month]      Show commit calendar view
    stealth               Analyze for suspicious patterns
    sneak                 Quick stealth score
    doctor                Check system and get suggestions
    push [remote]         Interactive push helper
    profile <action>      Manage configuration profiles
    gaps [threshold]      Detect date gaps in history
    template <action>     Manage commit templates

  COMMIT OPTIONS:
    --time HH:MM          Set specific time for commit
    --jitter N            Add random minutes (±N)
    --preview             Show what would happen
    --template <name>     Use commit template

  EXAMPLES:
    gbd init 2023-03-15
    gbd commit 0 "Initial commit"
    gbd commit 1 "Add feature" --time 14:30
    gbd commit 2 "Fix bug" --jitter 30
    gbd commit 3 --preview
    gbd stealth
    gbd calendar

  ALIASES:
    gbd c    → commit
    gbd s    → status
    gbd st   → stealth
    gbd sk   → sneak
    gbd cal  → calendar

"@
}

# Show detailed docs
function Show-Docs {
    Print-Header "Git Backdate (gbd) - Documentation"
    
    Write-Host @"

  ╔══════════════════════════════════════════════════════════════╗
  ║                    GETTING STARTED                           ║
  ╚══════════════════════════════════════════════════════════════╝

  1. Initialize with a reference date:
     gbd init 2023-03-15

  2. Make commits with day offsets:
     gbd commit 0 "Initial commit"    # Day 0 (March 15)
     gbd commit 1 "Add feature"       # Day 1 (March 16)
     gbd commit 2 "Fix bugs"          # Day 2 (March 17)


  ╔══════════════════════════════════════════════════════════════╗
  ║                    TIME SPECIFICATION                        ║
  ╚══════════════════════════════════════════════════════════════╝

  Set specific commit times:
    gbd commit 1 "Morning work" --time 09:30
    gbd commit 1 "Late session" --time 23:45

  Add randomness (±N minutes):
    gbd commit 2 "Random time" --jitter 30
    gbd commit 3 "More random" --time 14:00 --jitter 60


  ╔══════════════════════════════════════════════════════════════╗
  ║                    STEALTH FEATURES                          ║
  ╚══════════════════════════════════════════════════════════════╝

  Analyze your commit history for suspicious patterns:
    gbd stealth    # Full analysis with detailed report
    gbd sneak      # Quick stealth score only

  Detection patterns checked:
    - Identical timestamps (multiple commits at same minute)
    - Late night commits (midnight to 6am)
    - Weekend activity patterns
    - Round timestamps (exact hours)
    - Large gaps between commits


  ╔══════════════════════════════════════════════════════════════╗
  ║                    PROFILES                                  ║
  ╚══════════════════════════════════════════════════════════════╝

  Save and load different configurations:
    gbd profile create work 2023-01-01
    gbd profile create personal 2023-06-01
    gbd profile list
    gbd profile load work
    gbd profile save current-state


  ╔══════════════════════════════════════════════════════════════╗
  ║                    TEMPLATES                                 ║
  ╚══════════════════════════════════════════════════════════════╝

  Create reusable commit messages:
    gbd template add feature
    gbd template add fix
    gbd template list

  Use templates:
    gbd commit 1 --template feature


  ╔══════════════════════════════════════════════════════════════╗
  ║                    CALENDAR VIEW                             ║
  ╚══════════════════════════════════════════════════════════════╝

  Visualize commit distribution:
    gbd calendar         # Current month
    gbd calendar 3       # March
    gbd calendar 3 2023  # March 2023

  Shows which days have commits with [N] markers.


  ╔══════════════════════════════════════════════════════════════╗
  ║                    PUSH HELPER                               ║
  ╚══════════════════════════════════════════════════════════════╝

  Interactive push with preview:
    gbd push
    gbd push origin main

  Shows commits to be pushed and asks for confirmation.


  ╔══════════════════════════════════════════════════════════════╗
  ║                    GAP DETECTION                             ║
  ╚══════════════════════════════════════════════════════════════╝

  Find gaps in commit history:
    gbd gaps           # Default 3-day threshold
    gbd gaps 7         # 7-day threshold

  Useful for identifying periods that might need "filling".


  ╔══════════════════════════════════════════════════════════════╗
  ║                    CONFIGURATION                             ║
  ╚══════════════════════════════════════════════════════════════╝

  Config location: $env:USERPROFILE\.git-backdate\

  Files:
    config              Current configuration
    profiles\*.profile  Saved profiles
    templates\*.txt     Commit templates

  Config values:
    INITIAL_DATE        Reference start date
    CURRENT_OFFSET      Next day offset
    DEFAULT_TIME        Default commit time
    PROFILE             Active profile name

"@
}

# Quick stealth score
function Get-SneakScore {
    $commits = git log --pretty=format:"%ad" --date=iso -n 50 2>$null
    $score = 100
    
    $lateNight = 0
    $roundTimes = 0
    $total = 0
    
    foreach ($line in $commits) {
        $total++
        if ($line -match " (\d{2}):(\d{2}):") {
            $hour = [int]$Matches[1]
            $minute = [int]$Matches[2]
            if ($hour -ge 0 -and $hour -lt 6) { $lateNight++ }
            if ($minute -eq 0) { $roundTimes++ }
        }
    }
    
    if ($lateNight -gt ($total * 0.3)) { $score -= 15 }
    if ($roundTimes -gt ($total * 0.5)) { $score -= 10 }
    
    Write-Host ""
    Write-Host "  Stealth Score: $score/100" -ForegroundColor $(if ($score -ge 80) { "Green" } elseif ($score -ge 60) { "Yellow" } else { "Red" })
    Write-Host ""
}

# Parse and execute command
function Main {
    Init-Config
    
    # Handle aliases
    switch ($Command) {
        "c" { $Command = "commit" }
        "s" { $Command = "status" }
        "st" { $Command = "stealth" }
        "sk" { $Command = "sneak" }
        "cal" { $Command = "calendar" }
        "p" { $Command = "push" }
        "g" { $Command = "gaps" }
        "t" { $Command = "template" }
        "pr" { $Command = "profile" }
        "d" { $Command = "docs" }
        "?" { $Command = "help" }
        "h" { $Command = "help" }
    }
    
    switch ($Command) {
        "init" {
            Invoke-Init $Args[0]
        }
        "commit" {
            $dayOffset = 0
            $message = ""
            $timeSpec = ""
            $jitter = 0
            $preview = $false
            $template = ""
            
            $i = 0
            while ($i -lt $Args.Count) {
                $arg = $Args[$i]
                switch -Regex ($arg) {
                    "^\d+$" { $dayOffset = [int]$arg }
                    "^--time$" { $timeSpec = $Args[++$i] }
                    "^--jitter$" { $jitter = [int]$Args[++$i] }
                    "^--preview$" { $preview = $true }
                    "^--template$" { $template = $Args[++$i] }
                    default { 
                        if (-not $arg.StartsWith("--")) {
                            $message += if ($message) { " $arg" } else { $arg }
                        }
                    }
                }
                $i++
            }
            
            Invoke-Commit -DayOffset $dayOffset -Message $message -TimeSpec $timeSpec -JitterMinutes $jitter -Preview:$preview -Template $template
        }
        "status" {
            Show-Status
        }
        "log" {
            $count = if ($Args[0]) { [int]$Args[0] } else { 10 }
            Show-Log $count
        }
        "reset" {
            Invoke-Reset $Args[0]
        }
        "calendar" {
            $month = if ($Args[0]) { [int]$Args[0] } else { 0 }
            $year = if ($Args[1]) { [int]$Args[1] } else { 0 }
            Show-Calendar $month $year
        }
        "stealth" {
            Invoke-StealthCheck
        }
        "sneak" {
            Get-SneakScore
        }
        "doctor" {
            Invoke-Doctor
        }
        "push" {
            Invoke-PushHelper $Args[0] $Args[1]
        }
        "profile" {
            Manage-Profiles $Args[0] $Args[1] $Args[2]
        }
        "gaps" {
            $threshold = if ($Args[0]) { [int]$Args[0] } else { 3 }
            Show-Gaps $threshold
        }
        "template" {
            Manage-Templates $Args[0] $Args[1]
        }
        "docs" {
            Show-Docs
        }
        "help" {
            Show-Help
        }
        "--help" {
            Show-Help
        }
        "-h" {
            Show-Help
        }
        "" {
            Show-Help
        }
        default {
            Print-Error "Unknown command: $Command"
            Print-Info "Run 'gbd help' for usage information"
        }
    }
}

# Run main function
Main