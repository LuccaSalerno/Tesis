#!/usr/bin/env bash
# Ejecución manual por el operador; no integrar en GitHub Actions ni automatizaciones.
# SOLO LECTURA. No crea, altera ni elimina recursos. Puede requerir permisos IAM.
# Ojo: las salidas incluyen IDs de cuenta/roles; sanear antes de compartir.
set -u
REGION="${AWS_REGION:-us-east-1}"
run() { printf '\n### %s\n' "$1"; shift; "$@" || printf 'ERROR / SIN PERMISOS; requiere revisión (no equivale a No aplica)\n'; }
run 'Identidad AWS' aws sts get-caller-identity
run 'AWS Organizations (membresía)' aws organizations describe-organization --query 'Organization.{Id:Id,FeatureSet:FeatureSet}'
run 'Política efectiva de IA' aws organizations describe-effective-policy --policy-type AISERVICES_OPT_OUT_POLICY
run 'Registro de Bedrock de esta región' aws bedrock get-model-invocation-logging-configuration --region "$REGION"
run 'Modelos disponibles desde región de origen' aws bedrock list-foundation-models --region "$REGION" --query 'modelSummaries[].[modelId,modelName,modelLifecycle.status]' --output table
run 'Perfiles de inferencia desde región de origen' aws bedrock list-inference-profiles --region "$REGION" --type-equals SYSTEM_DEFINED --query 'inferenceProfileSummaries[].[inferenceProfileId,inferenceProfileName,status]' --output table
if [ -n "${INFERENCE_PROFILE_ID:-}" ];then
 run 'Destinos exactos del perfil' aws bedrock get-inference-profile --region "$REGION" --inference-profile-identifier "$INFERENCE_PROFILE_ID" --query '{Id:inferenceProfileId,Models:models[].modelArn,Status:status}'
else
 echo 'INFERENCE_PROFILE_ID no configurado: no se comprobó GetInferenceProfile. Buscar ID real en la salida de list-inference-profiles.'
fi
