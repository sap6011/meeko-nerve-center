class SolarPunkVault:
    def __init__(self, energy_output_kwh):
        self.shares_total = 1000  # Initial "Stock"
        self.energy_backing = energy_output_kwh # Real-world backing

    def mint_shares(self, contribution_usd, current_rate=1.0):
        # 70% to restoration, 30% to hardware as per Bylaws
        hw_portion = contribution_usd * 0.30
        new_shares = hw_portion / current_rate
        print(f"?? MINTING: {new_shares} $SPK shares created for Collective.")
        return new_shares
