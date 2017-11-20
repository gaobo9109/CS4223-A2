class SharedLine:
    def __init__(self):
        self.shared_data = {}

    def is_shared(self, key):
        return self.shared_data.has_key(key)

    def add_shared(self, key, pid):
        if self.shared_data.has_key(key):
            self.shared_data[key].add(pid)
        else:
            self.shared_data[key] = set()
            self.shared_data[key].add(pid)

    def remove_shared(self, key, pid):
        if self.shared_data.has_key(key):
            if pid in self.shared_data[key]:
                self.shared_data[key].remove(pid)
            if len(self.shared_data[key]) == 0:
                self.shared_data.pop(key)



