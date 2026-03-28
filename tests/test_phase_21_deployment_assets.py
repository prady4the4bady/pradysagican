"""PHASE 21 tests: deployment assets (Docker Compose, Kubernetes, Helm)."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent


def test_docker_compose_exists_and_has_service() -> None:
    compose_path = ROOT / "docker-compose.yml"
    assert compose_path.exists()
    data = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    assert "services" in data
    assert "pradysagican-api" in data["services"]


def test_k8s_manifests_exist() -> None:
    deployment_path = ROOT / "deploy" / "k8s" / "deployment.yaml"
    service_path = ROOT / "deploy" / "k8s" / "service.yaml"
    assert deployment_path.exists()
    assert service_path.exists()

    deployment = yaml.safe_load(deployment_path.read_text(encoding="utf-8"))
    service = yaml.safe_load(service_path.read_text(encoding="utf-8"))

    assert deployment["kind"] == "Deployment"
    assert service["kind"] == "Service"
    assert deployment["spec"]["template"]["spec"]["containers"][0]["ports"][0]["containerPort"] == 8000


def test_helm_chart_templates_exist() -> None:
    chart_path = ROOT / "deploy" / "helm" / "Chart.yaml"
    values_path = ROOT / "deploy" / "helm" / "values.yaml"
    deployment_tpl = ROOT / "deploy" / "helm" / "templates" / "deployment.yaml"
    service_tpl = ROOT / "deploy" / "helm" / "templates" / "service.yaml"

    assert chart_path.exists()
    assert values_path.exists()
    assert deployment_tpl.exists()
    assert service_tpl.exists()

    chart = yaml.safe_load(chart_path.read_text(encoding="utf-8"))
    values = yaml.safe_load(values_path.read_text(encoding="utf-8"))

    assert chart["name"] == "pradysagican"
    assert "image" in values
    assert values["service"]["targetPort"] == 8000
