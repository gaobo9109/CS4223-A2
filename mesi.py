from cache import Cache

INVALID = 'invalid'
SHARED = 'shared'
MODIFIED = 'modified'
EXCLUSIVE = 'exclusive'
BUS_RD = 'BUS_RD'
BUSR_DX = 'BUS_RDX'
PR_RD = 'PR_RD'
PR_RDS = 'PR_RDS'
PR_WR = 'PR_WR'

STATE_MACHINE = {
    INVALID: {
        PR_RD: (EXCLUSIVE, BUS_RD, 100),
        PR_RDS: (SHARED, BUS_RD, 100),
        PR_WR: (MODIFIED, BUS_RDX, 100),
        BUS_RD: (INVALID, False, 0),
        BUS_RDX: (INVALID, False, 0),
    },
    SHARED: {
        PR_RD: (SHARED, None, 1),
        PR_WR: (MODIFIED, BUS_RDX, 1),
        BUS_RD: (SHARED, False, 0),
        BUS_RDX: (INVALID, False, 0),
    },
    MODIFIED: {
        PR_RD: (MODIFIED, None, 0),
        PR_WR: (MODIFIED, None, 0),
        BUS_RD: (SHARED, True, 100),
        BUS_RDX: (INVALID, True, 100),
    },
    EXCLUSIVE: {
        PR_RD: (EXCLUSIVE, None, 0),
        PR_WR: (MODIFIED, None, 0),
        BUS_RD: (SHARED, True, 100),
        BUS_RDX: (INVALID, True, 100),
    }
}

class MESICache(Cache):
    def __init__(self, cache_size, associativity, block_size, processor_id):
        CacheController.__init__(cache_size, associativity, block_size, processor_id)
        self.state_machine = STATE_MACHINE
        self.initial_state = INVALID

    def processor_action(self, action, addr):
        tag, set_index = self.split_addr(addr)
        cache_state = self.cache_states[set_index]
        cache_set = self.cache_sets[set_index]
        state = self.initial_state
        if cache_state.has_key(tag):
            state = cache_state[tag]
        else:
            cache_state[tag] = state

        cycles = 0
        bus_txn = None
        if action == 'r':
            if self.shared_line.is_shared(addr):
                next_state, bus_txn, cycles = self.state_machine[state][PR_RDS]
            else:
                next_state, bus_txn, cycles = self.state_machine[state][PR_RD]
            cache_state[tag] = next_state

        elif action == 'w':
            next_state, bus_txn, cycles = self.state_machine[state][PR_WR]
            cache_state[tag] = next_state

        evicted_tag = cache_set.mem_action(tag)
        self.shared_line.add_shared(addr, self.pid)

        # flush the value
        if evicted_tag != -1:
            if cache_state[evicted_tag] == MODIFIED:
                cycles += 100
            self.shared_line.remove_shared(self.get_addr(evicted_tag, set_index), self.pid)
            cache_state.pop(tag)

        return bus_txn, cycles

    def bus_action(self, bus_txn):

