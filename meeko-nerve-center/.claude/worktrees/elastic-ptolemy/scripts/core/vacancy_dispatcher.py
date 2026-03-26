class VacancyDispatcher:
    def check_for_unfilled_gaps(self):
        # Scan gaps that have been open for > 24 hours
        unfilled = self.get_open_gaps()
        for gap in unfilled:
            if gap.type == "Digital":
                self.broadcast_to_A2A_network(gap)
            elif gap.type == "Physical":
                self.post_to_RentAHuman(gap)
            print(f"?? DISPATCHED: Gap {gap.id} routed to the Collective Network.")
