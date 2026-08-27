from dataclasses import dataclass, field
from enum import Enum, auto


class Storage(Enum):
    GLOBAL = auto()
    STACK = auto()
    CAPTURED = auto()
    
class TypeKind(Enum):
    STR = auto()
    INT = auto()
    BOOL = auto()
    FLOAT = auto()
    CHAR = auto()
    I8 = auto()
    I16 = auto()
    I32 = auto()
    I64 = auto()
    ISIZE = auto()
    U8 = auto()
    U16 = auto()
    U32 = auto()
    U64 = auto()
    USIZE = auto()
    F32 = auto()
    F64 = auto()
    VOID = auto()
    
TYPE_NAME_MAP = {
    'str': TypeKind.STR,
    'int': TypeKind.INT,
    'bool': TypeKind.BOOL,
    'float': TypeKind.FLOAT,
    'char': TypeKind.CHAR,
    'i8': TypeKind.I8,
    'i16': TypeKind.I16,
    'i32': TypeKind.I32,
    'i64': TypeKind.I64,
    'isize': TypeKind.ISIZE,
    'u8': TypeKind.U8,
    'u16': TypeKind.U16,
    'u32': TypeKind.U32,
    'u64': TypeKind.U64,
    'usize': TypeKind.USIZE,
    'f32': TypeKind.F32,
    'f64': TypeKind.F64,
    'void': TypeKind.VOID,
}
    

class SymbolState(Enum):
    ACTIVE = auto()
    BORROWED_RO = auto()
    BORROWED_RW = auto()
    DROPPED = auto()


@dataclass
class Symbol:
    name : str
    type_kind : TypeKind = TypeKind.STR
    storage: Storage = Storage.STACK
    
    state: SymbolState = SymbolState.ACTIVE
    ro_borrow_count: int = 0
    rw_claimed: bool = False

    scope_depth: int = 0
    stack_offset: int | None = None
    captured_index: int | None = None
    
    declared_in: "Scope | None" = None
    captured: bool = False
    
@dataclass
class Scope:
    parent: "Scope | None" = None
    kind: str = "block"
    depth: int = 0
    symbols: dict[str, Symbol] = field(default_factory=dict)

    def __post_init__(self):
        if self.parent:
            self.depth = self.parent.depth + 1
        
    def declare(self, name: str, type_kind: TypeKind = TypeKind.STR) -> Symbol:
        if name in self.symbols:
            raise NameError(f"Error :{name!r} already declared")
    
        storage = Storage.GLOBAL if self.kind == "global" else Storage.STACK
        
        symbol = Symbol(
            name = name,
            type_kind= type_kind,
            storage = storage,
            scope_depth = self.depth,
            declared_in = self
        )
        self.symbols[name] = symbol
        return symbol
    
    def resolve(self, name: str):
        scope = self
        distance = 0
        while scope:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
            distance += 1
        raise NameError(f"Error :Undefined name {name!r}")
    
    