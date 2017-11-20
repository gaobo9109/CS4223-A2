from file_reader import read_instruction

class Processor:
    def __init__(self, input_file, processor_id, cache):
        self.cache = cache
        self.instr = read_instruction(input_file, processor_id)
        self.instr_count = len(self.instructions)
        self.instr_index = 0
        self.finished = False
        self.pid = processor_id
        self.blocked_cycle = 0
        self.total_cycle = 0


    def tick(self):
        if self.blocked_cycle > 0:
            self.blocked_cycle -= 1
            self.total_cycle += 1
            return

        elif self.instr_index >= self.instr_count:
            print("processor {} is done".format(self.pid))
            self.finished = True
            return

        label, value = self.instr[self.instr_index]
        self.instr_index += 1
        self.total_cycle += 1
        return label, value

    def block_for(self, num_cycles):
        self.blocked_cycle += num_cycles

