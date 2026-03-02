from app.engine.categories.base import BaseCategoryAnalyzer


class Cat11OSKernelAnalyzer(BaseCategoryAnalyzer):
    category_id = 11
    name = "OS & Kernel Level"
    part = "B"
    min_signals = 20

    def get_checklist(self) -> list[str]:
        return [
            "File descriptor limit",
            "Inode exhaustion",
            "Disk I/O saturation",
            "Swap thrashing",
            "TCP kernel params (somaxconn)",
            "TIME_WAIT accumulation",
            "TCP FIN timeout",
            "Ephemeral port range",
            "Conntrack table",
            "OOM killer scoring",
            "Core dump handling",
            "System clock sync (NTP)",
            "cgroup limits",
            "PID limit",
            "Filesystem mount options",
            "Transparent Huge Pages",
            "NUMA topology",
            "IRQ affinity",
            "Kernel security modules (AppArmor/SELinux)",
            "Container cgroup driver mismatch",
            "Journal rotation",
            "/tmp partition separation",
        ]
