class OmniConsentEngine:
    def __init__(self):
        self.consent_state = "ALWAYS_GO"
        self.safety_filters = ["Legal", "Ethical", "50%_Aid_Rule"]

    def process_gap(self, gap_data):
        if all(filter in gap_data for filter in self.safety_filters):
            print(f"? AUTO-GO: Executing manifest for {gap_data['target']}")
            return True
        else:
            print("?? HOLD: Safety filter mismatch. Human Anchor intervention required.")
            return False
