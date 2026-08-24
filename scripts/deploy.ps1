[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z][a-z0-9-]{4,28}[a-z0-9]$')]
    [string]$ProjectId,

    [ValidatePattern('^[a-z][a-z0-9-]{0,62}$')]
    [string]$Region = 'us-central1',

    [ValidatePattern('^[a-z][a-z0-9-]{0,62}$')]
    [string]$Service = 'closeout',

    [ValidatePattern('^[a-z][a-z0-9-]{0,62}$')]
    [string]$WorkerService = 'closeout-worker',

    [ValidatePattern('^[a-z][a-z0-9-]{0,99}$')]
    [string]$Queue = 'closeout-runs'
)

$ErrorActionPreference = 'Stop'

function Resolve-GcloudCommand {
    $command = Get-Command gcloud -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $userInstall = Join-Path $env:LOCALAPPDATA 'Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd'
    if (Test-Path -LiteralPath $userInstall -PathType Leaf) {
        return $userInstall
    }

    throw 'Google Cloud CLI is required. Install gcloud, then run gcloud auth login.'
}

$script:GcloudCommand = Resolve-GcloudCommand

function Invoke-Gcloud {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    & $script:GcloudCommand @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud failed: gcloud $($Arguments -join ' ')"
    }
}

function Test-GcloudResource {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    & $script:GcloudCommand @Arguments *> $null
    return $LASTEXITCODE -eq 0
}

$activeAccount = & $script:GcloudCommand auth list '--filter=status:ACTIVE' '--format=value(account)' |
    Select-Object -First 1
if (-not $activeAccount) {
    throw 'No active Google Cloud account. Run gcloud auth login first.'
}

$runtimeAccountName = 'closeout-runtime'
$taskAccountName = 'closeout-tasks'
$runtimeAccount = "$runtimeAccountName@$ProjectId.iam.gserviceaccount.com"
$taskAccount = "$taskAccountName@$ProjectId.iam.gserviceaccount.com"

Invoke-Gcloud @('config', 'set', 'project', $ProjectId)
Invoke-Gcloud @(
    'services', 'enable',
    'aiplatform.googleapis.com',
    'artifactregistry.googleapis.com',
    'cloudbuild.googleapis.com',
    'cloudtasks.googleapis.com',
    'firestore.googleapis.com',
    'run.googleapis.com',
    "--project=$ProjectId"
)

foreach ($account in @(
    @{ Name = $runtimeAccountName; Display = 'Closeout runtime' },
    @{ Name = $taskAccountName; Display = 'Closeout task identity' }
)) {
    $email = "$($account.Name)@$ProjectId.iam.gserviceaccount.com"
    if (-not (Test-GcloudResource @('iam', 'service-accounts', 'describe', $email, "--project=$ProjectId"))) {
        Invoke-Gcloud @(
            'iam', 'service-accounts', 'create', $account.Name,
            "--display-name=$($account.Display)",
            "--project=$ProjectId"
        )
    }
}

foreach ($role in @('roles/datastore.user', 'roles/aiplatform.user', 'roles/cloudtasks.enqueuer')) {
    Invoke-Gcloud @(
        'projects', 'add-iam-policy-binding', $ProjectId,
        "--member=serviceAccount:$runtimeAccount",
        "--role=$role",
        '--condition=None',
        '--quiet'
    )
}

Invoke-Gcloud @(
    'iam', 'service-accounts', 'add-iam-policy-binding', $taskAccount,
    "--member=serviceAccount:$runtimeAccount",
    '--role=roles/iam.serviceAccountUser',
    "--project=$ProjectId",
    '--quiet'
)

$projectNumber = & $script:GcloudCommand projects describe $ProjectId '--format=value(projectNumber)'
if ($LASTEXITCODE -ne 0 -or -not $projectNumber) {
    throw "Could not resolve project number for $ProjectId"
}
$cloudTasksAgent = "service-$projectNumber@gcp-sa-cloudtasks.iam.gserviceaccount.com"
Invoke-Gcloud @(
    'iam', 'service-accounts', 'add-iam-policy-binding', $taskAccount,
    "--member=serviceAccount:$cloudTasksAgent",
    '--role=roles/iam.serviceAccountTokenCreator',
    "--project=$ProjectId",
    '--quiet'
)

if (-not (Test-GcloudResource @(
    'firestore', 'databases', 'describe', '--database=(default)', "--project=$ProjectId"
))) {
    Invoke-Gcloud @(
        'firestore', 'databases', 'create', '--database=(default)',
        "--location=$Region", '--type=firestore-native', '--delete-protection',
        "--project=$ProjectId", '--quiet'
    )
}

if (-not (Test-GcloudResource @(
    'tasks', 'queues', 'describe', $Queue, "--location=$Region", "--project=$ProjectId"
))) {
    Invoke-Gcloud @(
        'tasks', 'queues', 'create', $Queue,
        "--location=$Region", "--project=$ProjectId", '--quiet'
    )
}

$commonEnvironment = @(
    'ENVIRONMENT=production',
    'GOOGLE_GENAI_USE_VERTEXAI=true',
    "GOOGLE_CLOUD_PROJECT=$ProjectId",
    'GOOGLE_CLOUD_LOCATION=global',
    'CLOSEOUT_MODEL=gemini-3.5-flash',
    'CLOSEOUT_STORE=firestore',
    "CLOSEOUT_TASKS_LOCATION=$Region",
    "CLOSEOUT_TASKS_QUEUE=$Queue"
) -join ','

$workerEnvironment = "$commonEnvironment,CLOSEOUT_DISPATCHER=local"
Invoke-Gcloud @(
    'run', 'deploy', $WorkerService,
    '--source=.',
    "--region=$Region",
    "--project=$ProjectId",
    "--service-account=$runtimeAccount",
    "--set-env-vars=$workerEnvironment",
    '--memory=1Gi',
    '--concurrency=10',
    '--max-instances=3',
    '--timeout=300',
    '--no-allow-unauthenticated',
    '--quiet'
)

$workerUrl = & $script:GcloudCommand run services describe $WorkerService `
    "--region=$Region" "--project=$ProjectId" '--format=value(status.url)'
if ($LASTEXITCODE -ne 0 -or -not $workerUrl) {
    throw "Could not resolve the $WorkerService URL"
}
$image = & $script:GcloudCommand run services describe $WorkerService `
    "--region=$Region" "--project=$ProjectId" '--format=value(spec.template.spec.containers[0].image)'
if ($LASTEXITCODE -ne 0 -or -not $image) {
    throw "Could not resolve the $WorkerService image"
}

Invoke-Gcloud @(
    'run', 'services', 'add-iam-policy-binding', $WorkerService,
    "--member=serviceAccount:$taskAccount",
    '--role=roles/run.invoker',
    "--region=$Region", "--project=$ProjectId", '--quiet'
)

$publicEnvironment = @(
    $commonEnvironment,
    'CLOSEOUT_DISPATCHER=cloud-tasks',
    "CLOSEOUT_SERVICE_URL=$workerUrl",
    "CLOSEOUT_TASK_SERVICE_ACCOUNT=$taskAccount"
) -join ','
Invoke-Gcloud @(
    'run', 'deploy', $Service,
    "--image=$image",
    "--region=$Region",
    "--project=$ProjectId",
    "--service-account=$runtimeAccount",
    "--set-env-vars=$publicEnvironment",
    '--memory=512Mi',
    '--concurrency=40',
    '--max-instances=3',
    '--timeout=60',
    '--allow-unauthenticated',
    '--quiet'
)

$publicUrl = & $script:GcloudCommand run services describe $Service `
    "--region=$Region" "--project=$ProjectId" '--format=value(status.url)'
if ($LASTEXITCODE -ne 0 -or -not $publicUrl) {
    throw "Could not resolve the $Service URL"
}

Write-Host ''
Write-Host 'Closeout deployment complete.' -ForegroundColor Green
Write-Host "Public URL: $publicUrl"
Write-Host "Worker URL: $workerUrl"
Write-Host "Runtime account: $runtimeAccount"
Write-Host "Task identity: $taskAccount"
