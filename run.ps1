# Convenience wrapper: `.\run.ps1` uses the repo venv's python for everything.
param([Parameter(ValueFromRemainingArguments = $true)] [string[]] $Args)

$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"
& $PY @Args
