class Bus:
    def __init__(self, caches):
        self.shared_data = {}
        self.is_unique_data = {}
        self.caches = caches
        self.blocked_cycle = 0
        self.updates = 0
        self.invalidations = 0
        self.data_traffic = 0

    def is_shared(self, key):
        return key in self.shared_data

    # unique copy of this data
    def is_unique(self, key):
        if key in self.is_unique_data:
            return self.is_unique_data[key]
        else:
            return False

    def is_modified(self, tag, set_index, pid):
        for cache in self.caches:
            if cache.pid == pid:
                continue
            if tag in cache.cache_states[set_index] and cache.cache_states[set_index][tag] == 'modified':
                return True
        return False

    def add_shared(self, key, pid):
        if key in self.shared_data:
            self.shared_data[key].add(pid)
            if len(self.shared_data[key]) > 1:
                self.is_unique_data[key] = False
        else:
            self.shared_data[key] = set()
            self.shared_data[key].add(pid)
            self.is_unique_data[key] = True

    def remove_shared(self, key, pid):
        if key in self.shared_data:
            if pid in self.shared_data[key]:
                self.shared_data[key].remove(pid)
            if len(self.shared_data[key]) == 1:
                self.is_unique_data[key] = True
            elif len(self.shared_data[key]) == 0:
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
        is_private = False
        is_shared = False

        for cache in self.caches:
            if cache.pid == source:
                continue

            data_access = cache.bus_update(txn_type, tag, set_index)
            if data_access == 'modified' or data_access == 'exclusive':
                is_private = True
            elif data_access == 'shared' or data_access == 'shared_clean' or data_access == 'shared_modified':
                is_shared = True

        if is_private: 
            self.caches[source].data_access[0] += 1
        if is_shared: 
            self.caches[source].data_access[1] += 1
