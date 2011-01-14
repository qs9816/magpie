package com.stuffwithstuff.magpie.ast.pattern;

import java.util.List;

import com.stuffwithstuff.magpie.ast.Expr;
import com.stuffwithstuff.magpie.ast.pattern.Pattern;
import com.stuffwithstuff.magpie.util.Pair;

public class WildcardPattern implements Pattern {
  public WildcardPattern() {
  }
  
  public Expr createPredicate(Expr value) {
    return Expr.bool(true);
  }
  
  public void createBindings(List<Pair<String, Expr>> bindings, Expr root) {
    // Do nothing.
  }

  @Override
  public <R, C> R accept(PatternVisitor<R, C> visitor, C context) {
    return visitor.visit(this, context);
  }

  @Override
  public String toString() {
    return "_";
  }
}