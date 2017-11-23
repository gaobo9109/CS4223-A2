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
        self.cache_transfer_cycle = self.block_size // 4 * 2

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
        generate_bus_txn = True
        bus_txn = None

        if tag in cache_state:
            state = cache_state[tag]
        else:
            cache_state[tag] = state
        # print("Processor {}'s current state is {}").format(self.pid, state)

        # state transition 

        if action == 'r' and state == INVALID:
            shared = self.bus.is_shared(block_index)
            
            if shared:
                next_state, bus_txn, blocked_cycles = self.state_machine[state][PR_RDS]

            else:
                next_state, bus_txn, blocked_cycles = self.state_machine[state][PR_RD]

        elif action == 'r' and state != INVALID:
            next_state, bus_txn, blocked_cycles = self.state_machine[state][PR_RD]

        elif action == 'w':
            next_state, bus_txn, blocked_cycles = self.state_machine[state][PR_WR]
      
        if self.has_deferred_action:
            self.has_deferred_action = False

            # state update
            cache_state[tag] = next_state
            self.bus.add_shared(block_index, self.pid)

            evicted_tag = cache_set.memory_action(tag)
            if evicted_tag != -1:
                if cache_state[evicted_tag] == MODIFIED:
                    self.block_for(100)
                self.cache_states[set_index].pop(evicted_tag)
                evicted_block_index = self.get_block_index(evicted_tag, set_index)
                self.bus.remove_shared(evicted_block_index, self.pid)
       
        else:

            # if there is only one other cache holding the same data,
            # transfer the data from that cache instead of main memory
            unique = self.bus.is_unique(block_index)
            if unique and state == INVALID:
                self.bus.updates += 1
                # print("unique found!")
                # override previous operation
                # previous operation assumes no cache has the data
                # if currently one other cache has the data, 
                # should get the updated copy from that cache
                # data transfer takes cache_transfer_cycle
                self.has_deferred_action = True
                self.bus.block_for(self.cache_transfer_cycle)
                self.idle_cycles += self.cache_transfer_cycle
                generate_bus_txn = False
                self.data_miss += 1

            else:
                # just a normal cache miss
                if blocked_cycles > 0:
                    self.has_deferred_action = True
                    self.block_for(blocked_cycles) 
                    # bus transaction doesn't happen till deferred action is taken
                    generate_bus_txn = False
                    self.data_miss += 1

                # cache hit
                else:   
                    # no eviction of block for cache hit
                    cache_set.memory_action(tag)
                    cache_state[tag] = next_state

        if generate_bus_txn and bus_txn is not None:
            self.bus.data_traffic += 1
            self.bus.broadcast_txn(self.pid, bus_txn, tag, set_index)
                   
        return self.has_deferred_action

    def bus_update(self, txn_type, tag, set_index):
        cache_set = self.cache_sets[set_index]
        cache_state = self.cache_states[set_index]
        block_index = self.get_block_index(tag, set_index)       
        if tag in cache_state:
            curr_state = cache_state[tag]
            # print("Dinosaur {}'s current state is {}").format(self.pid, curr_state)

            if curr_state != INVALID:
                next_state, block_bus, write_back_cycle = self.state_machine[curr_state][txn_type]
                cache_state[tag] = next_state
                self.block_for(write_back_cycle)

                if next_state != SHARED:
                    evicted_tag = cache_set.invalidate(tag)
                    self.bus.invalidations += 1
                    if evicted_tag != -1:
                        if cache_state[evicted_tag] == MODIFIED:
                            self.block_for(100)
                        self.cache_states[set_index].pop(evicted_tag)
                        evicted_block_index = self.get_block_index(evicted_tag, set_index)
                        self.bus.remove_shared(evicted_block_index, self.pid)
                    # print("invalidated and evicted from cache {}").format(self.pid)
                return curr_state

        return INVALID    

        
                











