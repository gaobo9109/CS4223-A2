from file_reader import read_instruction

class Processor:
    def __init__(self, input_file, processor_id, cache):
        self.cache = cache
        self.instr = read_instruction(input_file, processor_id)
        self.instr_count = len(self.instr)
        self.instr_index = 0
        self.finished = False
        self.pid = processor_id
        self.blocked_cycle = 0
        self.cycles = [0, 0, 0, -1]

    def tick(self):
        if self.blocked_cycle == 0 or self.blocked_cycle == 1:
            self.blocked_cycle = 0
            return False
        else:
            self.blocked_cycle -= 1
            return True

    def execute_instr(self):
        if self.instr_index >= self.instr_count:
            print("Processor {} is done".format(self.pid))
            self.finished = True
            return None

        label, value = self.instr[self.instr_index]
        # print("processor {} is at instruction {}".format(self.pid, self.instr_index))
        self.instr_index += 1

        return label, value

    def stall_instr(self):
        if self.instr_index > 0:
            self.instr_index -= 1

    def block_for(self, num_cycles):
        self.blocked_cycle += num_cycles

