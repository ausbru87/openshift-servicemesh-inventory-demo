#!/bin/bash
set -e

GITHUB_REPO="${1:-https://github.com/your-username/openshift-servicemesh-inventory-demo.git}"
echo "🚀 Setting up Simple GitOps for Service Mesh Demo"
echo "📦 Repository: $GITHUB_REPO"

# Check OpenShift access
if ! oc whoami &>/dev/null; then
    echo "❌ Error: Please run 'oc login' first"
    exit 1
fi

# Install GitOps operator
echo "📦 Installing OpenShift GitOps..."
oc apply -f gitops/bootstrap/gitops-operator.yaml

# Wait for GitOps to be ready
echo "⏳ Waiting for GitOps operator..."
sleep 60
timeout 300 bash -c 'until oc get namespace openshift-gitops &>/dev/null; do sleep 5; done'

# Update applications with correct repo
echo "🔧 Updating GitOps apps with your repository..."
sed -i.bak "s|https://github.com/your-username/openshift-servicemesh-inventory-demo.git|$GITHUB_REPO|g" gitops/applications/*.yaml

# Deploy ArgoCD applications
echo "🎯 Deploying ArgoCD applications..."
oc apply -f gitops/applications/

# Get URLs
ARGOCD_URL=$(oc get route openshift-gitops-server -n openshift-gitops -o jsonpath='{.spec.host}' 2>/dev/null || echo "Not ready yet")
ARGOCD_PASSWORD=$(oc get secret openshift-gitops-cluster -n openshift-gitops -o jsonpath='{.data.admin\.password}' 2>/dev/null | base64 -d || echo "Not ready yet")

echo ""
echo "✅ GitOps setup complete!"
echo "🔗 ArgoCD: https://$ARGOCD_URL"
echo "👤 Username: admin"
echo "🔐 Password: $ARGOCD_PASSWORD"
echo ""
echo "🎯 Next steps:"
echo "1. Update your GitHub username in the files"
echo "2. Push changes to trigger the workflow"
echo "3. Watch ArgoCD deploy automatically!"
