{{/*
Expand the name of the chart.
*/}}
{{- define "open-healthcare.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "open-healthcare.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "open-healthcare.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "open-healthcare.labels" -}}
helm.sh/chart: {{ include "open-healthcare.chart" . }}
{{ include "open-healthcare.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: open-healthcare-agentic-platform
{{- end }}

{{/*
Selector labels
*/}}
{{- define "open-healthcare.selectorLabels" -}}
app.kubernetes.io/name: {{ include "open-healthcare.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API component labels
*/}}
{{- define "open-healthcare.api.labels" -}}
{{ include "open-healthcare.labels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
API selector labels
*/}}
{{- define "open-healthcare.api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "open-healthcare.name" . }}-api
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
UI component labels
*/}}
{{- define "open-healthcare.ui.labels" -}}
{{ include "open-healthcare.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
UI selector labels
*/}}
{{- define "open-healthcare.ui.selectorLabels" -}}
app.kubernetes.io/name: {{ include "open-healthcare.name" . }}-ui
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "open-healthcare.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "open-healthcare.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
