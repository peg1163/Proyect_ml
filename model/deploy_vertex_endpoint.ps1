param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectId,

    [Parameter(Mandatory = $true)]
    [string] $Bucket,

    [string] $Region = "us-central1",
    [string] $Repository = "house-price-vertex",
    [string] $ImageName = "house-price-catboost",
    [string] $ModelDisplayName = "house-price-catboost-grid-original",
    [string] $EndpointDisplayName = "house-price-catboost-endpoint",
    [string] $MachineType = "n1-standard-2"
)

$ErrorActionPreference = "Stop"

$ImageUri = "$Region-docker.pkg.dev/$ProjectId/$Repository/$ImageName`:latest"
$ArtifactUri = "gs://$Bucket/modelos/house-price-catboost"

gcloud config set project $ProjectId

python model\train_grid_search_target_original.py
gcloud storage cp model/artifacts/* "$ArtifactUri/"

gcloud artifacts repositories describe $Repository --location=$Region 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud artifacts repositories create $Repository `
        --repository-format=docker `
        --location=$Region `
        --description="Imagenes Docker para modelos Vertex AI"
}

gcloud builds submit `
    --tag $ImageUri `
    --file Dockerfile.vertex .

gcloud ai models upload `
    --region=$Region `
    --display-name=$ModelDisplayName `
    --artifact-uri=$ArtifactUri `
    --container-image-uri=$ImageUri `
    --container-ports=8080 `
    --container-health-route=/health `
    --container-predict-route=/predict

$ModelId = gcloud ai models list `
    --region=$Region `
    --filter="displayName=$ModelDisplayName" `
    --sort-by=~createTime `
    --limit=1 `
    --format="value(name.basename())"

gcloud ai endpoints create `
    --region=$Region `
    --display-name=$EndpointDisplayName

$EndpointId = gcloud ai endpoints list `
    --region=$Region `
    --filter="displayName=$EndpointDisplayName" `
    --sort-by=~createTime `
    --limit=1 `
    --format="value(name.basename())"

gcloud ai endpoints deploy-model $EndpointId `
    --region=$Region `
    --model=$ModelId `
    --display-name=$ModelDisplayName `
    --machine-type=$MachineType `
    --traffic-split=0=100 `
    --min-replica-count=1 `
    --max-replica-count=1

Write-Host "Vertex AI endpoint listo."
Write-Host "Model ID: $ModelId"
Write-Host "Endpoint ID: $EndpointId"
Write-Host "Region: $Region"
