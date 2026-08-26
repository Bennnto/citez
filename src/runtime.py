from dataclasses import dataclass
from symbol import TypeKind

@dataclass
class RuntimeValue:
    type_kind: TypeKind
    value: object
    
@dataclass 
class StringObject:
    value : str
    
class Heap:
    def __init__(self):
        self.objects : list[object] = []
    
    def allocate(self, obj):
        self.objects.append(obj)
        return obj
    
    def allocate_string(self, value:str):
        obj = StringObject(value)
        self.objects.append(obj)
        return obj
    
class Environment:
    def __init__(self, parent=None, heap=None):
        self.parent = parent
        self.heap = heap if heap else (parent.heap if parent else Heap())
        self.values: dict[str, RuntimeValue] = {}
    
    def define(self, name:str, value:RuntimeValue):
        self.values[name] = value
        
    def get(self, name:str):
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Error :Undefined variable {name!r}")
    
    def set(self, name:str , value: RuntimeValue):
        if name in self.values :
            self.values[name] = value
            return
        if self.parent:
            self.parent.set(name, value)
            return
        raise NameError(f"Error :Undefined variable {name!r}")