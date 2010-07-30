package com.stuffwithstuff.magpie.interpreter;

import java.util.*;

/**
 * A lexical scope for named variables. Maintains a stack of nested scopes to
 * support proper block scoping.
 */
public class Scope {
  public Scope() {
    mParent = null;
  }
  
  public void put(String name, Obj value) {
    mVariables.put(name, value);
  }
  
  public Obj get(String name) {
    // Walk up the scope chain.
    Scope scope = this;
    while (scope != null) {
      Obj value = scope.mVariables.get(name);
      if (value != null) return value;
      scope = scope.mParent;
    }
    
    // If we got here, it wasn't defined.
    return null;
  }
  
  public Scope push() {
    return new Scope(this);
  }
  
  public Scope pop() {
    return mParent;
  }
  
  private Scope(Scope parent) {
    mParent = parent;
  }

  private final Scope mParent;
  private final Map<String, Obj> mVariables = new HashMap<String, Obj>();
}