#!/bin/bash
set -e

# Cross-Platform GitOps Setup Script
# Works on both macOS and Linux

GITHUB_REPO="${1:-https://github.com/ausbru87/openshift-servicemesh-inventory-demo.git}"

echo "🚀 Setting up Simple GitOps for Service Mesh Demo"
echo "📦 Repository: $GITHUB_REPO"
echo "🖥️  Platform: $(uname -s)"

# Detect platform for cross-platform compatibility
detect_platform() {
    case "$(uname -s)" in
        Darwin*)    echo "macos";;
        Linux*)     echo "linux";;
        *)          echo "unknown";;
    esac
}

PLATFORM=$(detect_platform)

# Cross-platform timeout function
wait_with_timeout() {
    local timeout_seconds=$1
    local check_command=$2
    local description=$3
    
    echo "⏳ Waiting for $description (timeout: ${timeout_seconds}s)..."
    
    for i in $(seq 1 $timeout_seconds); do
        if eval "$check_command" &>/dev/null; then
            echo "✅ $description ready"
            return 0
        fi
        
        # Progress indicator every 10 seconds
        if [ $((i % 10)) -eq 0 ]; then
            echo "   ... still waiting ($i/${timeout_seconds}s)"
        fi
        
        sleep 1
    done
    
    echo "⚠️  Timeout waiting for $description"
    return 1
}

# Cross-platform sed function
cross_platform_sed() {
    local pattern=$1
    local file=$2
    
    if [ "$PLATFORM" = "macos" ]; then
        sed -i.bak "$pattern" "$file"
        rm -f "${file}.bak"
    else
        sed -i "$pattern" "$file"
    fi
}

# Check OpenShift access
echo "🔐 Checking OpenShift access..."
if ! oc whoami &>/dev/null; then
    echo "❌ Error: Not logged into OpenShift. Please run 'oc login' first."
    exit 1
fi

OC_USER=$(oc whoami)
echo "✅ Logged in as: $OC_USER"

# Check cluster admin permissions
if ! oc auth can-i create clusterrole &>/dev/null; then
    echo "⚠️  Warning: You may not have cluster-admin permissions"
    echo "   GitOps operator installation might fail"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install GitOps operator
echo "📦 Installing OpenShift GitOps operator..."
if ! oc apply -f gitops/bootstrap/gitops-operator.yaml; then
    echo "❌ Failed to install GitOps operator"
    exit 1
fi

# Wait for operator installation
wait_with_timeout 300 "oc get csv -n openshift-operators | grep -q 'openshift-gitops-operator.*Succeeded'" "GitOps operator installation"

# Wait for namespace creation
wait_with_timeout 120 "oc get namespace openshift-gitops" "openshift-gitops namespace creation"

# Wait for ArgoCD instance to be created
echo "⏳ Waiting for ArgoCD instance to be created..."
sleep 30

wait_with_timeout 300 "oc get argocd openshift-gitops -n openshift-gitops" "ArgoCD instance creation"

# Wait for ArgoCD server deployment
wait_with_timeout 300 "oc get deployment openshift-gitops-server -n openshift-gitops" "ArgoCD server deployment"

# Wait for ArgoCD to be ready
wait_with_timeout 300 "oc wait --for=condition=Available deployment/openshift-gitops-server -n openshift-gitops --timeout=1s" "ArgoCD server to be ready"

# Update applications with correct repo URL
echo "🔧 Updating GitOps applications with repository: $GITHUB_REPO"
if [ -f "gitops/applications/inventory-demo-app.yaml" ]; then
    cross_platform_sed "s|https://github.com/your-username/openshift-servicemesh-inventory-demo.git|$GITHUB_REPO|g" "gitops/applications/inventory-demo-app.yaml"
    echo "✅ Updated inventory-demo-app.yaml"
else
    echo "⚠️  Warning: gitops/applications/inventory-demo-app.yaml not found"
fi

# Set up RBAC for ArgoCD
echo "🔐 Setting up RBAC for ArgoCD..."
cat << EOF | oc apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: openshift-gitops-argocd-admin
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: openshift-gitops-argocd-application-controller
  namespace: openshift-gitops
- kind: ServiceAccount
  name: openshift-gitops-argocd-server
  namespace: openshift-gitops
EOF

# Deploy ArgoCD applications
echo "🎯 Deploying ArgoCD applications..."
if ! oc apply -f gitops/applications/; then
    echo "❌ Failed to deploy ArgoCD applications"
    exit 1
fi

# Wait for applications to be created
echo "⏳ Waiting for ArgoCD applications to be created..."
sleep 15

# Get ArgoCD URL and credentials
echo "🔍 Getting ArgoCD access information..."

# Get ArgoCD URL
ARGOCD_URL=""
if oc get route openshift-gitops-server -n openshift-gitops &>/dev/null; then
    ARGOCD_URL=$(oc get route openshift-gitops-server -n openshift-gitops -o jsonpath='{.spec.host}' 2>/dev/null)
fi

# Get ArgoCD password
ARGOCD_PASSWORD=""
if oc get secret openshift-gitops-cluster -n openshift-gitops &>/dev/null; then
    ARGOCD_PASSWORD=$(oc get secret openshift-gitops-cluster -n openshift-gitops -o jsonpath='{.data.admin\.password}' 2>/dev/null | base64 -d 2>/dev/null)
fi

# Service Mesh status check
echo "🌐 Checking Service Mesh status..."
if oc get smcp basic -n istio-system &>/dev/null; then
    SMCP_STATUS=$(oc get smcp basic -n istio-system -o jsonpath='{.status.conditions[-1].type}' 2>/dev/null || echo "Unknown")
    echo "✅ Service Mesh Control Plane found (Status: $SMCP_STATUS)"
else
    echo "⚠️  Service Mesh not found - you'll need to deploy it separately"
fi

# Display results
echo ""
echo "════════════════════════════════════════════"
echo "✅ GitOps setup complete!"
echo "════════════════════════════════════════════"
echo ""
if [ -n "$ARGOCD_URL" ]; then
    echo "🔗 ArgoCD Dashboard: https://$ARGOCD_URL"
else
    echo "🔗 ArgoCD Dashboard: Check 'oc get route -n openshift-gitops' in a few minutes"
fi

echo "👤 Username: admin"

if [ -n "$ARGOCD_PASSWORD" ]; then
    echo "🔐 Password: $ARGOCD_PASSWORD"
else
    echo "🔐 Password: Run 'oc get secret openshift-gitops-cluster -n openshift-gitops -o jsonpath=\"{.data.admin\\.password}\" | base64 -d' in a few minutes"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Wait 2-3 minutes for all components to fully initialize"
echo "2. Access ArgoCD dashboard using the credentials above"
echo "3. Push code changes to trigger GitHub Actions workflow"
echo "4. Watch ArgoCD automatically deploy your changes!"
echo ""
echo "📊 Monitoring Commands:"
echo "  oc get applications -n openshift-gitops"
echo "  oc get pods -n inventory-demo"
echo "  oc get pods -n openshift-gitops"
echo ""
echo "🌐 Service Mesh URLs (after deployment):"
echo "  Kiali: https://\$(oc get route kiali -n istio-system -o jsonpath='{.spec.host}' 2>/dev/null)"
echo "  Jaeger: https://\$(oc get route jaeger -n istio-system -o jsonpath='{.spec.host}' 2>/dev/null)"
echo ""
echo "🔧 Troubleshooting:"
echo "  View ArgoCD logs: oc logs deployment/openshift-gitops-server -n openshift-gitops"
echo "  Check operator status: oc get csv -n openshift-operators"
echo "  Check application sync: oc get applications -n openshift-gitops"

# Create status check script
cat > scripts/check-status.sh << 'EOF'
#!/bin/bash
echo "🔍 GitOps and Service Mesh Status Check"
echo "========================================"
echo ""

echo "📱 ArgoCD Applications:"
oc get applications -n openshift-gitops 2>/dev/null || echo "  No applications found"

echo ""
echo "🚀 Inventory Demo Pods:"
oc get pods -n inventory-demo 2>/dev/null || echo "  inventory-demo namespace not ready yet"

echo ""
echo "🌐 Service Mesh Status:"
oc get smcp -n istio-system 2>/dev/null || echo "  Service Mesh not deployed yet"

echo ""
echo "🔗 Application URLs:"
INVENTORY_URL=$(oc get route inventory-demo -n inventory-demo -o jsonpath='{.spec.host}' 2>/dev/null)
KIALI_URL=$(oc get route kiali -n istio-system -o jsonpath='{.spec.host}' 2>/dev/null)
JAEGER_URL=$(oc get route jaeger -n istio-system -o jsonpath='{.spec.host}' 2>/dev/null)
ARGOCD_URL=$(oc get route openshift-gitops-server -n openshift-gitops -o jsonpath='{.spec.host}' 2>/dev/null)

if [ -n "$INVENTORY_URL" ]; then
    echo "  📦 Inventory App: https://$INVENTORY_URL"
else
    echo "  📦 Inventory App: Not ready yet"
fi

if [ -n "$KIALI_URL" ]; then
    echo "  📊 Kiali Dashboard: https://$KIALI_URL"
else
    echo "  📊 Kiali Dashboard: Not ready yet"
fi

if [ -n "$JAEGER_URL" ]; then
    echo "  🔍 Jaeger Tracing: https://$JAEGER_URL"
else
    echo "  🔍 Jaeger Tracing: Not ready yet"
fi

if [ -n "$ARGOCD_URL" ]; then
    echo "  🔗 ArgoCD Dashboard: https://$ARGOCD_URL"
else
    echo "  🔗 ArgoCD Dashboard: Not ready yet"
fi

echo ""
echo "🔐 ArgoCD Password:"
ARGOCD_PASSWORD=$(oc get secret openshift-gitops-cluster -n openshift-gitops -o jsonpath='{.data.admin\.password}' 2>/dev/null | base64 -d 2>/dev/null)
if [ -n "$ARGOCD_PASSWORD" ]; then
    echo "  admin / $ARGOCD_PASSWORD"
else
    echo "  Not ready yet"
fi
EOF

chmod +x scripts/check-status.sh

echo ""
echo "📋 Status check script created: ./scripts/check-status.sh"
echo "   Run this anytime to check deployment status"