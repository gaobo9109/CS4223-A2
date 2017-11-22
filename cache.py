class CacheSet:
    def __init__(self, associativity, set_id):
        self.set_size = associativity
        self.members = []
        self.set_id = set_id

    def bring_to_front(self, index):
        block = self.members.pop(index)
        self.members.insert(index, block)

    def bring_to_back(self, index):
        block = self.members.pop(index)
        self.members.append(block)

    def memory_action(self, tag):
        evicted_tag = -1
        if tag in self.members:
            idx = self.members.index(tag)
            self.bring_to_front(idx)
        else:
            if len(self.members) == self.set_size:
                evicted_tag = self.members.pop()

            self.members.insert(0, tag)
        return evicted_tag

    def invalidate(self, tag):
        if tag in self.members:
            idx = self.members.index(tag)
            self.bring_to_back(idx)


class Cache:
    def __init__(self, cache_size, associativity, block_size, processor_id):
        self.num_set = cache_size // block_size // associativity
        self.block_size = block_size
        self.set_size = associativity
        self.cache_transfer_cycle = self.block_size // 4 * 2
        self.pid = processor_id
        self.cache_states = [{} for i in range(self.num_set)]
        self.cache_sets = [CacheSet(associativity, i) for i in range(self.num_set)]
        self.blocked_cycle = 0

    def tick(self):
        if self.blocked_cycle == 0 or self.blocked_cycle == 1:
            self.blocked_cycle = 0
            return False
        else:
            self.blocked_cycle -= 1
            return True

    def block_for(self, num_cycle):
        self.blocked_cycle = num_cycle

    def split_addr(self, addr):
        block_index = addr // self.block_size
        tag = block_index // self.num_set
        set_index = block_index % self.num_set
        return tag, set_index

    def get_block_index(self, tag, set_index):
        return (tag * self.num_set + set_index) * self.block_size

    def set_shared_bus(self, bus):
        self.bus = bus

    # override these functions

    def cache_update(self, action, addr):
        pass

    def deferred_cache_update(self):
        pass

    def bus_update(self, txn_type, tag, set_index):
        pass

    def bus_txn_generated(self, action, addr):
        pass





    