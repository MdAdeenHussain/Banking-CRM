"""Commission engine with slab-based payout rules."""

# ======================================
# SECTION: Imports
# ======================================
from __future__ import annotations


# ======================================
# SECTION: Core Service Logic
# ======================================
class CommissionService:
    """Calculates disbursal commission, splits, and statutory deductions."""

    def calculate_payout(self, disbursal_amount: float) -> dict:
        """Calculate slab-based commission payout.

        Slabs:
        - 0 to 50L     -> 0.50%
        - 50L to 1Cr   -> 0.65%
        - Above 1Cr    -> 0.80%

        Returns gross, tds, and net.
        """
        rate = self._slab_rate(disbursal_amount)
        gross = max(disbursal_amount, 0) * rate
        tds = self.calculate_tds(gross)
        net = gross - tds

        return {
            "disbursal_amount": round(disbursal_amount, 2),
            "slab_rate_percent": round(rate * 100, 3),
            "gross": round(gross, 2),
            "tds": round(tds, 2),
            "net": round(net, 2),
        }

    def split_branch_share(self, gross_commission: float, branch_share_ratio: float = 0.60) -> float:
        """Split gross commission share for branch."""
        ratio = min(max(branch_share_ratio, 0), 1)
        return round(gross_commission * ratio, 2)

    def split_agent_share(self, gross_commission: float, agent_share_ratio: float = 0.40) -> float:
        """Split gross commission share for agent."""
        ratio = min(max(agent_share_ratio, 0), 1)
        return round(gross_commission * ratio, 2)

    def calculate_tds(self, gross_commission: float, tds_rate_percent: float = 5.0) -> float:
        """Calculate TDS deduction from gross commission."""
        return round(max(gross_commission, 0) * (tds_rate_percent / 100), 2)

    def monthly_bonus(self, total_monthly_disbursal: float) -> float:
        """Simple monthly bonus placeholder.

        Example rule:
        - >= 2Cr disbursal: 50,000 bonus
        - >= 1Cr disbursal: 20,000 bonus
        - else: 0
        """
        if total_monthly_disbursal >= 2_00_00_000:
            return 50_000.0
        if total_monthly_disbursal >= 1_00_00_000:
            return 20_000.0
        return 0.0

    # ======================================
    # SECTION: Helper Functions
    # ======================================
    def _slab_rate(self, disbursal_amount: float) -> float:
        """Return slab rate as decimal fraction."""
        amount = max(disbursal_amount, 0)
        if amount <= 50_00_000:
            return 0.005
        if amount <= 1_00_00_000:
            return 0.0065
        return 0.008


# ======================================
# SECTION: Calculators
# ======================================
# N/A for this service. Formula logic is encapsulated in the class
# methods above for easier onboarding and reuse.
