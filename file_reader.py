import os

PREFIX = 'data'
EXT = '.data'


def read_instruction(input_file, processor_id):
    filename = ''.join([input_file, '_', str(processor_id), EXT])
    filepath = os.path.join(PREFIX, input_file, filename)

    instructions = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            instruction = [int(num, 0) for num in line.split()]
            instructions.append(instruction)

    print("Done reading file {}".format(processor_id))
    return instructions