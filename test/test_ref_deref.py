import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from astnode import (
    Ident_Node, Int_Node, Address_Node, Deref_Node,
    Assign_Node, Type_Node, Pointer_Type_Node
)
from semantic import Analyzer, SemanticError, PointerType
from symbol import TypeKind

def test_valid_address_of():
    analyzer = Analyzer()
    # var int x = 10
    analyzer.visit(Assign_Node(ident="x", type=Type_Node(name="int"), value=Int_Node(value=10)))
    
    # &x
    addr_node = Address_Node(target=Ident_Node(ident="x"))
    inferred = analyzer.visit(addr_node)
    
    assert inferred == PointerType(base_type=TypeKind.INT)
    assert str(inferred) == "*TypeKind.INT"

def test_invalid_address_of_literal():
    analyzer = Analyzer()
    # &10 (Invalid: 10 is an rvalue literal)
    addr_node = Address_Node(target=Int_Node(value=10))
    
    with pytest.raises(SemanticError, match="Cannot take address of a non-lvalue expression"):
        analyzer.visit(addr_node)

def test_valid_deref():
    analyzer = Analyzer()
    # var int x = 10
    analyzer.visit(Assign_Node(ident="x", type=Type_Node(name="int"), value=Int_Node(value=10)))
    # var *int p = &x
    analyzer.visit(Assign_Node(
        ident="p",
        type=Pointer_Type_Node(base_type=Type_Node(name="int")),
        value=Address_Node(target=Ident_Node(ident="x"))
    ))
    
    # *p
    deref_node = Deref_Node(target=Ident_Node(ident="p"))
    inferred = analyzer.visit(deref_node)
    
    assert inferred == TypeKind.INT

def test_invalid_deref_non_pointer():
    analyzer = Analyzer()
    # var int x = 10
    analyzer.visit(Assign_Node(ident="x", type=Type_Node(name="int"), value=Int_Node(value=10)))
    
    # *x (Invalid: x is int, not pointer)
    deref_node = Deref_Node(target=Ident_Node(ident="x"))
    
    with pytest.raises(SemanticError, match="Cannot dereference non-pointer type"):
        analyzer.visit(deref_node)
