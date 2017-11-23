from processor import Processor
from mesi import MESICache
from dragon import DragonCache
from bus import Bus
import time

LOAD = 0
STORE = 1
OTHER = 2
TOTAL = 3

class Simulator:
    def __init__(self, protocol, input_file, cache_size, associativity, block_size):
        if protocol == 'MESI':
            self.caches = [MESICache(cache_size, associativity, block_size, i) for i in range(4)]
        elif protocol == 'DRAGON':
            self.caches = [DragonCache(cache_size, associativity, block_size, i) for i in range(4)]

        self.processors = [Processor(input_file, i, self.caches[i]) for i in range(4)]
        self.bus = Bus(self.caches)
        for cache in self.caches:
            cache.set_shared_bus(self.bus)
        self.count = 0

        
    def run(self):
        done = [False for i in range(4)]

        start = time.time()
        while not all(done):
            bus_blocked = self.bus.tick()
            # if bus_blocked:
            #     print("Bus blocked for {} cycles").format(self.bus.blocked_cycle) 
            for p in self.processors:
                if done[p.pid]:
                    if p.cycles[TOTAL] == -1:
                        p.cycles[TOTAL] = self.count-1
                    continue

                cache = p.cache
                processor_blocked = p.tick()
                cache_blocked = cache.tick()

                # processor performing calculation
                if processor_blocked:
                    continue

                # cache retrieving data from main memory
                if cache_blocked:
                    continue

                res = p.execute_instr()
                if res is None:
                    done[p.pid] = True
                    continue

                label, value = res

                if label == OTHER:
                    p.block_for(value)
                    p.cycles[OTHER] += value
                    continue

                if label == LOAD:
                    action = 'r'

                elif label == STORE:
                    action = 'w'

                # print("bus is blocked: {}").format(bus_blocked)
                # check if bus is blocked and current instruction generate bus transaction 
                if not bus_blocked or not cache.bus_txn_generated(action, value):
                    deferred_action = cache.cache_update(action, value)
                    if deferred_action:
                        p.stall_instr()
                    elif action == 'w':
                        p.cycles[STORE] += 1
                    elif action == 'r':
                        p.cycles[LOAD] += 1
                else:
                    p.stall_instr()

            self.count += 1
            
        for i in range(4):
            if self.processors[i].cycles[TOTAL] == -1:
                self.processors[i].cycles[TOTAL] = self.count-1

        end = time.time()
        print("Time taken: {}").format(end - start)
        print("")

    def print_results(self):
        
        print("Overall Execution Cycle: {}").format(self.count)
        print("")

        for i in range (4):
            print("Core {} results:").format(i)

            print("Total cycles: {}").format(self.processors[i].cycles[TOTAL])
            print("Compute cycles: {}").format(self.processors[i].cycles[OTHER])
            print("Load instructions: {}").format(self.processors[i].cycles[LOAD])
            print("Store instructions: {}").format(self.processors[i].cycles[STORE])

            print("Idle cycles: {}").format(self.caches[i].idle_cycles)
            
            total_ldr_str = self.processors[i].cycles[LOAD] + self.processors[i].cycles[STORE]
            if total_ldr_str > 0:
                data_miss_rate =  100.0  * self.caches[i].data_miss / total_ldr_str
            else:
                data_miss_rate = 0.0
            print("Data miss rate: {}%").format(data_miss_rate)

            print("Total private data accesses: {} ").format(self.bus.caches[i].data_access[0])
            print("Total public data accesses: {} ").format(self.bus.caches[i].data_access[1])
            print("")

        print("Bus traffic:")
        print("Total number of Bus transactions: {}").format(self.bus.data_traffic)
        print("Total number of invalidations: {}").format(self.bus.invalidations)
        print("Total number of updates (cache-to-cache) : {}").format(self.bus.updates)


# sim = Simulator('MESI', 'bodytrack', 4096, 2, 32)
# sim.run()
# sim.print_results()

                
sim = Simulator('DRAGON', 'bodytrack', 4096, 2, 32)
sim.run()
sim.print_results()
