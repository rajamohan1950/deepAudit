"""Auto-discovers and registers all 40 category analyzers."""

import importlib
import logging

from app.engine.categories.base import BaseCategoryAnalyzer

logger = logging.getLogger(__name__)

_REGISTRY: dict[int, BaseCategoryAnalyzer] = {}

CATEGORY_MODULES = [
    ("app.engine.categories.cat_01_authentication", "Cat01AuthenticationAnalyzer"),
    ("app.engine.categories.cat_02_authorization", "Cat02AuthorizationAnalyzer"),
    ("app.engine.categories.cat_03_input_validation", "Cat03InputValidationAnalyzer"),
    ("app.engine.categories.cat_04_data_protection", "Cat04DataProtectionAnalyzer"),
    ("app.engine.categories.cat_05_cryptography", "Cat05CryptographyAnalyzer"),
    ("app.engine.categories.cat_06_memory", "Cat06MemoryAnalyzer"),
    ("app.engine.categories.cat_07_cpu_compute", "Cat07CpuComputeAnalyzer"),
    ("app.engine.categories.cat_08_network_io", "Cat08NetworkIoAnalyzer"),
    ("app.engine.categories.cat_09_database", "Cat09DatabaseAnalyzer"),
    ("app.engine.categories.cat_10_caching", "Cat10CachingAnalyzer"),
    ("app.engine.categories.cat_11_os_kernel", "Cat11OsKernelAnalyzer"),
    ("app.engine.categories.cat_12_graceful_shutdown", "Cat12GracefulShutdownAnalyzer"),
    ("app.engine.categories.cat_13_spof", "Cat13SpofAnalyzer"),
    ("app.engine.categories.cat_14_fault_tolerance", "Cat14FaultToleranceAnalyzer"),
    ("app.engine.categories.cat_15_concurrency", "Cat15ConcurrencyAnalyzer"),
    ("app.engine.categories.cat_16_data_integrity", "Cat16DataIntegrityAnalyzer"),
    ("app.engine.categories.cat_17_distributed_systems", "Cat17DistributedSystemsAnalyzer"),
    ("app.engine.categories.cat_18_queue_processing", "Cat18QueueProcessingAnalyzer"),
    ("app.engine.categories.cat_19_infra_security", "Cat19InfraSecurityAnalyzer"),
    ("app.engine.categories.cat_20_capacity_planning", "Cat20CapacityPlanningAnalyzer"),
    ("app.engine.categories.cat_21_deployment_cicd", "Cat21DeploymentCicdAnalyzer"),
    ("app.engine.categories.cat_22_supply_chain", "Cat22SupplyChainAnalyzer"),
    ("app.engine.categories.cat_23_aiml_risks", "Cat23AimlRisksAnalyzer"),
    ("app.engine.categories.cat_24_aiml_operations", "Cat24AimlOperationsAnalyzer"),
    ("app.engine.categories.cat_25_metrics_monitoring", "Cat25MetricsMonitoringAnalyzer"),
    ("app.engine.categories.cat_26_logging", "Cat26LoggingAnalyzer"),
    ("app.engine.categories.cat_27_distributed_tracing", "Cat27DistributedTracingAnalyzer"),
    ("app.engine.categories.cat_28_alerting_incident", "Cat28AlertingIncidentAnalyzer"),
    ("app.engine.categories.cat_29_testing_qa", "Cat29TestingQaAnalyzer"),
    ("app.engine.categories.cat_30_code_quality", "Cat30CodeQualityAnalyzer"),
    ("app.engine.categories.cat_31_api_design", "Cat31ApiDesignAnalyzer"),
    ("app.engine.categories.cat_32_ux_accessibility", "Cat32UxAccessibilityAnalyzer"),
    ("app.engine.categories.cat_33_cost_finops", "Cat33CostFinopsAnalyzer"),
    ("app.engine.categories.cat_34_multi_tenancy", "Cat34MultiTenancyAnalyzer"),
    ("app.engine.categories.cat_35_compliance", "Cat35ComplianceAnalyzer"),
    ("app.engine.categories.cat_36_disaster_recovery", "Cat36DisasterRecoveryAnalyzer"),
    ("app.engine.categories.cat_37_i18n", "Cat37I18nAnalyzer"),
    ("app.engine.categories.cat_38_state_management", "Cat38StateManagementAnalyzer"),
    ("app.engine.categories.cat_39_backward_compat", "Cat39BackwardCompatAnalyzer"),
    ("app.engine.categories.cat_40_organizational", "Cat40OrganizationalAnalyzer"),
]


def _load_registry():
    if _REGISTRY:
        return

    for module_path, class_name in CATEGORY_MODULES:
        try:
            module = importlib.import_module(module_path)
            analyzer_class = getattr(module, class_name)
            instance = analyzer_class()
            _REGISTRY[instance.category_id] = instance
        except Exception as e:
            logger.error(f"Failed to load category {module_path}: {e}")

    logger.info(f"Loaded {len(_REGISTRY)} category analyzers")


def get_analyzer(category_id: int) -> BaseCategoryAnalyzer:
    _load_registry()
    analyzer = _REGISTRY.get(category_id)
    if not analyzer:
        raise ValueError(f"No analyzer for category {category_id}")
    return analyzer


def get_analyzers(category_ids: list[int]) -> list[BaseCategoryAnalyzer]:
    return [get_analyzer(cid) for cid in category_ids]


def get_all_analyzers() -> dict[int, BaseCategoryAnalyzer]:
    _load_registry()
    return dict(_REGISTRY)
