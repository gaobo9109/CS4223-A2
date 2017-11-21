from processor import Processor
from mesi import MESICache
from dragon import DragonCache
from bus import Bus

LOAD = 0
STORE = 1
OTHER = 2

class Simulator:
    def __init__(self, protocol, input_file, cache_size, associativity, block_size):
        if protocol == 'MESI':
            self.caches = [MESICache(cache_size, associativity, block_size, i) for i in range(4)]
        elif protocol == 'DRAGON':
            self.caches = [DragonCache(cache_size, associativity, block_size, i) for i in range(4)]

        self.processors = [Processor(input_file, i, self.caches[i]) for i in range(4)]
        self.bus = Bus(self.cachces)
        for cache in self.caches:
            cache.set_shared_bus(self.bus)

        
    def run():
        done = [False for i in range(4)]

        while not all(done):
            bus_blocked = self.bus.tick()
            for p in self.processors:
                if done[p.pid]: 
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

                # cache done retrieving data, updating cache state
                if cache.has_deferred_action:
                    cache.deferred_cache_update()
                    continue

               res = p.execute_instr()
                if res is None:
                    done[p.pid] = True
                    continue

                label, value = res

                if label == OTHER:
                    p.block_for(value)
                    continue

                if label == LOAD:
                    action = 'r'

                elif label == STORE:
                    action = 'w'

                # check if bus is blocked and current instruction generate bus transaction 
                if not bus_blocked or not cache.bus_tnx_generated(action, value):
                    cache.cache_update(action, value)
                else:
                    p.stall_instr()







                

