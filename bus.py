class Bus:
    def __init__(self, caches):
        self.shared_data = {}
        self.is_unique_data = {}
        self.caches = caches
        self.blocked_cycle = 0

    def is_shared(self, key):
        return key in self.shared_data

    # unique copy of this data
    def is_unique(self, key):
        if key in self.is_unique_data:
            return self.is_unique_data[key]
        else:
            return False

    def add_shared(self, key, pid):
        if key in self.shared_data:
            self.shared_data[key].add(pid)
            self.is_unique_data[key] = False
        else:
            self.shared_data[key] = set()
            self.shared_data[key].add(pid)
            self.is_unique_data[key] = True

    def remove_shared(self, key, pid):
        if key in self.shared_data:
            if pid in self.shared_data[key]:
                self.shared_data[key].remove(pid)
            if len(self.shared_data[key]) == 0:
                self.shared_data.pop(key)
                self.is_unique_data.pop(key)

    def block_for(self, num_cycle):
        self.blocked_cycle = num_cycle

    def tick(self):
        if self.blocked_cycle == 0 or self.blocked_cycle == 1:
            self.blocked_cycle = 0
            return False
        else:
            self.blocked_cycle -= 1
            return True

    def broadcast_txn(self, source, txn_type, tag, set_index):
        for cache in self.caches:
            if cache.pid == source:
                continue

            blocked_cycle = cache.bus_update(txn_type, tag, set_index)
            self.block_for(blocked_cycle)



