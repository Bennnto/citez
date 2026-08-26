from dataclasses import dataclass
from symbol import Scope, Storage


@dataclass
class FrameLayout:
    scope: Scope
    word_size: int = 8
    stack_size: int = 0
    env_size: int = 0
    
    def allocate(self):
        next_stack = 0
        next_env = 0
        for symbol in self.scope.symbols.values():
            if symbol.storage == Storage.STACK:
                next_stack += self.word_size
                symbol.stack_offset = -next_stack
            
            elif symbol.storage == Storage.CAPTURED:
                symbol.captured_index = next_env
                next_env += 1
        
        self.stack_size = next_stack
        self.env_size = next_env
        return self