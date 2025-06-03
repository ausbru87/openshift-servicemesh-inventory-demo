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
