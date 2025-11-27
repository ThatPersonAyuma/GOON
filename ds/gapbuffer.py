class GapBuffer:
    def __init__(self, initial_size=128):
        self.buffer = [''] * initial_size
        self.gap_start = 0
        self.gap_end = initial_size
        self.cursor_position = 0
    
    def insert(self, char):
        if self.gap_start == self.gap_end:
            self._expand_gap()
        
        self.buffer[self.gap_start] = char
        self.gap_start += 1
        self.cursor_position += 1
    
    def delete(self):
        if self.gap_start > 0:
            self.gap_start -= 1
            self.buffer[self.gap_start] = ''
            self.cursor_position -= 1
            return True
        return False
    
    def delete_forward(self):
        if self.gap_end < len(self.buffer):
            self.buffer[self.gap_end] = ''
            self.gap_end += 1
            return True
        return False
    
    def move_cursor(self, position):
        text_length = self.get_text_length()
        position = max(0, min(position, text_length))
        
        if position < self.gap_start:
            while position < self.gap_start:
                self.gap_start -= 1
                self.gap_end -= 1
                self.buffer[self.gap_end] = self.buffer[self.gap_start]
                self.buffer[self.gap_start] = ''
        
        elif position > self.gap_start:
            while position > self.gap_start:
                self.buffer[self.gap_start] = self.buffer[self.gap_end]
                self.buffer[self.gap_end] = ''
                self.gap_start += 1
                self.gap_end += 1
        
        self.cursor_position = position
    
    def get_text(self):
        return ''.join(self.buffer[:self.gap_start] + 
                      self.buffer[self.gap_end:])
    
    def get_text_length(self):
        return len(self.buffer) - (self.gap_end - self.gap_start)
    
    def set_text(self, text):
        needed_size = len(text) + 128
        self.buffer = [''] * needed_size
        self.gap_start = 0
        self.gap_end = needed_size
        
        for char in text:
            self.insert(char)
        
        self.move_cursor(0)
    
    def clear(self):
        initial_size = 128
        self.buffer = [''] * initial_size
        self.gap_start = 0
        self.gap_end = initial_size
        self.cursor_position = 0
    
    def _expand_gap(self):
        old_size = len(self.buffer)
        new_size = old_size * 2
        
        new_buffer = [''] * new_size
        
        for i in range(self.gap_start):
            new_buffer[i] = self.buffer[i]
        
        new_gap_end = new_size - (old_size - self.gap_end)
        
        j = new_gap_end
        for i in range(self.gap_end, old_size):
            new_buffer[j] = self.buffer[i]
            j += 1
        
        self.buffer = new_buffer
        self.gap_end = new_gap_end
    
    def get_gap_info(self):
        return {
            'buffer_size': len(self.buffer),
            'gap_start': self.gap_start,
            'gap_end': self.gap_end,
            'gap_size': self.gap_end - self.gap_start,
            'text_length': self.get_text_length(),
            'cursor_position': self.cursor_position
        }
    
    def __str__(self):
        info = self.get_gap_info()
        text = self.get_text()
        return f"GapBuffer(text='{text[:50]}...', cursor={info['cursor_position']}, gap_size={info['gap_size']})"
