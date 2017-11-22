from cache import Cache

INVALID = 'invalid'
SHARED = 'shared'
MODIFIED = 'modified'
EXCLUSIVE = 'exclusive'
BUS_RD = 'BUS_RD'
BUS_RDX = 'BUS_RDX'
PR_RD = 'PR_RD'
PR_RDS = 'PR_RDS'
PR_WR = 'PR_WR'

STATE_MACHINE = {
    INVALID: {
        PR_RD: (EXCLUSIVE, BUS_RD, 100),
        PR_RDS: (SHARED, BUS_RD, 100),
        PR_WR: (MODIFIED, BUS_RDX, 100),
        BUS_RD: (INVALID, False, 0),
        BUS_RDX: (INVALID, False, 0)
    },
    SHARED: {
        PR_RD: (SHARED, None, 0),
        PR_WR: (MODIFIED, BUS_RDX, 0),
        BUS_RD: (SHARED, False, 0),
        BUS_RDX: (INVALID, False, 0)
    },
    MODIFIED: {
        PR_RD: (MODIFIED, None, 0),
        PR_WR: (MODIFIED, None, 0),
        BUS_RD: (SHARED, True, 100),
        BUS_RDX: (INVALID, True, 100)
    },
    EXCLUSIVE: {
        PR_RD: (EXCLUSIVE, None, 0),
        PR_WR: (MODIFIED, None, 0),
        BUS_RD: (SHARED, True, 0),
        BUS_RDX: (INVALID, True, 0)
    }
}

class MESICache(Cache):
    def __init__(self, cache_size, associativity, block_size, processor_id):
        Cache.__init__(self, cache_size, associativity, block_size, processor_id)
        self.state_machine = STATE_MACHINE
        self.initial_state = INVALID
        self.has_deferred_action = False
        self.deferred_action = ()

    def bus_txn_generated(self, action, addr):
        tag, set_index = self.split_addr(addr)
        cache_state = self.cache_states[set_index]
        state = self.initial_state
        if tag in cache_state:
            state = cache_state[tag]
        return state == INVALID or (state == SHARED and action == 'w')

    def cache_update(self, action, addr):
        tag, set_index = self.split_addr(addr)
        block_index = self.get_block_index(tag, set_index)
        cache_state = self.cache_states[set_index]
        cache_set = self.cache_sets[set_index]
        state = self.initial_state

        if tag in cache_state:
            state = cache_state[tag]
        else:
            cache_state[tag] = state

        if action == 'r':
            if state == INVALID and self.bus.is_shared(block_index):
                next_state, bus_txn, blocked_cycles = self.state_machine[state][PR_RDS]
            else:
                next_state, bus_txn, blocked_cycles = self.state_machine[state][PR_RD]

        elif action == 'w':
            next_state, bus_txn, blocked_cycles = self.state_machine[state][PR_WR]

        evicted_tag = cache_set.memory_action(tag)
       
        # when there is a cache miss, wait until data is retrieved before performing cache state update
        if blocked_cycles > 0:
            write_back_cycle = 100 if (evicted_tag != -1 and cache_state[evicted_tag] == MODIFIED) else 0 
            self.has_deferred_action = True
            self.deferred_action = (tag, set_index, next_state, bus_txn, evicted_tag, write_back_cycle) 
        else:
            # if cache hit, no need to evict a block
            assert evicted_tag == -1
            cache_state[tag] = next_state
            
            if bus_txn is not None:
                self.bus.broadcast_txn(self.pid, bus_txn, tag, set_index)
        
        self.block_for(blocked_cycles)

    def deferred_cache_update(self):
        tag, set_index, next_state, bus_txn, evicted_tag, write_back_cycle = self.deferred_action
        block_index = self.get_block_index(tag, set_index)
        self.has_deferred_action = False
        self.deferred_action = ()
        self.cache_states[set_index][tag] = next_state
        self.bus.add_shared(block_index, self.pid)

        if evicted_tag != -1:
            # remove block from cache state
            self.cache_states[set_index].pop(evicted_tag)

            # remove evicted block from bus shared_line
            evicted_block_index = self.get_block_index(evicted_tag, set_index)
            self.bus.remove_shared(evicted_block_index, self.pid)

        if bus_txn is not None:
            self.bus.broadcast_txn(self.pid, bus_txn, tag, set_index)
        self.block_for(write_back_cycle)

    def bus_update(self, txn_type, tag, set_index):
        cache_state = self.cache_states[set_index]
        block_index = self.get_block_index(tag, set_index)
        if tag in cache_state:
            curr_state = cache_state[tag]
            next_state, block_bus, write_back_cycle = self.state_machine[curr_state][txn_type]
            cache_state[tag] = next_state
            self.block_for(write_back_cycle)

            # if a block is invalidated, need to remove it from bus shared_line
            if next_state == INVALID:
                self.bus.remove_shared(block_index, self.pid)

            block_bus_cycle = 0
            if block_bus:
                block_bus_cycle = self.cache_transfer_cycle
            return block_bus_cycle

        return 0
                











