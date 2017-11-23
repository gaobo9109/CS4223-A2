from cache import Cache

INVALID = "invalid"
SHARED_CLEAN = "shared_clean"
SHARED_MODIFIED = "shared_modified"
EXCLUSIVE = "exclusive"
MODIFIED = 'modified'
BUS_UPDATE = "bus_update"
BUS_RD = "bus_read"
PR_RD = 'PR_RD'
PR_RDS = 'PR_RDS'
PR_WR = 'PR_WR'
PR_WRS = 'PR_WRS'

STATE_MACHINE = {
    INVALID: {
        PR_RDS: (SHARED_CLEAN, BUS_RD, 0),
        PR_RD: (EXCLUSIVE, BUS_RD, 100),
        PR_WR: (MODIFIED, BUS_RD, 100),
        PR_WRS: (SHARED_MODIFIED, BUS_UPDATE, 0),
    },
    SHARED_CLEAN: {
        PR_RD: (SHARED_CLEAN, None, 0),
        PR_WR: (MODIFIED, None, 0),
        PR_WRS: (SHARED_MODIFIED, BUS_UPDATE, 0),
        BUS_RD: (SHARED_CLEAN, False, 0),
        BUS_UPDATE: (SHARED_CLEAN, True, 0)
    },
    SHARED_MODIFIED: {
        PR_RD: (SHARED_MODIFIED, None, 0),
        PR_WR: (MODIFIED, None, 0),
        PR_WRS: (SHARED_MODIFIED, BUS_UPDATE, 0),
        BUS_RD: (SHARED_MODIFIED, False, 0),
        BUS_UPDATE: (SHARED_CLEAN, True, 0)
    },
    MODIFIED: {
        PR_RD: (MODIFIED, None, 0),
        PR_WR: (MODIFIED, None, 0),
        # PR_WRS: (MODIFIED, None, 0),
        BUS_RD: (SHARED_MODIFIED, True, 0)
    },
    EXCLUSIVE: {
        PR_RD: (EXCLUSIVE, None, 0),
        PR_WR: (MODIFIED, None, 0),
        # PR_WRS: (MODIFIED, None, 0),
        BUS_RD: (SHARED_CLEAN, True, 0)
    }
}


class DragonCache(Cache):
    def __init__(self, cache_size, associativity, block_size, processor_id):
        Cache.__init__(self, cache_size, associativity, block_size, processor_id)
        self.state_machine = STATE_MACHINE
        self.has_deferred_action = False
        self.cache_transfer_cycle = 2
        self.deferred_block_index = -1
        self.cache_to_cache_transfer = False

    def bus_txn_generated(self, action, addr):
        tag, set_index = self.split_addr(addr)
        cache_state = self.cache_states[set_index]
        state = INVALID
        if tag in cache_state:
            state = cache_state[tag]
        return state == INVALID or ((state == SHARED_CLEAN or state == SHARED_MODIFIED) and action == 'w')

    def cache_update(self, action, addr):
        tag, set_index = self.split_addr(addr)
        block_index = self.get_block_index(tag, set_index)
        cache_state = self.cache_states[set_index]
        cache_set = self.cache_sets[set_index]
        generate_bus_txn = True
        bus_txn = None

        if tag in cache_state:
            state = cache_state[tag]
            cache_hit = True
        else:
            cache_hit = False
            state = INVALID

        # state transition 
        shared = self.bus.is_shared(block_index)
        next_state = None
        if cache_hit:
            if state == SHARED_CLEAN:
                if action == 'w' and shared:
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_WRS]
                elif action == 'w':
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_WR]
                else:
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_RD]

            elif state == SHARED_MODIFIED:
                if action == 'w' and shared:
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_WRS]
                elif action == 'w':
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_WR]
                else:
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_RD]


            elif state == MODIFIED:
                if action == 'w':
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_WR]
                else:
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_RD]

            elif state == EXCLUSIVE:
                if action == 'w':
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_WR]
                else:
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_RD]


        else:
            if shared:
                if action == 'r':
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_RDS]
                else:
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_WRS]
            else:
                if action == 'r':
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_RD]
                else:
                    next_state, bus_txn, blocked_cycle = self.state_machine[state][PR_WR]

        # print(next_state)


        if self.has_deferred_action:
            self.has_deferred_action = False

            # state update
            cache_state[tag] = next_state
            self.bus.add_shared(block_index, self.pid)

            # kick out least recently used block
            evicted_tag = cache_set.memory_action(tag)
            if evicted_tag != -1:
                if cache_state[evicted_tag] == MODIFIED:
                    self.block_for(100)
                self.cache_states[set_index].pop(evicted_tag)
                evicted_block_index = self.get_block_index(evicted_tag, set_index)
                self.bus.remove_shared(evicted_block_index, self.pid)

            # if differed_action is a cache -> cache transfer, bus transaction already completed
            # if not, it is a normal cache miss, transaction not broadcasted yet
            generate_bus_txn = not self.cache_to_cache_transfer
            self.cache_to_cache_transfer = False

        else:
            if not cache_hit:
                self.has_deferred_action = True
                self.data_miss += 1
                
                if shared: # get data from other cache
                    self.block_for(self.cache_transfer_cycle)
                    self.cache_to_cache_transfer = True
                
                else: # get data from main memory
                    # note down which memory block is retrieived
                    # in case another cache can transfer the data before retrieval is complete
                    self.deferred_block_index = block_index
                    self.block_for(blocked_cycle)

            else:
                cache_set.memory_action(tag)
                cache_state[tag] = next_state
            
        if generate_bus_txn and bus_txn is not None:
            self.bus.data_traffic += 1
            self.bus.broadcast_txn(self.pid, bus_txn, tag, set_index)
            if bus_txn == BUS_UPDATE or (bus_txn == BUS_RD and shared and state == INVALID):
                self.bus.updates += 1

        return self.has_deferred_action


    def bus_update(self, txn_type, tag, set_index):
        cache_set = self.cache_sets[set_index]
        cache_state = self.cache_states[set_index]
        block_index = self.get_block_index(tag, set_index)        
        if tag in cache_state:
            curr_state = cache_state[tag]
            

            if txn_type == BUS_UPDATE and (curr_state == MODIFIED or curr_state == EXCLUSIVE):
                return curr_state

            next_state, _, _ = self.state_machine[curr_state][txn_type]
            cache_state[tag] = next_state


            # if source cache updating other cache, both source and dest need to bo blocked
            # if source cache requesting data , only source cache blocked
            if txn_type == BUS_UPDATE:
                self.block_for(self.cache_transfer_cycle)
                self.bus.block_for(self.cache_transfer_cycle)

            elif txn_type == BUS_RD:
                # snoop bus read when in the process of retrieving data from main memory
                # override the previous action
                # block bus and itself, transfer data from another cache 
                if self.has_deferred_action and self.deferred_block_index == block_index:
                    self.has_deferred_action = False
                    self.deferred_block_index = -1
                    self.block_for(self.cache_transfer_cycle)
                
                self.bus.block_for(self.cache_transfer_cycle)
            
            self.idle_cycles += self.cache_transfer_cycle

            return curr_state

        return INVALID



