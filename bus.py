class Bus:
    def __init__(self, caches):
        self.shared_data = {}
        self.caches = caches
        self.blocked_cycle = 0

    def is_shared(self, key):
        return self.shared_data.has_key(key)

    def add_shared(self, key, pid):
        if self.shared_data.has_key(key):
            self.shared_data[key].add(pid)
        else:
            self.shared_data[key] = set()
            self.shared_data[key].add(pid)

    def remove_shared(self, key, pid):
        if self.shared_data.has_key(key):
            if pid in self.shared_data[key]:
                self.shared_data[key].remove(pid)
            if len(self.shared_data[key]) == 0:
                self.shared_data.pop(key)

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



